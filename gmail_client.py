import os
import base64
from email.mime.text import MIMEText
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from config.settings import GOOGLE_CREDENTIALS, GOOGLE_TOKEN, GMAIL_SCOPES


def get_gmail_service():
    """Authenticate and return Gmail API service."""
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

    return build("gmail", "v1", credentials=creds)


def fetch_unread_emails_with_attachments(service) -> list[dict]:
    """
    Fetches unread emails that have PDF attachments.
    Returns a list of email dicts with metadata.
    """
    results = service.users().messages().list(
        userId="me",
        q="is:unread has:attachment filename:pdf"
    ).execute()

    messages = results.get("messages", [])
    emails = []

    for msg in messages:
        msg_detail = service.users().messages().get(userId="me", id=msg["id"]).execute()
        headers = {h["name"]: h["value"] for h in msg_detail["payload"]["headers"]}

        emails.append({
            "id":      msg["id"],
            "from":    headers.get("From", ""),
            "subject": headers.get("Subject", ""),
            "payload": msg_detail["payload"],
        })

    return emails


def download_pdf_attachment(service, message_id: str, payload: dict, save_dir: str) -> str | None:
    """
    Downloads the first PDF attachment from an email.
    Returns the local file path, or None if no PDF found.
    """
    os.makedirs(save_dir, exist_ok=True)

    parts = payload.get("parts", [])
    for part in parts:
        if part.get("mimeType") == "application/pdf":
            filename = part["filename"] or f"{message_id}.pdf"
            attachment_id = part["body"]["attachmentId"]

            attachment = service.users().messages().attachments().get(
                userId="me", messageId=message_id, id=attachment_id
            ).execute()

            data = base64.urlsafe_b64decode(attachment["data"])
            filepath = os.path.join(save_dir, filename)
            with open(filepath, "wb") as f:
                f.write(data)

            return filepath

    return None


def mark_as_read(service, message_id: str):
    """Marks a Gmail message as read."""
    service.users().messages().modify(
        userId="me",
        id=message_id,
        body={"removeLabelIds": ["UNREAD"]}
    ).execute()


def send_email(service, to: str, subject: str, body: str):
    """Sends an email via Gmail API."""
    message = MIMEText(body)
    message["to"]      = to
    message["subject"] = subject
    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()

    service.users().messages().send(
        userId="me",
        body={"raw": encoded}
    ).execute()
    print(f"[Gmail] Email sent to {to}")
