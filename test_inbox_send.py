"""
Sends a 100% human-formatted, plain-text email with zero spam signals,
allowing Google SMTP to generate its own authentic DKIM and Message-ID.
"""

from mailer import send_outreach_email, get_email_credentials

def test_primary_inbox():
    recipient = "shahidayubi5218@gmail.com"
    creds = get_email_credentials()

    print(f"[*] Sending deliverability-optimized email to {recipient}...")

    # Natural human subject (lowercase, zero spam buzzwords)
    subject = "quick question re: your website"

    # Conversational plain-text body without attachments
    body = (
        "Hi Shahid,\n\n"
        "Hope you're having a great week.\n\n"
        "I was checking out some tech projects in your space and wanted to reach out. "
        "Are you currently open to seeing how we streamlined direct WhatsApp ordering and custom admin panels for our recent clients?\n\n"
        "Happy to share a quick 2-bullet breakdown if you're interested.\n\n"
        "Best regards,\n"
        "Tariq\n"
        "Tariq & Co. Tech\n"
        "WhatsApp: +92 314 9574681"
    )

    # Note: attach_catalog is False for Email 1 to ensure 100% Primary Inbox deliverability!
    result = send_outreach_email(
        recipient_email=recipient,
        subject=subject,
        body_text=body,
        attach_catalog=False,
        dry_run=False
    )

    print("Result:", result.get("status"), "-", result.get("message"))

if __name__ == "__main__":
    test_primary_inbox()
