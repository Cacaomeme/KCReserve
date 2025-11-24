import smtplib
import threading
import sys
import traceback
import socket
from datetime import datetime, timedelta, timezone
from email.message import EmailMessage
from app.config import get_settings
from app.models.user import User
from app.models.reservation import Reservation
from app.database import session_scope

def log(msg):
    print(f"[EMAIL DEBUG] {msg}", file=sys.stdout, flush=True)

def _send_email_sendgrid(to_email: str, subject: str, body: str, api_key: str, from_email: str):
    import json
    import urllib.request
    import urllib.error

    log("Attempting to send via SendGrid API...")
    url = "https://api.sendgrid.com/v3/mail/send"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "personalizations": [{"to": [{"email": to_email}]}],
        "from": {"email": from_email},
        "subject": subject,
        "content": [{"type": "text/plain", "value": body}]
    }

    try:
        req = urllib.request.Request(url, data=json.dumps(data).encode('utf-8'), headers=headers, method='POST')
        with urllib.request.urlopen(req) as response:
            log(f"SendGrid response: {response.status}")
            if 200 <= response.status < 300:
                log(f"Email sent successfully to {to_email} via SendGrid")
                return True
    except urllib.error.HTTPError as e:
        log(f"SendGrid failed: {e.code} {e.read().decode('utf-8')}")
    except Exception as e:
        log(f"SendGrid failed: {e}")
    return False

def _send_email_sync(to_email: str, subject: str, body: str):
    settings = get_settings()
    
    # Try SendGrid first if configured (Recommended for Render)
    if settings.sendgrid_api_key:
        if _send_email_sendgrid(to_email, subject, body, settings.sendgrid_api_key, settings.mail_default_sender or settings.mail_username):
            return

    if not settings.mail_server or not settings.mail_username or not settings.mail_password:
        log("Email settings not configured. Skipping email.")
        return

    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = subject
    msg['From'] = settings.mail_default_sender or settings.mail_username
    msg['To'] = to_email

    # Remove spaces from password just in case (Gmail app passwords often have spaces)
    password = settings.mail_password.replace(" ", "")

    try:
        # Force IPv4 resolution to avoid [Errno 101] Network is unreachable on IPv6-disabled environments
        log(f"Resolving {settings.mail_server} (IPv4)...")
        addr_info = socket.getaddrinfo(settings.mail_server, settings.mail_port, socket.AF_INET, socket.SOCK_STREAM)
        server_ip = addr_info[0][4][0]
        log(f"Resolved to {server_ip}")

        log(f"Connecting to {server_ip}:{settings.mail_port} with timeout=30s...")
        
        if settings.mail_port == 465:
            # Use implicit SSL for port 465
            import ssl
            context = ssl.create_default_context()
            context.check_hostname = False
            
            with smtplib.SMTP_SSL(server_ip, settings.mail_port, context=context, timeout=30) as server:
                log("Connected. Logging in...")
                server.login(settings.mail_username, password)
                
                log(f"Sending message to {to_email}...")
                server.send_message(msg)
        else:
            # Use STARTTLS for port 587 (or others)
            with smtplib.SMTP(server_ip, settings.mail_port, timeout=30) as server:
                # server.set_debuglevel(1)
                if settings.mail_use_tls:
                    log("Connected. Starting TLS...")
                    import ssl
                    context = ssl.create_default_context()
                    context.check_hostname = False
                    server.starttls(context=context)
                
                log("Logging in...")
                server.login(settings.mail_username, password)
                
                log(f"Sending message to {to_email}...")
                server.send_message(msg)
                
        log(f"Email sent successfully to {to_email}")
    except Exception as e:
        log(f"Failed to send email to {to_email}: {e}")
        traceback.print_exc()

def send_email_async(to_email: str, subject: str, body: str):
    thread = threading.Thread(target=_send_email_sync, args=(to_email, subject, body))
    thread.start()

def send_new_reservation_notification(reservation_id: int):
    def _notify():
        log(f"Starting notification thread for reservation {reservation_id}")
        try:
            with session_scope() as session:
                reservation = session.get(Reservation, reservation_id)
                if not reservation:
                    log(f"Reservation {reservation_id} not found in thread.")
                    return
                
                # Eager load user to avoid detachment issues if we were passing object
                # But here we are in a session, so it's fine.
                user_name = reservation.user.display_name if reservation.user else "Unknown"
                user_email = reservation.user.email if reservation.user else "Unknown"
                purpose = reservation.purpose
                start = _format_dt_jst(reservation.start_time)
                end = _format_dt_jst(reservation.end_time)
                count = reservation.attendee_count
                desc = reservation.description or 'なし'

                admins = session.query(User).filter(
                    User.is_admin == True,
                    User.receives_notification == True
                ).all()
                
                admin_emails = [admin.email for admin in admins]
                log(f"Found {len(admin_emails)} admins to notify: {admin_emails}")
            
            if not admin_emails:
                log("No admins to notify.")
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
https://kcreserve-frontend.onrender.com/
"""

            for email in admin_emails:
                _send_email_sync(email, subject, body)
        except Exception as e:
            log(f"Error in notification thread: {e}")
            traceback.print_exc()

    thread = threading.Thread(target=_notify)
    thread.start()

def send_cancellation_request_notification(reservation_id: int):
    def _notify():
        log(f"Starting cancellation notification thread for reservation {reservation_id}")
        try:
            with session_scope() as session:
                reservation = session.get(Reservation, reservation_id)
                if not reservation:
                    log(f"Reservation {reservation_id} not found in thread.")
                    return
                
                user_name = reservation.user.display_name if reservation.user else "Unknown"
                user_email = reservation.user.email if reservation.user else "Unknown"
                purpose = reservation.purpose
                start = _format_dt_jst(reservation.start_time)
                end = _format_dt_jst(reservation.end_time)
                reason = reservation.cancellation_reason or 'なし'

                admins = session.query(User).filter(
                    User.is_admin == True,
                    User.receives_notification == True
                ).all()
                
                admin_emails = [admin.email for admin in admins]
                log(f"Found {len(admin_emails)} admins to notify: {admin_emails}")
            
            if not admin_emails:
                log("No admins to notify.")
                return

            subject = f"【KC Reserve】キャンセル申請: {purpose}"
            body = f"""
予約のキャンセル申請がありました。

申請者: {user_name} ({user_email})
目的: {purpose}
日時: {start} - {end}
キャンセル理由: {reason}

管理画面から確認・承認してください。
https://kcreserve-frontend.onrender.com/
"""

            for email in admin_emails:
                _send_email_sync(email, subject, body)
        except Exception as e:
            log(f"Error in cancellation notification thread: {e}")
            traceback.print_exc()

    thread = threading.Thread(target=_notify)
    thread.start()

JST = timezone(timedelta(hours=9))

def _format_dt_jst(dt):
    if not dt:
        return ""
    # If naive, assume UTC
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    
    dt_jst = dt.astimezone(JST)
    return dt_jst.strftime("%Y/%m/%d %H:%M")
