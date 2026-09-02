import smtplib
import os
from email.message import EmailMessage
from dotenv import load_dotenv

load_dotenv()

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587

SENDER_EMAIL = os.getenv("EMAIL_ADDRESS")
EMAIL_PASSWORD = os.getenv("EMAIL_APP_PASSWORD")


def _send_email(msg):
    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT, timeout=20) as server:
            server.starttls()
            server.login(SENDER_EMAIL, EMAIL_PASSWORD)
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Email Error: {e}")
        return False


def send_alert(blood_group, quantity, recipient_email):
    msg = EmailMessage()

    msg["Subject"] = f"URGENT: Low Stock Alert - {blood_group}"
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email

    msg.set_content(
        f"""URGENT BLOOD STOCK ALERT

The stock for {blood_group} blood has dropped to {quantity} units.

Please contact eligible donors immediately.

Regards,
Hospital Administration
"""
    )

    return _send_email(msg)


def send_donation_request(recipient_email, patient_name, missing_blood_type):
    msg = EmailMessage()

    msg["Subject"] = f"Urgent Appeal: {missing_blood_type} Blood Needed - Save a Life Today"
    msg["From"] = SENDER_EMAIL
    msg["To"] = recipient_email

    msg.set_content(
        f"""Dear {patient_name},

We hope you are in good health.

This is an urgent appeal from City Hospital. We are currently facing a critical shortage of {missing_blood_type} blood.

If you or anyone you know is eligible to donate, please visit our blood bank at your earliest convenience.

Your donation could save a life today.

Location: City Hospital, Block A
Hours: 9:00 AM - 8:00 PM

Thank you for your support.

Sincerely,
Hospital Administration
"""
    )

    return _send_email(msg)
