import os
from dotenv import load_dotenv

load_dotenv()

# ── Groq ─────────────────────────────────────────────
GROQ_API_KEY   = os.getenv("GROQ_API_KEY")
GROQ_MODEL     = "llama-3.3-70b-versatile"

# ── Gmail SMTP ────────────────────────────────────────
HR_EMAIL           = os.getenv("HR_EMAIL")
HR_EMAIL_PASSWORD  = os.getenv("HR_EMAIL_APP_PASSWORD")
SMTP_HOST          = "smtp.gmail.com"
SMTP_PORT          = 587

# ── Pipeline ──────────────────────────────────────────
SCORE_THRESHOLD    = int(os.getenv("SCREENING_SCORE_THRESHOLD", 70))
INTERVIEW_DURATION = int(os.getenv("INTERVIEW_DURATION_MINUTES", 60))
COMPANY_NAME       = os.getenv("COMPANY_NAME", "Our Company")

# ── Folders ───────────────────────────────────────────
INCOMING_DIR   = "data/resumes/incoming"
PROCESSED_DIR  = "data/resumes/processed"
LOG_DIR        = "data/logs"
SCHEDULE_FILE  = "data/schedules/interviews.csv"