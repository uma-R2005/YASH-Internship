import gradio as gr
import fitz  # PyMuPDF
import re
import time
import os
from openai import OpenAI

# ─────────────────────────────────────────────
# ⚠️  Set your OpenRouter API Key via environment variable:
#     export OPENROUTER_API_KEY="sk-or-v1-..."
# Or paste it directly below (NOT recommended for shared code)
# ─────────────────────────────────────────────
API_KEY = os.environ.get("OPENROUTER_API_KEY", "")   # ← use env var, never hardcode

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=API_KEY
)

# Valid free model on OpenRouter (as of 2024)
MODEL = "meta-llama/llama-3.1-8b-instruct:free"

# ─────────────────────────────────────────────
# STOP WORDS  (filtered out before any scoring)
# ─────────────────────────────────────────────

STOP_WORDS = {
    "a","an","the","and","or","but","in","on","at","to","for","of","with",
    "is","are","was","were","be","been","being","have","has","had","do","does",
    "did","will","would","could","should","may","might","shall","can","need",
    "it","its","this","that","these","those","he","she","they","we","i","you",
    "my","your","his","her","their","our","what","which","who","how","when",
    "where","why","from","by","as","if","so","not","no","nor","than","then",
    "there","here","just","also","about","into","over","after","before","more",
}

def meaningful_words(text: str) -> set:
    """Lowercase tokens with stop words and short tokens removed."""
    return {w for w in re.findall(r'\b[a-z]{3,}\b', text.lower()) if w not in STOP_WORDS}

# ─────────────────────────────────────────────
# 4 CHUNKING TECHNIQUES  (fixed)
# ─────────────────────────────────────────────

MAX_CHUNK_CHARS = 800   # upper bound for any single chunk

def chunk_fixed_size(text: str, chunk_size: int = 500, overlap: int = 100) -> list[str]:
    """
    Split into equal-length character windows.
    overlap=100 (was 50) gives enough context to avoid losing boundary sentences.
    """
    chunks, start = [], 0
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        start += chunk_size - overlap          # advance by (chunk_size - overlap)
    return chunks


def chunk_sentence(text: str, group_size: int = 5) -> list[str]:
    """
    Split at sentence boundaries, then group into windows of `group_size`
    sentences WITH a 1-sentence overlap so no boundary sentence is isolated.
    Sentences are also length-balanced: if a group exceeds MAX_CHUNK_CHARS
    it is split further.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    chunks = []
    i = 0
    while i < len(sentences):
        group = sentences[i: i + group_size]
        combined = " ".join(group)
        # If combined is too long, split it by fixed size
        if len(combined) > MAX_CHUNK_CHARS:
            chunks.extend(chunk_fixed_size(combined, chunk_size=MAX_CHUNK_CHARS, overlap=80))
        else:
            if combined:
                chunks.append(combined)
        i += group_size - 1          # 1-sentence overlap between groups
    return chunks if chunks else [text]


def chunk_paragraph(text: str) -> list[str]:
    """
    Split on blank lines (author's natural structure).
    FIX: paragraphs that exceed MAX_CHUNK_CHARS are sub-chunked with
    fixed-size so no single massive paragraph dominates.
    """
    raw = re.split(r'\n\s*\n', text.strip())
    chunks = []
    for para in raw:
        para = para.strip()
        if not para:
            continue
        if len(para) > MAX_CHUNK_CHARS:
            # Sub-chunk oversized paragraphs
            chunks.extend(chunk_fixed_size(para, chunk_size=MAX_CHUNK_CHARS, overlap=80))
        else:
            chunks.append(para)
    return chunks if chunks else [text]


def chunk_semantic(text: str, min_chunk_sentences: int = 3, overlap_keyword_threshold: int = 2,
                   keyword_window: int = 3) -> list[str]:
    """
    Detect topic shifts using MEANINGFUL word overlap (stop words excluded).

    BUG FIX — sliding keyword window:
      Previously `topic_keywords` accumulated ALL words from every sentence in
      the current chunk, so after a few sentences the set covered every topic
      ever mentioned and a genuine topic shift could never be detected (the
      overlap was always ≥ threshold).  Now we compare the incoming sentence
      against only the keywords from the last `keyword_window` sentences,
      giving a true local-context comparison.

    FIX 1: Stop words are filtered before comparing keyword sets.
    FIX 2: A minimum of `min_chunk_sentences` sentences is enforced before
            a boundary can be triggered — prevents over-splitting on short text.
    FIX 3: Keyword window (default 3) keeps the topic signal local and fresh.
    """
    sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', text.strip()) if s.strip()]
    chunks = []
    current_chunk: list[str] = []
    # Rolling buffer: store meaningful words for the last `keyword_window` sentences
    recent_words: list[set] = []

    for sentence in sentences:
        words = meaningful_words(sentence)

        # Build the local topic context from the recent window
        window_keywords: set = set().union(*recent_words) if recent_words else set()
        overlap = len(words & window_keywords)

        should_split = (
            len(current_chunk) >= min_chunk_sentences and   # min sentences met
            window_keywords and                              # have established a topic
            bool(words) and                                  # skip split if sentence has no meaningful words (all stop words)
            overlap < overlap_keyword_threshold              # genuine topic shift
        )

        if should_split:
            combined = " ".join(current_chunk)
            if len(combined) > MAX_CHUNK_CHARS:
                chunks.extend(chunk_fixed_size(combined, chunk_size=MAX_CHUNK_CHARS, overlap=80))
            else:
                chunks.append(combined)
            current_chunk = [sentence]
            recent_words = [words]          # reset window to the new opening sentence
        else:
            current_chunk.append(sentence)
            recent_words.append(words)
            if len(recent_words) > keyword_window:
                recent_words.pop(0)         # slide the window forward

    if current_chunk:
        combined = " ".join(current_chunk)
        if len(combined) > MAX_CHUNK_CHARS:
            chunks.extend(chunk_fixed_size(combined, chunk_size=MAX_CHUNK_CHARS, overlap=80))
        else:
            chunks.append(combined)

    return chunks if chunks else [text]


# ─────────────────────────────────────────────
# CHUNK SELECTION  (fixed)
# ─────────────────────────────────────────────

def get_best_chunks(chunks: list[str], question: str, max_chars: int = 3000) -> str:
    """
    Score each chunk by meaningful-word overlap with the question.

    FIX 1: Stop words excluded from both question and chunk before scoring.
    FIX 2: Score normalised by chunk length so a tiny chunk with 2 hits
            doesn't beat a large relevant chunk with 5 hits.
    FIX 3: Fallback now picks the longest chunk (more likely to have useful
            content) rather than blindly returning chunks[0].
    """
    q_words = meaningful_words(question)

    if not q_words:
        # No meaningful question words — return the longest chunks up to budget
        sorted_by_len = sorted(chunks, key=len, reverse=True)
        selected = ""
        for chunk in sorted_by_len:
            if len(selected) + len(chunk) + 2 <= max_chars:
                selected += chunk + "\n\n"
        return selected.strip() or max(chunks, key=len)

    scored = []
    for chunk in chunks:
        chunk_words = meaningful_words(chunk)
        raw_overlap = len(chunk_words & q_words)
        # Normalise: overlap per 100 meaningful words in chunk (avoid length bias)
        # BUG FIX: old formula  raw_overlap / (chunk_size / 100)  gave LARGER
        # chunks a LOWER score (dividing by bigger denominator) — the opposite
        # of what we want. Correct normalisation: fraction of question keywords
        # covered by this chunk, scaled 0–100.
        norm_score = (raw_overlap / max(len(q_words), 1)) * 100
        scored.append((norm_score, raw_overlap, chunk))

    # Sort by normalised score desc, then raw overlap desc
    scored.sort(key=lambda x: (x[0], x[1]), reverse=True)

    selected = ""
    for _, _, chunk in scored:
        if len(selected) + len(chunk) + 2 <= max_chars:
            selected += chunk + "\n\n"

    # Fallback: longest chunk (most likely relevant)
    return selected.strip() or max(chunks, key=len)


# ─────────────────────────────────────────────
# 4 PROMPTING TECHNIQUES
# ─────────────────────────────────────────────

def prompt_zero_shot(context: str, question: str) -> str:
    return f"""You are a precise document assistant. Answer ONLY using information from the document below.
If the answer is not in the document, say "Not found in document."

Document:
{context}

Question: {question}

Answer:"""


def prompt_chain_of_thought(context: str, question: str) -> str:
    return f"""You are an analytical assistant. Use the document below to answer the question.
Work through these steps explicitly before giving your final answer:

Document:
{context}

Question: {question}

Step 1 — Restate what the question is specifically asking:
Step 2 — Identify the relevant passages or data points in the document:
Step 3 — Reason through what those passages imply:
Step 4 — Final Answer (concise, document-grounded):"""


def prompt_role_based(context: str, question: str) -> str:
    return f"""You are a senior analyst with deep expertise in document review and information extraction.
Your task is to read the document carefully and provide a professional, evidence-based answer.
Cite specific parts of the document where possible. If the answer is absent, state that clearly.

Document:
{context}

Question: {question}

Professional Analysis:"""


def prompt_few_shot(context: str, question: str) -> str:
    return f"""You are a precise Q&A assistant. Study the two examples below, then answer the real question in the same format.

--- EXAMPLE 1 ---
Q: What is the main topic of the document?
A: The document focuses on [specific topic], covering [key aspects] as evidenced by [specific section/phrase].

--- EXAMPLE 2 ---
Q: What conclusion does the document reach?
A: The document concludes that [specific finding], supported by [specific evidence from the text].

--- REAL TASK ---
Document:
{context}

Q: {question}
A:"""


# ─────────────────────────────────────────────
# ANSWER QUALITY SCORING  (fixed)
# ─────────────────────────────────────────────

def score_answer(answer: str, question: str, context: str) -> float:
    """
    Multi-signal quality score (out of 10).

    Replaces the old length+period+keyword hack with signals that
    actually correlate with answer quality:

    1. Relevance  (3 pts): meaningful-word overlap between answer and question
    2. Grounding  (3 pts): meaningful-word overlap between answer and source context
    3. Specificity(2 pts): presence of numbers, proper nouns, quotes — signs of
                           concrete evidence rather than vague waffle
    4. Conciseness(2 pts): penalise extremely short OR extremely long answers;
                           sweet spot is 80–400 words
    """
    if not answer or answer.startswith(("⚠️", "❌")):
        return 0.0

    a_words = meaningful_words(answer)
    q_words = meaningful_words(question)
    c_words = meaningful_words(context)

    # 1. Relevance: how much of the question's vocabulary appears in the answer
    relevance = 0.0
    if q_words:
        relevance = min(len(a_words & q_words) / len(q_words), 1.0) * 3

    # 2. Grounding: answer uses vocabulary from the source document
    grounding = 0.0
    if c_words:
        grounding = min(len(a_words & c_words) / max(len(a_words), 1), 1.0) * 3

    # 3. Specificity: numbers, capitalised words (named entities), quoted phrases
    numbers      = len(re.findall(r'\b\d+[\d,\.%]*\b', answer))
    # FIX 3: exclude sentence-starting capitals (after . ! ?) — they are NOT proper nouns,
    # just normal capitalisation. Only count capitalised words that appear mid-sentence.
    mid_sentence = re.sub(r'(?<=[.!?])\s+[A-Z]', lambda m: m.group().lower(), answer)
    proper_nouns = len(re.findall(r'\b[A-Z][a-z]{2,}\b', mid_sentence))
    quotes       = len(re.findall(r'"[^"]{5,}"', answer))
    specificity  = min((numbers * 0.4 + proper_nouns * 0.2 + quotes * 0.5), 2.0)

    # 4. Conciseness: word count sweet spot 80–400
    word_count = len(answer.split())
    if word_count < 20:
        conciseness = 0.0
    elif word_count < 80:
        conciseness = 0.5
    elif word_count <= 400:
        conciseness = 2.0
    elif word_count <= 600:
        conciseness = 1.0
    else:
        conciseness = 0.5   # penalise very long rambling answers

    total = round(relevance + grounding + specificity + conciseness, 1)
    return min(total, 10.0)


# ─────────────────────────────────────────────
# CORE FUNCTIONS
# ─────────────────────────────────────────────

def extract_text(pdf_file) -> str:
    if pdf_file is None:
        return ""
    with fitz.open(pdf_file.name) as doc:   # FIX 1: context manager ensures file handle is always closed
        return "\n".join(page.get_text() for page in doc)


def call_llm(prompt: str, retries: int = 3, base_delay: int = 3) -> str:
    """
    FIX: base_delay reduced to 3s; backoff is 2x not 4x (3s → 6s → 12s).
    This keeps the UI responsive while still respecting rate limits.
    """
    for attempt in range(retries):
        try:
            response = client.chat.completions.create(
                model=MODEL,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1024,
                temperature=0.2      # low temperature = more factual, less hallucination
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            err = str(e)
            if attempt < retries - 1:
                wait = base_delay * (2 ** attempt)   # 3s, 6s, 12s  (was 5s, 20s, 80s)
                print(f"[Attempt {attempt+1}] Error, retrying in {wait}s… ({err})")
                time.sleep(wait)
            else:
                return f"❌ Error after {retries} attempts: {err}"


def call_llm_sequential(prompts: list[str], inter_call_delay: float = 1.5) -> list[str]:
    results = []
    for i, prompt in enumerate(prompts):
        if i > 0:
            time.sleep(inter_call_delay)
        results.append(call_llm(prompt))
    return results


def generate_questions(pdf_file):
    if pdf_file is None:
        return gr.Dropdown(choices=[], label="📋 Select a question", interactive=True)
    try:
        text = extract_text(pdf_file)[:3000]   # FIX 2: moved inside try so corrupt PDFs are caught cleanly
        if not text.strip():
            return gr.Dropdown(choices=["Error: Could not extract text from PDF"], interactive=True)
        response = client.chat.completions.create(
            model=MODEL,
            messages=[{
                "role": "user",
                "content": (
                    "Generate exactly 6 specific, insightful questions that can be answered "
                    "from this document. Return ONLY a numbered list (1. ... 2. ...), one per line, "
                    "no preamble.\n\nDocument:\n" + text
                )
            }],
            max_tokens=400,
            temperature=0.3
        )
        raw = response.choices[0].message.content.strip()
        questions = [
            re.sub(r'^\d+[\.\)]\s*', '', line).strip()
            for line in raw.split("\n")
            if line.strip() and line.strip()[0].isdigit()
        ]
        return gr.Dropdown(
            choices=questions,
            label="📋 Select a question",
            interactive=True,
            value=questions[0] if questions else None
        )
    except Exception as e:
        return gr.Dropdown(choices=[f"Error: {e}"], interactive=True)


def analyze(pdf_file, dropdown_q, custom_q):
    question = custom_q.strip() if custom_q.strip() else (dropdown_q or "")
    if not question:
        return ["⚠️ Please select or type a question first."] * 8, ""
    if pdf_file is None:
        return ["⚠️ Please upload a PDF first."] * 8, ""

    full_text = extract_text(pdf_file)
    if not full_text.strip():
        return ["⚠️ Could not extract text from this PDF."] * 8, ""

    # For prompting techniques: use first 3500 chars (same content, different framing)
    plain = full_text[:3500]

    # For chunking techniques: chunk full document, then select best chunks per strategy
    chunks_fixed    = chunk_fixed_size(full_text)
    chunks_sentence = chunk_sentence(full_text)
    chunks_para     = chunk_paragraph(full_text)
    chunks_semantic = chunk_semantic(full_text)

    ctx_fixed    = get_best_chunks(chunks_fixed,    question)
    ctx_sentence = get_best_chunks(chunks_sentence, question)
    ctx_para     = get_best_chunks(chunks_para,     question)
    ctx_semantic = get_best_chunks(chunks_semantic, question)

    prompts = [
        # Prompting techniques (same context, different instructions)
        prompt_zero_shot(plain,        question),
        prompt_chain_of_thought(plain, question),
        prompt_role_based(plain,       question),
        prompt_few_shot(plain,         question),
        # Chunking techniques (same zero-shot instruction, different context)
        prompt_zero_shot(ctx_fixed,    question),
        prompt_zero_shot(ctx_sentence, question),
        prompt_zero_shot(ctx_para,     question),
        prompt_zero_shot(ctx_semantic, question),
    ]

    results = call_llm_sequential(prompts, inter_call_delay=1.5)
    return results, plain   # FIX 4: return plain text so analyze_and_compare doesn't read PDF again


def analyze_and_compare(pdf_file, dropdown_q, custom_q):
    question = custom_q.strip() if custom_q.strip() else (dropdown_q or "")
    results, context = analyze(pdf_file, dropdown_q, custom_q)   # FIX 4: reuse extracted text, no second PDF read

    table_html = build_comparison_table(results, question, context)
    return results + [table_html]


# ─────────────────────────────────────────────
# COMPARISON TABLE  (fixed scoring)
# ─────────────────────────────────────────────

def build_comparison_table(answers: list[str], question: str, context: str) -> str:
    labels = [
        ("⚡ Zero-Shot",        "Prompting"),
        ("🔗 Chain-of-Thought", "Prompting"),
        ("🎭 Role-Based",       "Prompting"),
        ("🎯 Few-Shot",         "Prompting"),
        ("📏 Fixed Size",       "Chunking"),
        ("📝 Sentence",         "Chunking"),
        ("📄 Paragraph",        "Chunking"),
        ("🧠 Semantic",         "Chunking"),
    ]

    scored = []
    for ans, (name, category) in zip(answers, labels):
        score = score_answer(ans, question, context)
        preview = (ans[:120] + "…") if len(ans) > 120 else ans
        scored.append((score, name, category, ans, preview))

    scored.sort(key=lambda x: x[0], reverse=True)

    rows = ""
    for rank, (score, name, category, ans, preview) in enumerate(scored, 1):
        medal = ["🥇", "🥈", "🥉"][rank - 1] if rank <= 3 else f"#{rank}"
        cat_color = "#2dd4bf" if category == "Prompting" else "#e8b84b"
        bar_pct = int((score / 10) * 100)
        is_best = "style='background:rgba(201,168,76,0.06); border-left:2px solid #c9a84c;'" if rank == 1 else ""
        score_str = f"{score}/10" if score > 0 else "N/A"
        rows += f"""
        <tr {is_best}>
          <td style='text-align:center; font-size:18px; padding:12px 10px;'>{medal}</td>
          <td style='padding:12px 10px; font-family:Playfair Display,serif; font-weight:700; color:#f0ede6; font-size:14px;'>{name}</td>
          <td style='padding:12px 10px; text-align:center;'>
            <span style='font-family:DM Mono,monospace; font-size:10px; padding:3px 8px; border-radius:100px;
                         border:1px solid {cat_color}33; color:{cat_color}; background:{cat_color}11;'>{category}</span>
          </td>
          <td style='padding:12px 10px;'>
            <div style='background:#16161f; border-radius:4px; height:8px; width:100%;'>
              <div style='background:linear-gradient(90deg,#c9a84c,#e8b84b); height:8px; border-radius:4px; width:{bar_pct}%;'></div>
            </div>
          </td>
          <td style='padding:12px 10px; text-align:center; font-family:DM Mono,monospace; font-size:13px; color:#c9a84c; font-weight:600;'>{score_str}</td>
          <td style='padding:12px 10px; font-size:12px; color:#8e8c86; max-width:280px;'>{preview}</td>
        </tr>"""

    html = f"""
    <div style='margin-top:8px;'>
      <table style='width:100%; border-collapse:collapse; font-size:13px;'>
        <thead>
          <tr style='border-bottom:1px solid #2a2a36;'>
            <th style='padding:10px; color:#52504c; font-family:DM Mono,monospace; font-size:10px; letter-spacing:0.15em; text-transform:uppercase;'>Rank</th>
            <th style='padding:10px; color:#52504c; font-family:DM Mono,monospace; font-size:10px; letter-spacing:0.15em; text-transform:uppercase; text-align:left;'>Technique</th>
            <th style='padding:10px; color:#52504c; font-family:DM Mono,monospace; font-size:10px; letter-spacing:0.15em; text-transform:uppercase;'>Type</th>
            <th style='padding:10px; color:#52504c; font-family:DM Mono,monospace; font-size:10px; letter-spacing:0.15em; text-transform:uppercase; text-align:left;'>Score Bar</th>
            <th style='padding:10px; color:#52504c; font-family:DM Mono,monospace; font-size:10px; letter-spacing:0.15em; text-transform:uppercase;'>Score</th>
            <th style='padding:10px; color:#52504c; font-family:DM Mono,monospace; font-size:10px; letter-spacing:0.15em; text-transform:uppercase; text-align:left;'>Preview</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style='font-family:DM Mono,monospace; font-size:10px; color:#52504c; margin-top:12px; text-align:right; letter-spacing:0.1em;'>
        SCORING: relevance (3pts) · grounding (3pts) · specificity (2pts) · conciseness (2pts)
      </p>
    </div>"""
    return html


# ─────────────────────────────────────────────
# CUSTOM CSS  (unchanged from original)
# ─────────────────────────────────────────────

custom_css = """
@import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700;900&family=DM+Mono:wght@300;400;500&family=DM+Sans:wght@300;400;500&display=swap');

:root {
    --bg-primary: #0a0a0f;
    --bg-card: #111118;
    --bg-elevated: #16161f;
    --accent-gold: #c9a84c;
    --accent-teal: #2dd4bf;
    --accent-rose: #fb7185;
    --accent-amber: #e8b84b;
    --text-primary: #f0ede6;
    --text-secondary: #8e8c86;
    --text-muted: #52504c;
    --border: #222228;
    --border-accent: #2a2a36;
    --glow-gold: rgba(201, 168, 76, 0.15);
    --radius: 12px;
    --radius-sm: 8px;
}

body, .gradio-container {
    background: var(--bg-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    color: var(--text-primary) !important;
}

.gradio-container {
    max-width: 1200px !important;
    margin: 0 auto !important;
    padding: 0 24px 60px !important;
}

.hero-wrap {
    text-align: center;
    padding: 56px 0 40px;
    position: relative;
}
.hero-wrap::before {
    content: '';
    position: absolute;
    top: 0; left: 50%;
    transform: translateX(-50%);
    width: 600px; height: 260px;
    background: radial-gradient(ellipse at center top, rgba(201,168,76,0.07) 0%, transparent 70%);
    pointer-events: none;
}
.hero-eyebrow {
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.3em;
    text-transform: uppercase;
    color: var(--accent-gold);
    display: block;
    margin-bottom: 14px;
}
.hero-title {
    font-family: 'Playfair Display', serif;
    font-size: clamp(34px, 5vw, 58px);
    font-weight: 900;
    line-height: 1.05;
    color: var(--text-primary);
    margin: 0 0 14px;
    letter-spacing: -0.02em;
}
.hero-title em { color: var(--accent-gold); font-style: italic; }
.hero-sub {
    font-size: 15px;
    color: var(--text-secondary);
    font-weight: 300;
    max-width: 460px;
    margin: 0 auto 24px;
    line-height: 1.7;
}
.hero-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    background: rgba(201,168,76,0.08);
    border: 1px solid rgba(201,168,76,0.2);
    border-radius: 100px;
    padding: 6px 16px;
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    color: var(--accent-gold);
    letter-spacing: 0.1em;
}
.hero-line {
    width: 60px; height: 1px;
    background: linear-gradient(90deg, transparent, var(--accent-gold), transparent);
    margin: 32px auto 0;
}

.step-card {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 22px 28px;
    margin-bottom: 16px;
    display: flex;
    align-items: center;
    gap: 14px;
}
.step-num {
    width: 30px; height: 30px;
    border-radius: 50%;
    background: linear-gradient(135deg, var(--accent-gold), #a07830);
    display: flex; align-items: center; justify-content: center;
    font-family: 'DM Mono', monospace;
    font-size: 13px; font-weight: 600;
    color: #0a0a0f;
    flex-shrink: 0;
}
.step-title {
    font-family: 'Playfair Display', serif;
    font-size: 18px; font-weight: 700;
    color: var(--text-primary);
}

.sec-head {
    display: flex;
    align-items: baseline;
    gap: 12px;
    margin: 36px 0 6px;
}
.sec-tag {
    font-family: 'DM Mono', monospace;
    font-size: 10px;
    letter-spacing: 0.25em;
    text-transform: uppercase;
    color: var(--accent-teal);
    background: rgba(45,212,191,0.08);
    border: 1px solid rgba(45,212,191,0.2);
    border-radius: 4px;
    padding: 3px 8px;
}
.sec-tag.b { color: var(--accent-amber); background: rgba(232,184,75,0.08); border-color: rgba(232,184,75,0.2); }
.sec-tag.c { color: var(--accent-rose); background: rgba(251,113,133,0.08); border-color: rgba(251,113,133,0.2); }
.sec-h2 {
    font-family: 'Playfair Display', serif;
    font-size: 22px; font-weight: 700;
    color: var(--text-primary);
    margin: 0;
}
.sec-desc {
    font-size: 13px;
    color: var(--text-secondary);
    margin: 4px 0 20px;
    line-height: 1.6;
}

.tgrid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
    margin-bottom: 20px;
}
.tcard {
    background: var(--bg-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 16px 18px;
    position: relative;
    overflow: hidden;
}
.tcard::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 2px;
}
.tcard.c1::before { background: linear-gradient(90deg, transparent, var(--accent-teal), transparent); }
.tcard.c2::before { background: linear-gradient(90deg, transparent, var(--accent-gold), transparent); }
.tcard.c3::before { background: linear-gradient(90deg, transparent, var(--accent-rose), transparent); }
.tcard.c4::before { background: linear-gradient(90deg, transparent, var(--accent-amber), transparent); }
.tcard-icon { font-size: 18px; margin-bottom: 4px; display: block; }
.tcard-name { font-family: 'Playfair Display', serif; font-size: 14px; font-weight: 700; color: var(--text-primary); }
.tcard-desc { font-size: 11px; color: var(--text-secondary); font-family: 'DM Mono', monospace; }

textarea, input[type="text"], .scroll-hide {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-accent) !important;
    border-radius: var(--radius-sm) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    line-height: 1.7 !important;
}
textarea:focus, input[type="text"]:focus {
    border-color: var(--accent-gold) !important;
    outline: none !important;
    box-shadow: 0 0 0 3px var(--glow-gold) !important;
}

button.primary, .gr-button-primary, button[variant="primary"] {
    background: linear-gradient(135deg, var(--accent-gold), #a07830) !important;
    border: none !important;
    color: #0a0a0f !important;
    font-family: 'DM Sans', sans-serif !important;
    font-weight: 600 !important;
    font-size: 14px !important;
    border-radius: var(--radius-sm) !important;
    box-shadow: 0 4px 20px rgba(201,168,76,0.25) !important;
    transition: all 0.2s !important;
}
button.secondary, .gr-button-secondary, button[variant="secondary"] {
    background: var(--bg-elevated) !important;
    border: 1px solid var(--border-accent) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.2s !important;
}

label, span.svelte-1gfkn6j {
    font-family: 'DM Mono', monospace !important;
    font-size: 11px !important;
    letter-spacing: 0.1em !important;
    text-transform: uppercase !important;
    color: var(--text-secondary) !important;
}

.gr-accordion {
    background: var(--bg-card) !important;
    border: 1px solid var(--border) !important;
    border-radius: var(--radius) !important;
    margin-top: 32px !important;
}

hr { border: none !important; border-top: 1px solid var(--border) !important; margin: 36px 0 !important; }

table { width: 100% !important; border-collapse: collapse !important; font-size: 13px !important; }
table th { background: var(--bg-elevated) !important; color: var(--text-secondary) !important;
           font-family: 'DM Mono', monospace !important; font-size: 11px !important;
           padding: 10px 14px !important; border-bottom: 1px solid var(--border) !important; }
table td { padding: 10px 14px !important; border-bottom: 1px solid var(--border) !important; color: var(--text-primary) !important; }
table tr:last-child td { border-bottom: none !important; }

::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: var(--bg-primary); }
::-webkit-scrollbar-thumb { background: var(--border-accent); border-radius: 3px; }
::-webkit-scrollbar-thumb:hover { background: var(--accent-gold); }

.or-divider {
    text-align: center;
    color: var(--text-muted);
    font-family: 'DM Mono', monospace;
    font-size: 11px;
    letter-spacing: 0.2em;
    margin: 10px 0;
}
"""

# ─────────────────────────────────────────────
# GRADIO UI
# ─────────────────────────────────────────────

with gr.Blocks(title="PDF Q&A Analyzer") as app:

    gr.HTML("""
    <div class="hero-wrap">
        <span class="hero-eyebrow">✦ AI-Powered Document Intelligence</span>
        <h1 class="hero-title">PDF <em>Q&amp;A</em> Analyzer</h1>
        <p class="hero-sub">Upload any document and receive 8 distinct answers —
        crafted using 4 prompting techniques and 4 chunking strategies.</p>
        <div class="hero-badge">⚡ Free · Powered by OpenRouter · Llama 3.1 8B</div>
        <div class="hero-line"></div>
    </div>
    """)

    gr.HTML("""
    <div class="step-card">
        <div class="step-num">1</div>
        <span class="step-title">Upload Your PDF</span>
    </div>
    """)
    with gr.Row():
        pdf_input = gr.File(label="Drop PDF here or click to browse", file_types=[".pdf"], scale=3)
        gen_btn   = gr.Button("⚙️ Generate Questions from PDF", variant="secondary", scale=1)

    gr.HTML("""
    <div class="step-card" style="margin-top:8px;">
        <div class="step-num">2</div>
        <span class="step-title">Choose Your Question</span>
    </div>
    """)
    dropdown_q = gr.Dropdown(choices=[], label="📋 Select an AI-generated question", interactive=True)
    gr.HTML('<div class="or-divider">── OR ──</div>')
    custom_q = gr.Textbox(label="✏️ Type your own question",
                          placeholder="e.g. What is the main conclusion of this document?")

    gr.HTML('<div style="margin-top:16px;"></div>')
    analyze_btn = gr.Button("🚀 Analyze with 8 Techniques", variant="primary", size="lg")

    gr.HTML('<hr/>')

    gr.HTML("""
    <div class="sec-head">
        <span class="sec-tag">Section A</span>
        <h2 class="sec-h2">4 Prompting Techniques</h2>
    </div>
    <p class="sec-desc">Same PDF content — four different ways of instructing the AI.</p>
    <div class="tgrid">
        <div class="tcard c1"><span class="tcard-icon">⚡</span><div class="tcard-name">Zero-Shot</div><div class="tcard-desc">Direct question, no examples</div></div>
        <div class="tcard c2"><span class="tcard-icon">🔗</span><div class="tcard-name">Chain-of-Thought</div><div class="tcard-desc">Step-by-step reasoning</div></div>
        <div class="tcard c3"><span class="tcard-icon">🎭</span><div class="tcard-name">Role-Based</div><div class="tcard-desc">Expert persona answers</div></div>
        <div class="tcard c4"><span class="tcard-icon">🎯</span><div class="tcard-name">Few-Shot</div><div class="tcard-desc">Answer guided by examples</div></div>
    </div>
    """)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### ⚡ Zero-Shot\n*Direct question, no examples*")
            out_zero = gr.Textbox(label="Answer", lines=10)
        with gr.Column():
            gr.Markdown("### 🔗 Chain-of-Thought\n*Step-by-step reasoning*")
            out_cot = gr.Textbox(label="Answer", lines=10)
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 🎭 Role-Based\n*Expert persona answers*")
            out_role = gr.Textbox(label="Answer", lines=10)
        with gr.Column():
            gr.Markdown("### 🎯 Few-Shot\n*Answer guided by examples*")
            out_few = gr.Textbox(label="Answer", lines=10)

    gr.HTML('<hr/>')

    gr.HTML("""
    <div class="sec-head">
        <span class="sec-tag b">Section B</span>
        <h2 class="sec-h2">4 Chunking Techniques</h2>
    </div>
    <p class="sec-desc">Same question — four different strategies for splitting the PDF content.</p>
    <div class="tgrid">
        <div class="tcard c2"><span class="tcard-icon">📏</span><div class="tcard-name">Fixed Size</div><div class="tcard-desc">Split every 500 characters with overlap</div></div>
        <div class="tcard c1"><span class="tcard-icon">📝</span><div class="tcard-name">Sentence</div><div class="tcard-desc">5 sentences with 1-sentence overlap</div></div>
        <div class="tcard c4"><span class="tcard-icon">📄</span><div class="tcard-name">Paragraph</div><div class="tcard-desc">Natural breaks, oversized chunks sub-split</div></div>
        <div class="tcard c3"><span class="tcard-icon">🧠</span><div class="tcard-name">Semantic</div><div class="tcard-desc">Stop-word-filtered topic shift detection</div></div>
    </div>
    """)

    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📏 Fixed Size\n*500 chars, 100-char overlap*")
            out_fixed = gr.Textbox(label="Answer", lines=10)
        with gr.Column():
            gr.Markdown("### 📝 Sentence\n*Groups of 5 with 1-sentence overlap*")
            out_sentence = gr.Textbox(label="Answer", lines=10)
    with gr.Row():
        with gr.Column():
            gr.Markdown("### 📄 Paragraph\n*Natural breaks, capped at 800 chars*")
            out_paragraph = gr.Textbox(label="Answer", lines=10)
        with gr.Column():
            gr.Markdown("### 🧠 Semantic\n*Meaningful keyword topic detection*")
            out_semantic = gr.Textbox(label="Answer", lines=10)

    gr.HTML('<hr/>')

    gr.HTML("""
    <div class="sec-head">
        <span class="sec-tag c">Section C</span>
        <h2 class="sec-h2">Answer Comparison &amp; Ranking</h2>
    </div>
    <p class="sec-desc">All 8 techniques ranked — scored on relevance, grounding, specificity &amp; conciseness.</p>
    """)

    comparison_table = gr.HTML(
        value="""<div style='background:#111118; border:1px solid #222228; border-radius:12px; padding:40px;
                      text-align:center; color:#52504c; font-family:DM Mono,monospace; font-size:12px; letter-spacing:0.15em;'>
            ── RUN ANALYSIS ABOVE TO SEE RANKINGS ──
        </div>"""
    )

    gr.HTML('<hr/>')

    with gr.Accordion("📚 Learn About These 8 Techniques", open=False):
        gr.HTML("""
        <div style="padding:8px 4px 16px;">
          <p style="color:#c8c5be; font-size:13px; line-height:1.7;">
            <strong style="color:#f0ede6;">Prompting techniques</strong> vary <em>how</em> the AI is instructed
            while keeping the document content identical.<br>
            <strong style="color:#f0ede6;">Chunking techniques</strong> vary <em>what</em> content the AI sees
            (the most question-relevant slices of the document) while keeping the instruction identical.
          </p>
          <hr style="border-color:#222228; margin:16px 0;"/>
          <p style="color:#8e8c86; font-family:DM Mono,monospace; font-size:11px; letter-spacing:0.1em;">
            SCORING SIGNALS: relevance to question (3pts) · vocabulary grounded in document (3pts) ·
            specificity — numbers, entities, quotes (2pts) · conciseness — 80–400 word sweet spot (2pts)
          </p>
        </div>
        """)

    gr.HTML("""
    <div style="text-align:center; padding:40px 0 16px; border-top:1px solid #222228; margin-top:40px;">
        <p style="font-family:'DM Mono',monospace; font-size:11px; letter-spacing:0.15em; color:#52504c; text-transform:uppercase;">
            Built with Gradio · PyMuPDF · OpenRouter &nbsp;✦&nbsp; 100% Free
        </p>
    </div>
    """)

    # ── EVENTS ──
    gen_btn.click(fn=generate_questions, inputs=[pdf_input], outputs=[dropdown_q])

    analyze_btn.click(
        fn=analyze_and_compare,
        inputs=[pdf_input, dropdown_q, custom_q],
        outputs=[out_zero, out_cot, out_role, out_few,
                 out_fixed, out_sentence, out_paragraph, out_semantic,
                 comparison_table]
    )

app.launch(css=custom_css)
