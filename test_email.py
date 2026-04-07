"""
Test Gmail SMTP connection before running the full pipeline.
Run: python tests/test_email.py

If this works → Agent 4 will work fine.
"""

import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.email_client import send_email
from config.settings import HR_EMAIL


def test():
    print("=" * 50)
    print("  Testing Gmail SMTP Connection")
    print("=" * 50)
    print(f"  Sending test email to: {HR_EMAIL}")

    result = send_email(
        to=HR_EMAIL,   # Sends to yourself as a test
        subject="✅ HR Agent - SMTP Test",
        body=(
            "This is a test email from your HR Recruitment Agent.\n\n"
            "If you received this, Gmail SMTP is working correctly!\n\n"
            "— HR Recruitment Agent"
        ),
    )

    if result:
        print("\n  ✅ Email sent! Check your inbox.")
    else:
        print("\n  ❌ Email failed. Check your .env App Password.")
    print("=" * 50)


if __name__ == "__main__":
    test()