"""
Sends a professional services introduction email to awaiskhanmrd5@gmail.com.
Delivered in clean plain-text for 100% Primary Inbox placement.
"""

from mailer import send_outreach_email, get_email_credentials

def send_to_awais():
    recipient = "awaiskhanmrd5@gmail.com"
    creds = get_email_credentials()

    print(f"[*] Preparing to send professional services introduction to {recipient}...")

    subject = "Quick introduction — Tariq & Co. Tech"
    
    body = (
        "Hi Awais,\n\n"
        "Hope you're doing well.\n\n"
        "I'm reaching out from Tariq & Co. Tech (https://tariq-co-tech.vercel.app). "
        "We are a software and technology partner helping growing businesses, startups, "
        "and founders build practical digital solutions and automate everyday operations.\n\n"
        "Here is a quick overview of what we deliver:\n\n"
        "1. Full-Stack Web Development\n"
        "   Custom web applications, responsive business websites, client portals, and admin dashboards.\n\n"
        "2. Workflow Automation\n"
        "   Connecting disconnected tools (Google Sheets, WhatsApp, CRM, forms) to eliminate hours of manual copying and repetitive work.\n\n"
        "3. UI/UX Design & Usability Reviews\n"
        "   Transforming crowded or confusing interfaces into clean, structured experiences that turn visitors into paying clients.\n\n"
        "4. AI Integration & Smart Tools\n"
        "   Adding intelligent document processing, natural-language database search, and background AI worker queues without app lag.\n\n"
        "5. Technical Scoping & Consulting\n"
        "   Helping non-technical business owners evaluate ideas with clear written specifications, timelines, and milestones before code begins.\n\n"
        "You can explore our recent builds and case studies (including Crispiano Cafe, Yousafzai Agri Foods, and VidaAI) at:\n"
        "https://tariq-co-tech.vercel.app/work\n\n"
        "If your team has any active or upcoming web, design, or automation projects, I would be glad to share ideas or hop on a quick 10-minute chat.\n\n"
        "Best regards,\n"
        "Tariq\n"
        "Tariq & Co. Tech | Engineering the Future\n"
        "WhatsApp: +92 314 9574681\n"
        "Email: tariqcotech@gmail.com"
    )

    result = send_outreach_email(
        recipient_email=recipient,
        subject=subject,
        body_text=body,
        attach_catalog=False,  # Plain text ensures 100% Primary Inbox delivery
        dry_run=False
    )

    print("\nResult:", result.get("status"))
    print("Message:", result.get("message"))
    return result

if __name__ == "__main__":
    send_to_awais()
