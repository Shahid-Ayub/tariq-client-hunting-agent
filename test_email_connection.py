"""
Quick test script to verify Gmail SMTP credentials and catalog PDF attachment.
Sends a test email to your own company address (tariqcotech@gmail.com).
"""

from mailer import send_outreach_email, get_email_credentials, find_catalog_pdf

def test_connection():
    creds = get_email_credentials()
    catalog_path = find_catalog_pdf()
    
    print("==================================================================")
    print("        TARIQ & CO. TECH | EMAIL CONNECTION TEST")
    print("==================================================================")
    print(f"Sender Email:     {creds['email']}")
    print(f"Password Set:     {'[YES - Hidden]' if creds['password'] else '[NO]'}")
    print(f"Catalog Attached: {catalog_path.name if catalog_path else 'None found'}")
    print("------------------------------------------------------------------")
    print(f"Sending a self-test email to: {creds['email']}...")

    test_subject = "Test: Tariq & Co. Tech Client Hunting Agent Connection"
    test_body = (
        "Hi Tariq,\n\n"
        "Congratulations! Your Client Hunting AI Agent is successfully connected to your company Gmail.\n\n"
        "This confirms:\n"
        "1. Your Gmail App Password is authenticated.\n"
        "2. The Tariq & Co. Tech Catalog PDF is attached properly.\n"
        "3. Live outreach dispatch is ready to go!\n\n"
        "Best regards,\n"
        "Tariq & Co. Tech Client Hunter Agent\n"
        "Website: https://tariq-co-tech.vercel.app\n"
        "WhatsApp: +92 314 9574681"
    )

    result = send_outreach_email(
        recipient_email=creds["email"],
        subject=test_subject,
        body_text=test_body,
        attach_catalog=True,
        dry_run=False
    )

    print("\nResult:")
    print(f"Status:  {result.get('status')}")
    print(f"Message: {result.get('message')}")
    print("==================================================================")

if __name__ == "__main__":
    test_connection()
