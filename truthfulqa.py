import json
import os
from groq_client import ask_truefalse

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")


async def run_truthfulqa() -> dict:
    """
    Loads medical myth statements,
    asks Groq True or False for each,
    returns score + per-question breakdown.
    """
    filepath = os.path.join(DATA_DIR, "truthfulqa_medical.json")

    with open(filepath, "r") as f:
        questions = json.load(f)

    results = []
    correct_count = 0

    for q in questions:
        # Ask Groq if statement is true or false
        model_answer = await ask_truefalse(q["statement"])
        is_correct = model_answer.lower() == q["correct"].lower()

        if is_correct:
            correct_count += 1

        results.append({
            "id": q["id"],
            "question": q["statement"],
            "model_answer": model_answer,
            "correct_answer": q["correct"],
            "explanation": q["explanation"],
            "passed": is_correct
        })

    score = correct_count / len(questions) if questions else 0

    return {
        "score": round(score, 3),
        "correct": correct_count,
        "total": len(questions),
        "questions": results
    }