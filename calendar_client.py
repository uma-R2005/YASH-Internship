import os
from datetime import datetime, timedelta
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import GOOGLE_CREDENTIALS, GOOGLE_TOKEN, GMAIL_SCOPES, INTERVIEW_DURATION


def get_calendar_service():
    """Authenticate and return Google Calendar API service."""
    creds = None
    if os.path.exists(GOOGLE_TOKEN):
        creds = Credentials.from_authorized_user_file(GOOGLE_TOKEN, GMAIL_SCOPES)

    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(GOOGLE_CREDENTIALS, GMAIL_SCOPES)
            creds = flow.run_local_server(port=0)
        with open(GOOGLE_TOKEN, "w") as f:
            f.write(creds.to_json())

    return build("calendar", "v3", credentials=creds)


def find_free_slot(service, days_ahead: int = 7) -> dict | None:
    """
    Finds the first available 1-hour slot in the next N days.
    Returns a dict with start and end ISO datetime strings.
    Checks between 10 AM and 5 PM on each day.
    """
    now = datetime.utcnow()

    for day_offset in range(1, days_ahead + 1):
        target_date = now + timedelta(days=day_offset)

        for hour in [10, 11, 14, 15, 16]:  # Check 10am, 11am, 2pm, 3pm, 4pm
            slot_start = target_date.replace(hour=hour, minute=0, second=0, microsecond=0)
            slot_end   = slot_start + timedelta(minutes=INTERVIEW_DURATION)

            # Check if slot is free using freebusy query
            body = {
                "timeMin": slot_start.isoformat() + "Z",
                "timeMax": slot_end.isoformat() + "Z",
                "items": [{"id": "primary"}]
            }
            result = service.freebusy().query(body=body).execute()
            busy_times = result["calendars"]["primary"]["busy"]

            if not busy_times:
                return {
                    "start": slot_start.isoformat() + "Z",
                    "end":   slot_end.isoformat() + "Z",
                    "display": slot_start.strftime("%A, %B %d at %I:%M %p UTC")
                }

    return None  # No free slot found in next N days


def book_interview(service, candidate_name: str, candidate_email: str, slot: dict) -> str:
    """
    Books a Google Calendar event for the interview.
    Returns the event ID.
    """
    event = {
        "summary": f"Interview - {candidate_name}",
        "description": "Candidate interview scheduled by HR Recruitment Agent.",
        "start": {"dateTime": slot["start"], "timeZone": "UTC"},
        "end":   {"dateTime": slot["end"],   "timeZone": "UTC"},
        "attendees": [{"email": candidate_email}],
    }

    created = service.events().insert(calendarId="primary", body=event).execute()
    print(f"[Calendar] Interview booked: {created.get('id')}")
    return created.get("id")
