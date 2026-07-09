import random
import smtplib
from datetime import datetime, timedelta
from email.message import EmailMessage

from .config import EMAIL_ADDRESS, EMAIL_PASSWORD, EMAIL_REGEX, OTP_EXPIRY_SECONDS
from .db import get_db_connection


def is_valid_email(email):
    return bool(EMAIL_REGEX.match(email or ""))


def generate_otp(length=6):
    return "".join(str(random.randint(0, 9)) for _ in range(length))


def send_email(to_email, subject, body):
    if not EMAIL_ADDRESS or not EMAIL_PASSWORD:
        return False, "Email credentials not configured."
    try:
        msg = EmailMessage()
        msg.set_content(body)
        msg["Subject"] = subject
        msg["From"] = EMAIL_ADDRESS
        msg["To"] = to_email
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
            server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
            server.send_message(msg)
        return True, "Email sent successfully."
    except Exception as e:
        return False, f"Could not send email to {to_email} ({e})."


def send_otp_email(recipient_email, recipient_name, otp, purpose):
    subject = "Your OTP for Digital Voting System"
    body = (
        f"Hello {recipient_name},\n\n"
        f"Your OTP is: {otp}\n"
        f"It is valid for {OTP_EXPIRY_SECONDS // 60} minutes.\n\n"
        f"Enter this code to continue."
    )
    if purpose == "admin":
        subject = "Admin login verification"
        body = (
            f"Hello {recipient_name},\n\n"
            f"Your admin OTP is: {otp}\n"
            f"It expires in {OTP_EXPIRY_SECONDS // 60} minutes.\n\n"
            f"Enter this code to continue."
        )
    return send_email(recipient_email, subject, body)


def save_otp_for_record(record_type, record_id, otp, expires_at):
    conn = get_db_connection()
    cursor = conn.cursor()
    if record_type == "voter":
        cursor.execute("UPDATE voters SET verification_otp = %s, verification_expires_at = %s WHERE id = %s", (otp, expires_at, record_id))
    else:
        cursor.execute("UPDATE candidates SET verification_otp = %s, verification_expires_at = %s WHERE id = %s", (otp, expires_at, record_id))
    conn.commit()
    cursor.close()
    conn.close()


def send_verification_otp(record_type, record_id, recipient_email, recipient_name):
    otp = generate_otp()
    expires_at = (datetime.now() + timedelta(seconds=OTP_EXPIRY_SECONDS)).isoformat()
    save_otp_for_record(record_type, record_id, otp, expires_at)
    subject = "Verify your email"
    body = (
        f"Hello {recipient_name},\n\n"
        f"Your verification code is: {otp}\n"
        f"It expires in {OTP_EXPIRY_SECONDS // 60} minutes.\n\n"
        f"Open the verification page to activate your account."
    )
    email_sent, email_message = send_email(recipient_email, subject, body)
    return {
        "otp": otp,
        "email_sent": email_sent,
        "email_message": email_message,
    }
