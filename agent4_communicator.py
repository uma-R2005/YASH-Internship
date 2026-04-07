"""
Agent 4 — Communicator Agent
Sends emails via Gmail SMTP and logs outcomes.
"""

import os
import json
from datetime import datetime

from config.settings import COMPANY_NAME, LOG_DIR
from utils.email_client import send_email
from utils.groq_client import call_groq


def _generate_invite_email(application: dict) -> str:
    prompt = f"""
Write a professional interview invitation email body only (no subject line).
- Candidate Name: {application['name']}
- Applied for: {application['job_role'].replace('_', ' ').title()}
- Company: {COMPANY_NAME}
- Interview Slot: {application.get('interview_slot', 'TBD')}
- Key strengths: {', '.join(application.get('strengths', []))}
Keep it under 150 words. Be warm. Ask them to confirm by replying.
Sign off as "HR Team, {COMPANY_NAME}"
"""
    return call_groq("You are a professional HR recruiter writing candidate emails.", prompt)


def _generate_rejection_email(application: dict) -> str:
    prompt = f"""
Write a professional rejection email body only (no subject line).
- Candidate Name: {application['name']}
- Applied for: {application['job_role'].replace('_', ' ').title()}
- Company: {COMPANY_NAME}
Keep it under 120 words. Be kind and encouraging.
Do NOT mention their score. Sign off as "HR Team, {COMPANY_NAME}"
"""
    return call_groq("You are a professional HR recruiter writing candidate emails.", prompt)


def _log_outcome(application: dict):
    os.makedirs(LOG_DIR, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_path  = os.path.join(LOG_DIR, f"{timestamp}_{application['recommendation']}_{application['name'].replace(' ','_')}.json")
    log_data  = {
        "timestamp":      timestamp,
        "name":           application["name"],
        "email":          application["email"],
        "job_role":       application["job_role"],
        "score":          application.get("score"),
        "recommendation": application["recommendation"],
        "strengths":      application.get("strengths", []),
        "gaps":           application.get("gaps", []),
        "summary":        application.get("summary", ""),
        "interview_slot": application.get("interview_slot"),
        "email_sent":     application.get("email_sent", False),
    }
    with open(log_path, "w") as f:
        json.dump(log_data, f, indent=2)
    print(f"[Agent 4 - Communicator] 📝 Logged → {log_path}")


def run(application: dict) -> dict:
    print(f"\n[Agent 4 - Communicator] Preparing email for: {application['name']}")

    role_title = application["job_role"].replace("_", " ").title()

    if application["recommendation"] == "shortlist":
        subject = f"Interview Invitation - {role_title} at {COMPANY_NAME}"
        body    = _generate_invite_email(application)
        print("[Agent 4 - Communicator] ✅ Sending interview invitation...")
    else:
        subject = f"Your Application for {role_title} at {COMPANY_NAME}"
        body    = _generate_rejection_email(application)
        print("[Agent 4 - Communicator] ❌ Sending rejection email...")

    sent = send_email(to=application["email"], subject=subject, body=body)
    application["email_sent"] = sent
    _log_outcome(application)
    return application