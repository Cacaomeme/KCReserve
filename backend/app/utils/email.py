import smtplib
import threading
from email.message import EmailMessage
from app.config import get_settings
from app.models.user import User
from app.models.reservation import Reservation
from app.database import session_scope

def _send_email_sync(to_email: str, subject: str, body: str):
    settings = get_settings()
    if not settings.mail_server or not settings.mail_username or not settings.mail_password:
        print("Email settings not configured. Skipping email.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = settings.mail_default_sender or settings.mail_username
    msg['To'] = to_email

    try:
        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            if settings.mail_use_tls:
                server.starttls()
            server.login(settings.mail_username, settings.mail_password)
            server.send_message(msg)
        print(f"Email sent to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {e}")

def send_email_async(to_email: str, subject: str, body: str):
    thread = threading.Thread(target=_send_email_sync, args=(to_email, subject, body))
    thread.start()

def send_new_reservation_notification(reservation_id: int):
    def _notify():
        with session_scope() as session:
            reservation = session.get(Reservation, reservation_id)
            if not reservation:
                return
            
            # Eager load user to avoid detachment issues if we were passing object
            # But here we are in a session, so it's fine.
            user_name = reservation.user.display_name if reservation.user else "Unknown"
            user_email = reservation.user.email if reservation.user else "Unknown"
            purpose = reservation.purpose
            start = reservation.start_time
            end = reservation.end_time
            count = reservation.attendee_count
            desc = reservation.description or 'なし'

            admins = session.query(User).filter(
                User.is_admin == True,
                User.receives_notification == True
            ).all()
            
            admin_emails = [admin.email for admin in admins]
        
        if not admin_emails:
            return

        subject = f"【KC Reserve】新規予約申請: {purpose}"
        body = f"""
新規の予約申請がありました。

申請者: {user_name} ({user_email})
目的: {purpose}
日時: {start} - {end}
人数: {count}人
詳細: {desc}

管理画面から確認・承認してください。
"""

        for email in admin_emails:
            _send_email_sync(email, subject, body)

    thread = threading.Thread(target=_notify)
    thread.start()
