# 🤖 HR Recruitment Agent — Automated Candidate Screening Pipeline

An intermediate-level **agent-to-agent architecture** that automates resume screening, candidate scoring, interview scheduling, and email communication — all for free, with no admin access required.

Built with **Groq (free LLM)**, **Gmail SMTP**, and **local file-based scheduling**.

---

## 📌 Project Overview

HR teams waste hours manually reading resumes, scoring candidates, sending follow-up emails, and scheduling interviews. This project automates that entire pipeline using 4 specialized AI agents that hand off work to each other in sequence.

```
Agent 1 (Intake) → Agent 2 (Screener) → Agent 3 (Scheduler) → Agent 4 (Communicator)
```

---

## 🏗️ Architecture

### Agent 1 — Intake Agent
- Watches a local `data/resumes/incoming/` folder for resume PDFs
- Parses the filename to extract candidate name, job role, and email
- Passes a structured application object to Agent 2

### Agent 2 — Screener Agent
- Reads the resume PDF using `pdfplumber`
- Sends the resume text to Groq's Llama 3.3 70B model for evaluation
- Returns a scorecard: `{ score, strengths, gaps, summary }`
- Routes to shortlist (≥70 score) or reject

### Agent 3 — Scheduler Agent
- Finds the next available interview slot in the next 7 business days
- Books the slot to a local `data/schedules/interviews.csv` file
- Passes the confirmed slot back to the pipeline

### Agent 4 — Communicator Agent
- Uses Groq to generate a personalized email (invite or rejection)
- Sends it via Gmail SMTP using an App Password (no OAuth needed)
- Logs the full outcome as a JSON file in `data/logs/`

---

## 💡 Key Concepts Demonstrated

| Concept | Implementation |
|---|---|
| Agent handoff | Structured JSON dict grows richer at each agent hop |
| Conditional routing | Agent 2 acts as orchestrator — shortlist vs. reject path |
| LLM tool use | Groq Llama 3.3 for resume parsing and email generation |
| Error handling | Graceful fallback if PDF is unreadable or LLM fails |
| State passing | Single `application` dict flows through all agents |
| Free + no-admin | No OAuth, no cloud APIs, no install privileges needed |

---

## 🧰 Tech Stack

| Component | Tool | Cost |
|---|---|---|
| LLM (resume scoring + email drafting) | [Groq API](https://console.groq.com) — Llama 3.3 70B | Free |
| Email sending | Gmail SMTP + App Password | Free |
| PDF text extraction | `pdfplumber` | Free |
| Interview scheduling | Local CSV file | Free |
| Orchestration | Plain Python | Free |

---

## 📁 Project Structure

```
hr_recruitment_agent/
│
├── main.py                          # Pipeline orchestrator
│
├── agents/
│   ├── agent1_intake.py             # Scans folder, parses filenames
│   ├── agent2_screener.py           # Scores resume with Groq LLM
│   ├── agent3_scheduler.py          # Books interview slot in CSV
│   └── agent4_communicator.py      # Sends emails, logs outcomes
│
├── config/
│   ├── settings.py                  # Env vars and constants
│   └── job_descriptions.py          # Role-specific JD templates
│
├── utils/
│   ├── groq_client.py               # Groq API wrapper
│   ├── pdf_parser.py                # PDF text extraction
│   ├── email_client.py              # Gmail SMTP sender
│   └── scheduler.py                 # Slot finder and CSV booker
│
├── data/
│   ├── resumes/
│   │   ├── incoming/                # ← Drop resume PDFs here
│   │   └── processed/               # Processed resumes moved here
│   ├── logs/                        # JSON outcome logs per candidate
│   └── schedules/
│       └── interviews.csv           # Booked interview slots
│
├── tests/
│   ├── test_agent2.py               # Test LLM scoring independently
│   └── test_email.py                # Test Gmail SMTP independently
│
├── .env.example                     # Environment variable template
├── requirements.txt
└── README.md
```

### Expected output

```
═══════════════════════════════════════════════════════
  🤖 HR RECRUITMENT PIPELINE STARTED
═══════════════════════════════════════════════════════

[Agent 1 - Intake]       ✅ Found: John Doe | Role: python_developer
[Agent 2 - Screener]     ✅ Score: 95/100 → SHORTLIST
                          Summary: Highly skilled Python developer with 3 years of experience
[Agent 3 - Scheduler]    📅 Booked: Wednesday, 08 April 2026 at 10:00 AM
[Agent 4 - Communicator] ✅ Sending interview invitation...
[Email]                  ✅ Sent to john@gmail.com
[Agent 4 - Communicator] 📝 Logged → data/logs/20260408_john_doe.json
[Agent 1 - Intake]       📁 Moved to processed

  ✔ DONE | John Doe
    Score:    95/100
    Decision: SHORTLIST
    Interview: Wednesday, 08 April 2026 at 10:00 AM
    Email sent: Yes

═══════════════════════════════════════════════════════
  PIPELINE COMPLETE
  Total processed : 1
  Shortlisted     : 1
  Rejected        : 0
  Logs saved in   : data/logs/
  Schedule saved  : data/schedules/interviews.csv
═══════════════════════════════════════════════════════
```

---

## 📊 How Scoring Works

Agent 2 sends the resume and the job description to Groq and receives:

```json
{
  "score": 95,
  "strengths": ["Strong Python and FastAPI experience", "Proficient in Docker and AWS"],
  "gaps": ["No open source contributions"],
  "summary": "Highly skilled Python developer with 3 years experience in backend systems."
}
```

- Score **≥ 70** → Shortlisted → interview invite sent
- Score **< 70** → Rejected → polite rejection email sent

The threshold is configurable via `SCREENING_SCORE_THRESHOLD` in `.env`.

---

