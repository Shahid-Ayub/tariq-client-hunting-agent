"""
Sends a demo email to shahidayubi5218@gmail.com with the Tariq & Co. Tech catalog attached.
"""

from mailer import send_outreach_email, get_email_credentials, find_catalog_pdf

def send_demo():
    recipient = "shahidayubi5218@gmail.com"
    creds = get_email_credentials()
    catalog = find_catalog_pdf()

    print(f"Connecting to SMTP as: {creds['email']}...")
    print(f"Recipient: {recipient}")
    print(f"Attaching Catalog: {catalog.name if catalog else 'Not Found'}")

    subject = "Tariq & Co. Tech — System Capabilities & Company Catalog"
    body = (
        "Hi Shahid,\n\n"
        "This is a live demonstration email sent directly from the Tariq & Co. Tech Client Hunting AI Agent.\n\n"
        "The AI outreach engine has been successfully authenticated with tariqcotech@gmail.com and is configured to:\n"
        "1. Discover high-potential business prospects automatically across target niches and locations.\n"
        "2. Audit prospect websites for modern AI era and workflow automation bottlenecks.\n"
        "3. Generate formatted Excel sheets (.xlsx) and Notion-ready CSV files for HR tracking.\n"
        "4. Dispatch personalized, spam-proof outreach directly to verified business decision-makers.\n\n"
        "Attached is our official Tariq & Co. Tech Company Catalog (PDF), summarizing our core services "
        "(Full-Stack Web Dev, Workflow Automation, UI/UX Design, AI Integration) and proven case studies "
        "(Crispiano Cafe, Yousafzai Agri Foods, VidaAI, and more).\n\n"
        "You can also explore our live portfolio at:\n"
        "https://tariq-co-tech.vercel.app/work\n\n"
        "Best regards,\n"
        "Tariq\n"
        "Tariq & Co. Tech | Engineering the Future\n"
        "Website: https://tariq-co-tech.vercel.app\n"
        "WhatsApp: +92 314 9574681\n"
        "Email: tariqcotech@gmail.com"
    )

    result = send_outreach_email(
        recipient_email=recipient,
        subject=subject,
        body_text=body,
        attach_catalog=True,
        dry_run=False
    )

    print("\nSend Status:", result.get("status"))
    print("Details:", result.get("message"))
    return result

if __name__ == "__main__":
    send_demo()
