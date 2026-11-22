"""
Diagnostic script to test deliverability with proper RFC headers (Date, Message-ID).
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate, make_msgid
from mailer import get_email_credentials

def test_clean_send():
    creds = get_email_credentials()
    recipient = "shahidayubi5218@gmail.com"

    msg = MIMEMultipart()
    msg["From"] = f"Tariq & Co. Tech <{creds['email']}>"
    msg["To"] = recipient
    msg["Reply-To"] = creds["email"]
    msg["Date"] = formatdate(localtime=True)
    msg["Message-ID"] = make_msgid(domain="gmail.com")
    msg["Subject"] = "Quick test from Tariq"

    body = (
        "Hi Shahid,\n\n"
        "Just testing the email delivery directly from our system with updated headers.\n\n"
        "Let me know if this arrives in your primary inbox!\n\n"
        "Best regards,\n"
        "Tariq\n"
        "Tariq & Co. Tech\n"
        "WhatsApp: +92 314 9574681"
    )
    msg.attach(MIMEText(body, "plain", "utf-8"))

    context = ssl.create_default_context()
    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=15, context=context) as server:
        server.login(creds["email"], creds["password"])
        server.sendmail(creds["email"], [recipient], msg.as_string())

    print("[SUCCESS] Sent clean RFC-compliant email to:", recipient)

if __name__ == "__main__":
    test_clean_send()
