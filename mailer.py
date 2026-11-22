"""
Email dispatcher engine for Tariq & Co. Tech.
Supports sending via Gmail SMTP with PDF catalog attachment and deliverability safeguards.
"""

import os
import smtplib
import ssl
import time
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.utils import formatdate, make_msgid
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent

def get_email_credentials():
    # Check .env file or environment variables
    env_file = BASE_DIR / ".env"
    creds = {
        "email": "tariqcotech@gmail.com",
        "password": "",
        "smtp_server": "smtp.gmail.com",
        "smtp_port": 587
    }
    
    if env_file.exists():
        with open(env_file, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, val = line.split("=", 1)
                    key = key.strip()
                    val = val.strip().strip('"').strip("'")
                    if key == "SENDER_EMAIL":
                        creds["email"] = val
                    elif key in ["SENDER_PASSWORD", "GMAIL_APP_PASSWORD"]:
                        creds["password"] = val.replace(" ", "")
                    elif key == "SMTP_SERVER":
                        creds["smtp_server"] = val
                    elif key == "SMTP_PORT":
                        creds["smtp_port"] = int(val)

    # Environment variables override .env
    if os.getenv("SENDER_EMAIL"):
        creds["email"] = os.getenv("SENDER_EMAIL")
    if os.getenv("SENDER_PASSWORD"):
        creds["password"] = os.getenv("SENDER_PASSWORD")

    return creds

def find_catalog_pdf():
    candidates = [
        BASE_DIR / "Tariq_and_Co_Tech_Catalog.pdf",
        BASE_DIR / "catalog.pdf",
        BASE_DIR / "Catalog.pdf",
        BASE_DIR / "tariq_and_co_tech_catalog.pdf"
    ]
    for c in candidates:
        if c.exists():
            return c
    return None

def send_outreach_email(recipient_email: str, subject: str, body_text: str, attach_catalog: bool = True, dry_run: bool = False):
    creds = get_email_credentials()
    sender_email = creds["email"]
    sender_password = creds["password"]
    
    if dry_run or not sender_password:
        return {
            "status": "dry_run",
            "message": "Simulated send (Dry Run). To send live emails, set SENDER_PASSWORD in .env.",
            "recipient": recipient_email,
            "subject": subject,
            "catalog_attached": bool(find_catalog_pdf())
        }

    # Construct email message
    catalog_path = find_catalog_pdf() if attach_catalog else None

    if catalog_path:
        # Multipart when sending attachment
        msg = MIMEMultipart()
        msg["From"] = f"Tariq & Co. Tech <{sender_email}>"
        msg["To"] = recipient_email
        msg["Reply-To"] = sender_email
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject
        msg.attach(MIMEText(body_text, "plain", "utf-8"))
        try:
            with open(catalog_path, "rb") as f:
                attach = MIMEApplication(f.read(), _subtype="pdf")
                attach.add_header('Content-Disposition', 'attachment', filename=catalog_path.name)
                msg.attach(attach)
        except Exception as e:
            print(f"[Warning] Could not attach PDF: {e}")
    else:
        # Clean plain text format (Highest deliverability, 100% Primary Inbox)
        msg = MIMEText(body_text, "plain", "utf-8")
        msg["From"] = f"Tariq & Co. Tech <{sender_email}>"
        msg["To"] = recipient_email
        msg["Reply-To"] = sender_email
        msg["Date"] = formatdate(localtime=True)
        msg["Subject"] = subject

    # Send over SMTP (tries Port 465 SSL first for maximum reliability, falls back to 587 STARTTLS)
    context = ssl.create_default_context()
    last_err = None

    # Strategy 1: SMTP_SSL over Port 465
    smtp_host = creds.get("smtp_server", "smtp.gmail.com")
    try:
        with smtplib.SMTP_SSL(smtp_host, 465, timeout=15, context=context) as server:
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [recipient_email], msg.as_string())
        return {
            "status": "sent",
            "message": f"Successfully sent to {recipient_email} with catalog attached (via SSL/465).",
            "recipient": recipient_email
        }
    except Exception as e:
        last_err = e

    # Strategy 2: SMTP over Port 587 with STARTTLS
    try:
        with smtplib.SMTP(smtp_host, 587, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.ehlo()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, [recipient_email], msg.as_string())
        return {
            "status": "sent",
            "message": f"Successfully sent to {recipient_email} with catalog attached (via TLS/587).",
            "recipient": recipient_email
        }
    except Exception as e:
        last_err = e

    return {
        "status": "error",
        "message": f"SMTP Error: {str(last_err)}",
        "recipient": recipient_email
    }

def send_batch_outreach(email_tasks: list, delay_seconds: int = 4, dry_run: bool = False):
    """
    Sends a batch of emails with safe delay between sends to protect sender reputation.
    """
    results = []
    print(f"\n[*] Preparing to dispatch {len(email_tasks)} emails (Dry-run: {dry_run})...")
    
    for idx, task in enumerate(email_tasks, 1):
        recipients = task.get("recipients", [])
        if not recipients:
            print(f"[{idx}/{len(email_tasks)}] Skipping {task['company_name']} - No email address found.")
            results.append({"company": task["company_name"], "status": "skipped_no_email"})
            continue

        target_email = recipients[0]
        print(f"[{idx}/{len(email_tasks)}] Sending to {task['company_name']} ({target_email})...")
        
        res = send_outreach_email(
            recipient_email=target_email,
            subject=task["primary_subject"],
            body_text=task["email_body"],
            attach_catalog=task.get("attach_catalog", False),
            dry_run=dry_run
        )
        results.append(res)
        print(f"    -> Result: {res['status']} ({res['message']})")

        if not dry_run and idx < len(email_tasks):
            time.sleep(delay_seconds)

    return results
