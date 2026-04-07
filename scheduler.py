import os
import csv
from datetime import datetime, timedelta

from config.settings import SCHEDULE_FILE, INTERVIEW_DURATION


INTERVIEW_HOURS = [10, 11, 14, 15, 16]


def _load_booked_slots() -> list[str]:
    """Loads already-booked slot start times from the CSV."""
    if not os.path.exists(SCHEDULE_FILE):
        return []

    booked = []
    with open(SCHEDULE_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            booked.append(row["slot_start"])
    return booked


def find_free_slot(days_ahead: int = 7) -> dict | None:
    """
    Finds the next available interview slot in the next N days.
    Skips weekends and already-booked slots.
    """
    booked = _load_booked_slots()
    now    = datetime.now()

    for day_offset in range(1, days_ahead + 1):
        target = now + timedelta(days=day_offset)

        # Skip weekends
        if target.weekday() >= 5:
            continue

        for hour in INTERVIEW_HOURS:
            slot_start = target.replace(hour=hour, minute=0, second=0, microsecond=0)
            slot_end   = slot_start + timedelta(minutes=INTERVIEW_DURATION)
            slot_key   = slot_start.strftime("%Y-%m-%d %H:%M")

            if slot_key not in booked:
                return {
                    "start":   slot_key,
                    "end":     slot_end.strftime("%Y-%m-%d %H:%M"),
                    "display": slot_start.strftime("%A, %d %B %Y at %I:%M %p"),
                }

    return None


def book_slot(candidate_name: str, candidate_email: str,
              job_role: str, slot: dict) -> bool:
    """Books an interview slot by writing it to the CSV schedule file."""
    os.makedirs(os.path.dirname(SCHEDULE_FILE), exist_ok=True)

    file_exists = os.path.exists(SCHEDULE_FILE)

    with open(SCHEDULE_FILE, "a", newline="") as f:
        fieldnames = ["slot_start", "slot_end", "candidate_name",
                      "candidate_email", "job_role", "booked_at"]
        writer = csv.DictWriter(f, fieldnames=fieldnames)

        if not file_exists:
            writer.writeheader()

        writer.writerow({
            "slot_start":      slot["start"],
            "slot_end":        slot["end"],
            "candidate_name":  candidate_name,
            "candidate_email": candidate_email,
            "job_role":        job_role,
            "booked_at":       datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        })

    print(f"[Scheduler] 📅 Booked: {slot['display']} for {candidate_name}")
    return True