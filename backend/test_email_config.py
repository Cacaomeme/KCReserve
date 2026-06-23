import os
import smtplib
from email.message import EmailMessage

import pytest

def _run_email_config(
    *,
    mail_server: str,
    mail_port: str,
    mail_username: str,
    mail_password: str,
    mail_use_tls: bool,
    recipient: str,
) -> None:
    print("--- Email Configuration Test ---")
    print(f"\nAttempting to connect to {mail_server}:{mail_port}...")

    msg = EmailMessage()
    msg.set_content("This is a test email from KC Reserve debug script.")
    msg['Subject'] = "KC Reserve Email Test"
    msg['From'] = mail_username
    msg['To'] = recipient

    try:
        server = smtplib.SMTP(mail_server, int(mail_port))
        server.set_debuglevel(1) # Show SMTP conversation
        
        if mail_use_tls:
            print("Starting TLS...")
            server.starttls()
        
        print("Logging in...")
        server.login(mail_username, mail_password)
        
        print("Sending message...")
        server.send_message(msg)
        server.quit()
        
        print("\nSUCCESS: Email sent successfully!")
        print("Please check your inbox (and spam folder).")
        
    except Exception as e:
        print(f"\nFAILED: {e}")
        print("\nTroubleshooting tips:")
        print("1. If using Gmail, you MUST use an 'App Password', not your login password.")
        print("   Go to Google Account > Security > 2-Step Verification > App passwords.")
        print("2. Check if the server and port are correct (smtp.gmail.com:587 is standard for TLS).")
        print("3. Check your internet connection.")


def test_email_config():
    required_env = ("MAIL_SERVER", "MAIL_USERNAME", "MAIL_PASSWORD", "MAIL_TEST_RECIPIENT")
    missing = [name for name in required_env if not os.environ.get(name)]
    if missing:
        pytest.skip(
            "Email configuration smoke test requires environment variables: "
            + ", ".join(required_env)
        )

    _run_email_config(
        mail_server=os.environ["MAIL_SERVER"],
        mail_port=os.environ.get("MAIL_PORT", "587"),
        mail_username=os.environ["MAIL_USERNAME"],
        mail_password=os.environ["MAIL_PASSWORD"],
        mail_use_tls=os.environ.get("MAIL_USE_TLS", "True").lower() == "true",
        recipient=os.environ["MAIL_TEST_RECIPIENT"],
    )


if __name__ == "__main__":
    _run_email_config(
        mail_server=os.environ.get("MAIL_SERVER") or input("MAIL_SERVER (e.g., smtp.gmail.com): ").strip(),
        mail_port=os.environ.get("MAIL_PORT") or input("MAIL_PORT (default 587): ").strip() or "587",
        mail_username=os.environ.get("MAIL_USERNAME") or input("MAIL_USERNAME: ").strip(),
        mail_password=os.environ.get("MAIL_PASSWORD") or input("MAIL_PASSWORD (App Password if Gmail): ").strip(),
        mail_use_tls=os.environ.get("MAIL_USE_TLS", "True").lower() == "true",
        recipient=os.environ.get("MAIL_TEST_RECIPIENT") or input("Enter a recipient email address for the test: ").strip(),
    )
