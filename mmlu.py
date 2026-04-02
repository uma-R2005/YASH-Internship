import json
import os
from groq_client import ask_mcq

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


async def run_mmlu(subject: str = "clinical") -> dict:
    """
    Loads medical MCQ questions from JSON,
    asks Groq to answer each one,
    returns score + per-question breakdown.
    """
    # Load the right question file
    if subject == "anatomy":
        filepath = os.path.join(DATA_DIR, "mmlu_anatomy.json")
    else:
        filepath = os.path.join(DATA_DIR, "mmlu_clinical.json")

    with open(filepath, "r") as f:
        questions = json.load(f)

    results = []
    correct_count = 0

    for q in questions:
        # Ask Groq the MCQ question
        model_answer = await ask_mcq(q["question"], q["options"])
        is_correct = model_answer.upper() == q["correct"].upper()

        if is_correct:
            correct_count += 1

        results.append({
            "id": q["id"],
            "question": q["question"],
            "options": q["options"],
            "model_answer": model_answer,
            "correct_answer": q["correct"],
            "passed": is_correct
        })

    score = correct_count / len(questions) if questions else 0

    return {
        "score": round(score, 3),
        "correct": correct_count,
        "total": len(questions),
        "questions": results
    }