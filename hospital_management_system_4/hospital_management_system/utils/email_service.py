import smtplib
from email.message import EmailMessage

# Configuration
SMTP_SERVER = "127.0.0.1"
SMTP_PORT = 1025
SENDER_EMAIL = "system@hospital.com"

def send_alert(blood_group, quantity, recipient_email):
    """
    Sends a low stock alert email.
    """
    msg = EmailMessage()
    msg.set_content(f"Warning! The stock for {blood_group} has dropped to {quantity} units. Please contact donors immediately.")
    msg['Subject'] = f"URGENT: Low Stock Alert - {blood_group}"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print("=== Sending Email ===")
            print(msg.as_string())
            print("=====================")
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending email: {e}")
        return False

def send_donation_request(recipient_email, patient_name, missing_blood_type):
    """
    Sends a broadcast email requesting blood donation.
    """
    msg = EmailMessage()
    body = f"""Dear {patient_name},

We hope you are in good health.

This is an urgent appeal from City Hospital. We are currently facing a critical shortage of **{missing_blood_type}** blood in our inventory. 

As a registered member of our hospital network, we are reaching out to ask for your support. If you or anyone you know is eligible to donate, please visit our blood bank at your earliest convenience. Your donation could save a life today.

Location: City Hospital, Block A.
Hours: 9 AM - 8 PM.

Thank you for your kindness and support.

Sincerely,
Hospital Administration"""
    
    msg.set_content(body)
    msg['Subject'] = f"Urgent Appeal: {missing_blood_type} Blood Needed - Save a Life Today"
    msg['From'] = SENDER_EMAIL
    msg['To'] = recipient_email

    try:
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            print("=== Sending Email ===")
            print(msg.as_string())
            print("=====================")
            server.send_message(msg)
        return True
    except Exception as e:
        print(f"Error sending broadcast: {e}")
        return False
