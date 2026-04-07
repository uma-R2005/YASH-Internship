import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config.settings import HR_EMAIL, HR_EMAIL_PASSWORD, SMTP_HOST, SMTP_PORT


def send_email(to: str, subject: str, body: str) -> bool:
    """
    Sends an email using Gmail SMTP + App Password.
    No OAuth, no admin access needed.
    Returns True if sent successfully.
    """
    try:
        msg = MIMEMultipart()
        msg["From"]    = HR_EMAIL
        msg["To"]      = to
        msg["Subject"] = subject
        msg.attach(MIMEText(body, "plain"))

        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.ehlo()
            server.starttls()
            server.login(HR_EMAIL, HR_EMAIL_PASSWORD)
            server.sendmail(HR_EMAIL, to, msg.as_string())

        print(f"[Email] ✅ Sent to {to}")
        return True

    except smtplib.SMTPAuthenticationError:
        print("[Email] ❌ Authentication failed.")
        print("         Make sure you're using an App Password, not your Gmail password.")
        print("         Go to: myaccount.google.com → Search 'App Passwords'")
        return False

    except Exception as e:
        print(f"[Email] ❌ Failed to send email: {e}")
        return False