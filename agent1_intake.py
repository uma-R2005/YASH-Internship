"""
Agent 1 — Intake Agent
Scans data/resumes/incoming/ folder for PDF files.

Filename format:
  firstname_lastname_jobrole_email@domain.com.pdf
Example:
  john_doe_python_developer_john@gmail.com.pdf
"""

import os
import shutil
from config.settings import INCOMING_DIR, PROCESSED_DIR
from config.job_descriptions import JOB_DESCRIPTIONS, DEFAULT_JOB


def _parse_filename(filename: str) -> dict:
    stem  = filename.replace(".pdf", "").replace(".PDF", "")
    parts = stem.split("_")

    # Extract email
    email = next((p for p in parts if "@" in p), "unknown@example.com")

    # Extract job role
    job_role = DEFAULT_JOB
    for role in JOB_DESCRIPTIONS:
        if role.replace("_", " ") in stem.replace("_", " ").lower():
            job_role = role
            break

    # Extract name (first 2 parts that are not email/role)
    name_parts = [
        p for p in parts
        if "@" not in p
        and p.lower() not in job_role.split("_")
    ]
    name = " ".join(name_parts[:2]).title() if name_parts else "Candidate"

    return {"name": name, "email": email, "job_role": job_role}


def run() -> list[dict]:
    print("\n[Agent 1 - Intake] Scanning incoming folder for resumes...")

    os.makedirs(INCOMING_DIR, exist_ok=True)
    os.makedirs(PROCESSED_DIR, exist_ok=True)

    pdf_files = [f for f in os.listdir(INCOMING_DIR) if f.lower().endswith(".pdf")]

    if not pdf_files:
        print(f"[Agent 1 - Intake] No PDFs found in {INCOMING_DIR}/")
        return []

    applications = []
    for filename in pdf_files:
        resume_path = os.path.join(INCOMING_DIR, filename)
        parsed      = _parse_filename(filename)
        application = {
            "filename":    filename,
            "resume_path": resume_path,
            "name":        parsed["name"],
            "email":       parsed["email"],
            "job_role":    parsed["job_role"],
        }
        print(f"[Agent 1 - Intake] ✅ Found: {parsed['name']} | "
              f"Role: {parsed['job_role']} | Email: {parsed['email']}")
        applications.append(application)

    return applications


def mark_processed(resume_path: str):
    filename = os.path.basename(resume_path)
    dest     = os.path.join(PROCESSED_DIR, filename)
    shutil.move(resume_path, dest)
    print(f"[Agent 1 - Intake] 📁 Moved to processed: {filename}")