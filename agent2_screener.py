"""
Agent 2 — Screener Agent
Scores resume using Groq LLM (free).
"""

import json
from config.settings import SCORE_THRESHOLD
from config.job_descriptions import JOB_DESCRIPTIONS, DEFAULT_JOB
from utils.pdf_parser import extract_text_from_pdf
from utils.groq_client import call_groq


SYSTEM_PROMPT = """
You are an expert HR recruiter. Evaluate the candidate's resume against the job description.
Respond ONLY with valid JSON — no markdown, no explanation, no extra text.

Format:
{
  "score": <integer 0-100>,
  "strengths": ["strength 1", "strength 2", "strength 3"],
  "gaps": ["gap 1", "gap 2"],
  "summary": "One sentence summary of the candidate"
}
"""


def score_resume(resume_text: str, job_role: str) -> dict:
    job_description = JOB_DESCRIPTIONS.get(job_role, JOB_DESCRIPTIONS[DEFAULT_JOB])

    user_prompt = f"""
Job Description:
{job_description}

Candidate Resume:
{resume_text[:3000]}

Evaluate this candidate and return the JSON scorecard.
"""
    raw = call_groq(SYSTEM_PROMPT, user_prompt)
    raw = raw.strip().removeprefix("```json").removeprefix("```").removesuffix("```").strip()

    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        print("[Agent 2 - Screener] ⚠️  Could not parse JSON. Using fallback.")
        return {
            "score":     0,
            "strengths": [],
            "gaps":      ["Could not parse resume response"],
            "summary":   "Parsing error"
        }


def run(application: dict) -> dict:
    print(f"\n[Agent 2 - Screener] Scoring resume: {application['name']}")

    resume_text = extract_text_from_pdf(application["resume_path"])

    if not resume_text.strip():
        print("[Agent 2 - Screener] ❌ Empty resume — auto-rejecting.")
        application.update({
            "score":          0,
            "strengths":      [],
            "gaps":           ["Could not extract text from resume PDF"],
            "summary":        "Resume unreadable.",
            "recommendation": "reject",
        })
        return application

    scorecard      = score_resume(resume_text, application["job_role"])
    score          = scorecard.get("score", 0)
    recommendation = "shortlist" if score >= SCORE_THRESHOLD else "reject"

    application.update({
        "score":          score,
        "strengths":      scorecard.get("strengths", []),
        "gaps":           scorecard.get("gaps", []),
        "summary":        scorecard.get("summary", ""),
        "recommendation": recommendation,
    })

    icon = "✅" if recommendation == "shortlist" else "❌"
    print(f"[Agent 2 - Screener] {icon} Score: {score}/100 → {recommendation.upper()}")
    print(f"                     Summary: {application['summary']}")

    return application