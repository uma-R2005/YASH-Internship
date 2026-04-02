import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MODEL = "llama-3.1-8b-instant"   # free tier model — 6000 requests/day


async def ask(prompt: str, system: str = None) -> str:
    """
    Send a single prompt to Groq and return the text response.
    Used by all 4 benchmark files.
    """
    messages = []

    if system:
        messages.append({"role": "system", "content": system})

    messages.append({"role": "user", "content": prompt})

    response = client.chat.completions.create(
        model=MODEL,
        messages=messages,
        temperature=0,        # 0 = deterministic, best for eval
        max_tokens=256,       # answers are short (A/B/C/D or True/False)
    )

    return response.choices[0].message.content.strip()


async def ask_mcq(question: str, options: list[str]) -> str:
    """
    Ask a multiple choice question.
    Returns only the letter: A, B, C, or D.
    Used by MMLU benchmark.
    """
    options_text = "\n".join([f"{chr(65+i)}. {opt}" for i, opt in enumerate(options)])

    prompt = f"""Question: {question}

{options_text}

Reply with ONLY the letter of the correct answer (A, B, C, or D). Nothing else."""

    system = "You are a medical knowledge expert. Answer MCQ questions with only the letter A, B, C, or D."

    answer = await ask(prompt, system)

    # Extract just the letter in case model adds extra text
    for char in answer.upper():
        if char in ["A", "B", "C", "D"]:
            return char

    return "A"   # fallback


async def ask_truefalse(statement: str) -> str:
    """
    Ask if a medical statement is true or false.
    Returns 'True' or 'False'.
    Used by TruthfulQA benchmark.
    """
    prompt = f"""Is the following medical statement TRUE or FALSE?

Statement: {statement}

Reply with ONLY the word True or False. Nothing else."""

    system = "You are a medical fact-checker. Reply only with True or False."

    answer = await ask(prompt, system)

    if "true" in answer.lower():
        return "True"
    return "False"


async def ask_fairness(prompt_a: str, prompt_b: str) -> dict:
    """
    Ask the same clinical question about two different patient demographics.
    Returns both answers for HELM bias comparison.
    """
    answer_a = await ask(prompt_a, system="You are a clinical assistant. Give a brief medical recommendation.")
    answer_b = await ask(prompt_b, system="You are a clinical assistant. Give a brief medical recommendation.")

    return {"answer_a": answer_a, "answer_b": answer_b}


async def ask_rag(context: str, question: str) -> str:
    """
    Answer a question based ONLY on the given context (patient report).
    Used by RAGAS benchmark to test faithfulness.
    """
    prompt = f"""You are given a patient report. Answer the question using ONLY the information in the report.
If the answer is not in the report, say exactly: "Not found in report."

Patient Report:
{context}

Question: {question}

Answer:"""

    system = "You are a medical document reader. Only use the provided document to answer. Do not use outside knowledge."

    return await ask(prompt, system)