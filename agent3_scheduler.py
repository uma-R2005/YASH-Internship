"""
Agent 3 — Scheduler Agent
Finds free interview slot and books it in a local CSV file.
No Google Calendar needed.
"""

from utils.scheduler import find_free_slot, book_slot


def run(application: dict) -> dict:
    print(f"\n[Agent 3 - Scheduler] Finding interview slot for: {application['name']}")

    slot = find_free_slot(days_ahead=7)

    if not slot:
        print("[Agent 3 - Scheduler] ⚠️  No free slots in next 7 days.")
        application["interview_slot"] = "To be scheduled manually"
        application["slot_start"]     = None
        return application

    book_slot(
        candidate_name=application["name"],
        candidate_email=application["email"],
        job_role=application["job_role"],
        slot=slot,
    )

    application["interview_slot"] = slot["display"]
    application["slot_start"]     = slot["start"]

    return application