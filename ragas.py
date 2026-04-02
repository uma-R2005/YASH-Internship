import os
from groq_client import ask_rag

DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "data")

# Questions to test against the patient report
# answerable=True  → answer IS in the document (model should find it)
# answerable=False → answer is NOT in document (model should say "Not found in report")
RAGAS_QUESTIONS = [
    {
        "id": "ragas_001",
        "question": "What is the patient's name?",
        "correct_answer": "Ravi Kumar",
        "answerable": True
    },
    {
        "id": "ragas_002",
        "question": "What is the primary diagnosis?",
        "correct_answer": "Type 2 Diabetes Mellitus",
        "answerable": True
    },
    {
        "id": "ragas_003",
        "question": "What medication is prescribed for diabetes?",
        "correct_answer": "Metformin 500mg twice daily",
        "answerable": True
    },
    {
        "id": "ragas_004",
        "question": "What is the patient allergic to?",
        "correct_answer": "Penicillin and Sulfonamides",
        "answerable": True
    },
    {
        "id": "ragas_005",
        "question": "What was the patient's HbA1c result?",
        "correct_answer": "9.4%",
        "answerable": True
    },
    {
        "id": "ragas_006",
        "question": "When is the follow-up with endocrinology?",
        "correct_answer": "2 weeks from discharge (March 29, 2024)",
        "answerable": True
    },
    {
        "id": "ragas_007",
        "question": "What is the patient's blood group?",
        "correct_answer": "B+",
        "answerable": True
    },
    {
        "id": "ragas_008",
        "question": "Which hospital was the patient admitted to?",
        "correct_answer": "Apollo Multispecialty Hospital, Hyderabad",
        "answerable": True
    },
    {
        "id": "ragas_009",
        "question": "What is the patient's previous surgery history?",
        "correct_answer": "Not found in report.",
        "answerable": False
    },
    {
        "id": "ragas_010",
        "question": "What is the patient's family history of diabetes?",
        "correct_answer": "Not found in report.",
        "answerable": False
    },
    {
        "id": "ragas_011",
        "question": "What is the recommended daily water intake for the patient?",
        "correct_answer": "At least 2.5 litres per day",
        "answerable": True
    },
    {
        "id": "ragas_012",
        "question": "Who is the treating physician?",
        "correct_answer": "Dr. Sneha Reddy",
        "answerable": True
    },
    {
        "id": "ragas_013",
        "question": "What is the patient's job or occupation?",
        "correct_answer": "Not found in report.",
        "answerable": False
    },
    {
        "id": "ragas_014",
        "question": "What medication is prescribed for hypertension?",
        "correct_answer": "Amlodipine 5mg once daily",
        "answerable": True
    },
    {
        "id": "ragas_015",
        "question": "How many cigarettes does the patient smoke per day?",
        "correct_answer": "10 cigarettes per day",
        "answerable": True
    }
]


def check_answer(model_answer: str, correct_answer: str, answerable: bool) -> bool:
    """
    For answerable questions: check if key words from correct answer appear in model answer.
    For unanswerable questions: check if model correctly said 'not found'.
    """
    model_lower = model_answer.lower()

    if not answerable:
        # Model should say "not found in report"
        return "not found" in model_lower

    # Check if key words from correct answer appear in model's answer
    key_words = correct_answer.lower().replace(",", "").split()
    # At least 50% of key words should match
    matches = sum(1 for word in key_words if word in model_lower)
    return matches / len(key_words) >= 0.5 if key_words else False


async def run_ragas() -> dict:
    """
    Loads patient report,
    asks questions about it,
    checks if model answers faithfully from the document.
    """
    report_path = os.path.join(DATA_DIR, "patient_report.txt")

    with open(report_path, "r") as f:
        patient_report = f.read()

    results = []
    correct_count = 0

    for q in RAGAS_QUESTIONS:
        # Ask Groq to answer from document only
        model_answer = await ask_rag(patient_report, q["question"])
        is_correct = check_answer(model_answer, q["correct_answer"], q["answerable"])

        if is_correct:
            correct_count += 1

        results.append({
            "id": q["id"],
            "question": q["question"],
            "model_answer": model_answer,
            "correct_answer": q["correct_answer"],
            "answerable": q["answerable"],
            "passed": is_correct
        })

    score = correct_count / len(RAGAS_QUESTIONS)

    return {
        "score": round(score, 3),
        "correct": correct_count,
        "total": len(RAGAS_QUESTIONS),
        "questions": results
    }