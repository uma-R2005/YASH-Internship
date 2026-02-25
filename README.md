# 📄 PDF Q&A Analyzer

<div align="center">

**Upload any PDF. Ask any question. Get 8 AI-powered answers — ranked by quality.**

*A side-by-side comparison engine for 4 prompting techniques × 4 chunking strategies.*

[Features](#features) · [Installation](#installation) · [Usage](#usage) · [How It Works](#how-it-works)

</div>

---

## What Is This?

PDF Q&A Analyzer is a **RAG (Retrieval-Augmented Generation) comparison tool** built with Gradio and Google Gemini. It answers your question 8 different ways — using 4 different prompting strategies and 4 different chunking strategies — then scores and ranks every answer automatically.

It makes the impact of RAG design decisions **visible and tangible**, rather than theoretical.

---

## Features

- 📤 **PDF Upload** — drag-and-drop ingestion via PyMuPDF
- 🤖 **Auto Question Generation** — Gemini suggests 6 relevant questions from your document
- ✏️ **Custom Questions** — type your own question at any time
- ⚡ **4 Prompting Techniques** — Zero-Shot, Chain-of-Thought, Role-Based, Few-Shot
- ✂️ **4 Chunking Strategies** — Fixed Size, Sentence, Paragraph, Semantic
- 📊 **Automated Answer Ranking** — 4-signal quality scorer ranks all 8 answers side-by-side
- 🎨 **Polished Dark UI** — professional dark-mode interface with animated score bars

---

## Installation

### Prerequisites

- Python 3.10+
- A free API key from [Google AI Studio](https://aistudio.google.com)

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/pdf-qa-analyzer.git
cd pdf-qa-analyzer

# 2. Create and activate a virtual environment
python -m venv venv
source venv/bin/activate        # macOS / Linux
venv\Scripts\activate           # Windows

# 3. Install dependencies
pip install gradio pymupdf google-generativeai
```

---

## Configuration

Set your Google Gemini API key as an environment variable. **Never hardcode secrets in source files.**

```bash
# macOS / Linux
export GOOGLE_API_KEY="your-api-key-here"

# Windows (PowerShell)
$env:GOOGLE_API_KEY="your-api-key-here"
```

Get your free API key at [aistudio.google.com/apikey](https://aistudio.google.com/apikey).

---

## Usage

```bash
python app.py
```

Open `http://127.0.0.1:7860` in your browser, then:

1. **Upload** a PDF (report, paper, contract, manual — anything with embedded text)
2. **Generate Questions** — click to get 6 AI-suggested questions, or type your own
3. **Analyze** — click "Analyze with 8 Techniques" and wait ~30–60 seconds
4. **Compare** — Section A shows prompting results, Section B shows chunking results
5. **Check Rankings** — Section C ranks all 8 answers by the quality scorer

---

## How It Works

The tool runs a **controlled experiment** on every query:

| | Prompting Techniques | Chunking Techniques |
|---|---|---|
| **What changes** | The instruction given to the AI | The document content shown to the AI |
| **What stays fixed** | The document context | The instruction (Zero-Shot) |
| **Purpose** | Measure impact of *how you ask* | Measure impact of *what context you retrieve* |

### The 4 Prompting Techniques

| Technique | Approach | Best For |
|---|---|---|
| ⚡ **Zero-Shot** | Direct question with no examples or scaffolding | Simple factual lookups |
| 🔗 **Chain-of-Thought** | Forces explicit step-by-step reasoning before the final answer | Complex, inferential questions |
| 🎭 **Role-Based** | Assigns the model a senior expert persona | Professional tone, technical documents |
| 🎯 **Few-Shot** | Provides 2 example Q&A pairs to define the expected answer format | Consistent, structured output |

### The 4 Chunking Strategies

| Strategy | Method | Best For |
|---|---|---|
| 📏 **Fixed Size** | 500-character windows with 100-character overlap | Dense, uniformly structured documents |
| 📝 **Sentence** | Groups of 5 sentences with a 1-sentence overlap between groups | Narrative text, articles, papers |
| 📄 **Paragraph** | Splits on blank lines; oversized paragraphs are sub-chunked | Well-formatted PDFs |
| 🧠 **Semantic** | Topic-shift detection using stop-word-filtered keyword overlap | Multi-topic reports and documents |

### Answer Scoring (out of 10)

All 8 answers are scored on 4 independent signals — **not** by length or keyword frequency:

| Signal | Points | What It Measures |
|---|---|---|
| **Relevance** | 3 | Meaningful-word overlap between answer and question |
| **Grounding** | 3 | How much of the answer's vocabulary comes from the source document *(hallucination proxy)* |
| **Specificity** | 2 | Presence of numbers, named entities, and quoted phrases |
| **Conciseness** | 2 | Sweet spot of 80–400 words; very short or rambling answers are penalised |

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | [Gradio](https://gradio.app) |
| PDF Parsing | [PyMuPDF (fitz)](https://pymupdf.readthedocs.io) |
| Language Model | [Google Gemini](https://ai.google.dev) |
| SDK | `google-generativeai` |
| Language | Python 3.10+ |

---

## Requirements

```
gradio
pymupdf
google-generativeai
```

---

## Limitations

- **Scanned PDFs** — PyMuPDF cannot extract text from image-only (scanned) PDFs; use text-embedded PDFs
- **Large documents** — prompting techniques use only the first 3,500 characters; chunking techniques process the full document
- **Scoring is a proxy** — the quality scorer measures linguistic signals correlated with quality, not factual correctness
- **English only** — stop word filtering is optimised for English text

---

## Roadmap

- [ ] Sentence-embedding based semantic chunking (`sentence-transformers`)
- [ ] Vector search chunk retrieval (FAISS / cosine similarity)
- [ ] OCR support for scanned PDFs
- [ ] Multi-document comparison mode
- [ ] LLM-as-judge scoring for factual accuracy verification
- [ ] Export results as CSV or PDF report

---
