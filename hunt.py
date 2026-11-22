#!/usr/bin/env python3
"""
===================================================================
TARIQ & CO. TECH - AUTONOMOUS CLIENT HUNTING & MAILING AI AGENT
===================================================================
1. Finds target businesses automatically (no manual URL copying)
2. Audits their website for AI era & automation gaps
3. Finds emails, phones, and contacts
4. Generates tailored, anti-spam outreach
5. Attaches the Tariq & Co. Tech catalog and sends directly via company email
"""

import argparse
import json
import os
import sys
from datetime import datetime
from pathlib import Path

from config import load_company_profile
from discovery import find_prospects
from scanner import audit_website
from matcher import match_opportunity
from generator import generate_cold_email, generate_ai_enhanced_angles
from mailer import send_batch_outreach, get_email_credentials, find_catalog_pdf
from exporter import export_prospects_to_excel
from crm import (
    sync_batch_results_to_crm,
    mark_as_contacted,
    mark_as_replied,
    process_due_follow_ups,
    export_team_crm_excel,
    get_crm_stats,
    get_all_prospects
)

class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    DIM = '\033[2m'

def print_banner():
    banner = f"""
{Colors.CYAN}{Colors.BOLD}======================================================================
       TARIQ & CO. TECH | AUTONOMOUS CLIENT HUNTING AGENT
  Automated Lead Discovery · AI-Era Website Audit · Cold Outreach Engine
======================================================================{Colors.ENDC}
"""
    print(banner)

def format_terminal_box(title, content, color=Colors.CYAN):
    border = "=" * 68
    print(f"\n{color}{Colors.BOLD}[ {title.upper()} ]{Colors.ENDC}")
    print(f"{Colors.DIM}{border}{Colors.ENDC}")
    print(content)
    print(f"{Colors.DIM}{border}{Colors.ENDC}")

def save_batch_report(batch_results: list, niche: str, location: str, output_dir="outreach_drafts"):
    out_path = Path(output_dir)
    out_path.mkdir(parents=True, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    clean_niche = niche.replace(" ", "_")
    clean_loc = (location or "global").replace(" ", "_")
    filename = out_path / f"batch_{clean_niche}_{clean_loc}_{timestamp}.md"
    
    catalog_path = find_catalog_pdf()
    catalog_name = catalog_path.name if catalog_path else "None (Add catalog.pdf)"

    md = f"""# Autonomous Client Outreach Batch: {niche.title()} ({location or 'Global'})
**Agent:** Tariq & Co. Tech Client Hunting AI  
**Generated Date:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}  
**Total Prospects Audited:** {len(batch_results)}  
**Attached Catalog:** `{catalog_name}`  

---

| # | Company Name | Website | Email | Phone | Detected AI / Automation Gap | Matched Proof |
|---|--------------|---------|-------|-------|------------------------------|---------------|
"""
    for idx, item in enumerate(batch_results, 1):
        target = item["audit"]
        match = item["match"]
        outreach = item["email"]
        emails_str = ", ".join(target.get("emails", [])) or "None found"
        phones_str = ", ".join(target.get("phones", [])) or "None found"
        md += f"| {idx} | **{outreach['company_name']}** | {target.get('url')} | `{emails_str}` | `{phones_str}` | {match.get('primary_issue')} | {outreach.get('matched_case_study')} |\n"

    md += "\n---\n\n## Generated Cold Outreach Emails\n\n"
    for idx, item in enumerate(batch_results, 1):
        outreach = item["email"]
        target = item["audit"]
        md += f"### Prospect {idx}: {outreach['company_name']} ({target.get('url')})\n"
        md += f"- **Target Email:** {', '.join(target.get('emails', [])) or 'Check website contact form'}\n"
        md += f"- **Subject:** `{outreach['primary_subject']}`\n\n"
        md += f"```text\n{outreach['email_body']}\n```\n\n"
        md += f"**WhatsApp / DM Alternative:**\n"
        md += f"> {outreach['whatsapp_script']}\n\n"
        md += "---\n\n"

    with open(filename, "w", encoding="utf-8") as f:
        f.write(md)

    return filename

def run_autonomous_hunt(niche: str, location: str = "", count: int = 10, auto_send: bool = False, dry_run: bool = True):
    print(f"\n{Colors.BOLD}{Colors.BLUE}[Step 1/4] Hunting for {count} '{niche}' prospects in {location or 'Global Market'}...{Colors.ENDC}")
    
    discovered_leads = find_prospects(niche=niche, location=location, count=count)
    print(f"{Colors.GREEN}[OK] Discovered {len(discovered_leads)} business targets without manual searching!{Colors.ENDC}\n")

    batch_results = []
    email_tasks = []

    print(f"{Colors.BOLD}{Colors.BLUE}[Step 2/4] Auditing websites for AI era & automation gaps...{Colors.ENDC}")
    for idx, lead in enumerate(discovered_leads, 1):
        url = lead["url"]
        print(f"  [{idx}/{len(discovered_leads)}] Auditing: {lead['name']} ({url})...")
        
        audit_data = audit_website(url, mock_mode=False, custom_niche=niche)
        if audit_data.get("status") == "error_fallback":
            audit_data = audit_data["fallback_audit"]

        # Match Tariq & Co. Tech services and case study
        match_data = match_opportunity(audit_data)
        
        # Write personalized email with catalog reference
        email_data = generate_cold_email(audit_data, match_data)

        batch_results.append({
            "lead": lead,
            "audit": audit_data,
            "match": match_data,
            "email": email_data
        })

        if audit_data.get("emails"):
            email_tasks.append({
                "company_name": email_data["company_name"],
                "recipients": audit_data["emails"],
                "primary_subject": email_data["primary_subject"],
                "email_body": email_data["email_body"]
            })

    # Save summary markdown report, Excel/Notion sheets, and sync to persistent SQLite CRM
    saved_md = save_batch_report(batch_results, niche, location)
    excel_files = export_prospects_to_excel(batch_results, niche, location)
    crm_ids = sync_batch_results_to_crm(batch_results, niche, location)
    team_crm = export_team_crm_excel()

    # Print Summary Table
    print(f"\n{Colors.BOLD}{Colors.GREEN}[Step 3/4] Prospect Intelligence Summary Table:{Colors.ENDC}")
    border = "=" * 80
    print(f"{Colors.DIM}{border}{Colors.ENDC}")
    print(f"{'#':<3} | {'Company':<20} | {'Email':<25} | {'Detected Problem / AI Opportunity':<28}")
    print(f"{Colors.DIM}{border}{Colors.ENDC}")
    for idx, res in enumerate(batch_results, 1):
        comp = res["email"]["company_name"][:18]
        em = (res["audit"].get("emails") or ["None"])[0][:23]
        prob = res["match"]["primary_issue"][:26] + "..."
        print(f"{idx:<3} | {comp:<20} | {em:<25} | {prob:<28}")
    print(f"{Colors.DIM}{border}{Colors.ENDC}")
    print(f"{Colors.GREEN}[OK] Outreach drafts saved to:{Colors.ENDC} {saved_md}")
    print(f"{Colors.GREEN}[OK] Synced {len(crm_ids)} leads to SQLite CRM (crm.db){Colors.ENDC}")
    if team_crm.get("xlsx"):
        print(f"{Colors.GREEN}[OK] Master Team CRM Excel Workbook updated:{Colors.ENDC} {team_crm['latest_xlsx']}")
    print(f"{Colors.GREEN}[OK] Notion Database CSV updated:{Colors.ENDC} {team_crm['csv']}\n")

    # Sample preview
    sample = batch_results[0]["email"]
    format_terminal_box("Sample Generated Email (With Catalog Attachment)", f"To: {(batch_results[0]['audit'].get('emails') or ['client@example.com'])[0]}\nSubject: {sample['primary_subject']}\n\n{sample['email_body']}", Colors.CYAN)

    # Step 4: Dispatch
    creds = get_email_credentials()
    catalog_path = find_catalog_pdf()
    catalog_display = catalog_path.name if catalog_path else "NOT FOUND (Make sure Tariq_and_Co_Tech_Catalog.pdf is in workspace)"

    print(f"\n{Colors.BOLD}{Colors.CYAN}[Step 4/4] Email Dispatch Center{Colors.ENDC}")
    print(f"Company Sender Email: {Colors.BOLD}{creds['email']}{Colors.ENDC}")
    print(f"Attached Catalog:     {Colors.BOLD}{catalog_display}{Colors.ENDC}")
    print(f"Ready Recipients:     {Colors.BOLD}{len(email_tasks)} prospects have valid email addresses{Colors.ENDC}")

    attach_pdf = False
    if not auto_send:
        print(f"\nOptions:")
        print(f"  [1] Send all {len(email_tasks)} emails (Plain-Text — 100% Primary Inbox Delivery)")
        print(f"  [2] Send all {len(email_tasks)} emails with PDF Catalog attached")
        print(f"  [3] Run dry-run simulation (verify without sending)")
        print(f"  [4] Skip sending (keep saved in drafts folder)")
        choice = input("\nEnter choice [1/2/3/4] (default 1): ").strip()
        if choice in ["1", ""]:
            dry_run = False
            attach_pdf = False
        elif choice == "2":
            dry_run = False
            attach_pdf = True
        elif choice == "4":
            print(f"{Colors.WARNING}Sending skipped. Review your drafts anytime in {saved_md}.{Colors.ENDC}")
            return
        else:
            dry_run = True

    # Dispatch emails
    for task in email_tasks:
        task["attach_catalog"] = attach_pdf

    results = send_batch_outreach(email_tasks, delay_seconds=4, dry_run=dry_run)

    # If sent live, update the CRM stages to 'Contacted' and schedule 3-day follow-ups
    if not dry_run:
        contacted_count = 0
        for task, res in zip(email_tasks, results):
            if res.get("status") == "sent":
                recipient = (task.get("recipients") or [""])[0]
                if recipient:
                    mark_as_contacted(recipient, notes=f"Initial outreach sent for {niche}", follow_up_days=3)
                    contacted_count += 1
        print(f"\n{Colors.GREEN}[OK] Updated {contacted_count} leads to 'Contacted' in CRM (Follow-up scheduled in 3 days).{Colors.ENDC}")
        export_team_crm_excel()

def show_crm_terminal_dashboard():
    stats = get_crm_stats()
    print(f"\n{Colors.BOLD}{Colors.CYAN}======================================================================{Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}          TARIQ & CO. TECH | PIPELINE & CRM DASHBOARD                {Colors.ENDC}")
    print(f"{Colors.BOLD}{Colors.CYAN}======================================================================{Colors.ENDC}")
    for k, v in stats.items():
        color = Colors.GREEN if k in ["Replied", "Response Rate"] else (Colors.WARNING if "Due" in k else Colors.ENDC)
        print(f"  {k:<22}: {color}{v}{Colors.ENDC}")
    print(f"{Colors.DIM}{'-' * 70}{Colors.ENDC}")
    
    prospects = get_all_prospects()
    print(f"{'#':<3} | {'Company':<18} | {'Email':<24} | {'Stage':<13} | {'Follow-up Due'}")
    print(f"{Colors.DIM}{'-' * 70}{Colors.ENDC}")
    for idx, p in enumerate(prospects[:15], 1):
        st = p.get('stage', 'Discovered')
        st_color = Colors.GREEN if st == 'Replied' else (Colors.BLUE if st == 'Contacted' else Colors.DIM)
        cname = (p.get('company_name') or 'Prospect')[:17]
        em = (p.get('primary_email') or 'No email')[:23]
        due = p.get('follow_up_due_at') or '—'
        print(f"{idx:<3} | {cname:<18} | {em:<24} | {st_color}{st:<13}{Colors.ENDC} | {due}")
    
    excel_info = export_team_crm_excel()
    print(f"\n{Colors.GREEN}[OK] Master Team CRM Excel Workbook ready:{Colors.ENDC} {excel_info['latest_xlsx']}")
    print(f"{Colors.GREEN}[OK] Notion CRM CSV Database ready:{Colors.ENDC} {excel_info['csv']}\n")

def main():
    print_banner()
    parser = argparse.ArgumentParser(description="Tariq & Co. Tech Autonomous Lead Hunter & CRM Engine")
    parser.add_argument("--auto", action="store_true", help="Run autonomous prospect discovery mode")
    parser.add_argument("--niche", type=str, default="", help="Business niche (e.g. 'cafes', 'b2b exporters', 'private clinics', 'academies')")
    parser.add_argument("--location", type=str, default="", help="Target city or country (e.g. 'London', 'Dubai', 'Pakistan')")
    parser.add_argument("--count", type=int, default=10, help="Number of prospects to find (default: 10)")
    parser.add_argument("--send", action="store_true", help="Send emails live (requires SENDER_PASSWORD in .env)")
    parser.add_argument("--url", type=str, default="", help="Manual single website audit URL")
    parser.add_argument("--crm", action="store_true", help="Display CRM pipeline metrics and prospect status")
    parser.add_argument("--follow-up", action="store_true", help="Run automated 3-day follow-up dispatcher")
    parser.add_argument("--export-crm", action="store_true", help="Generate and export the team CRM Excel workbook")
    parser.add_argument("--replied", type=str, default="", help="Mark prospect email as 'Replied'")

    args = parser.parse_args()

    # CRM Dashboard Mode
    if args.crm:
        show_crm_terminal_dashboard()
        return

    # Export CRM Sheets Mode
    if args.export_crm:
        excel_info = export_team_crm_excel()
        print(f"{Colors.GREEN}[OK] Generated Master Team CRM Workbook:{Colors.ENDC} {excel_info['latest_xlsx']}")
        print(f"{Colors.GREEN}[OK] Generated Notion CSV Database:{Colors.ENDC} {excel_info['csv']}")
        return

    # Mark as replied mode
    if args.replied:
        mark_as_replied(args.replied, reply_notes="Marked via CLI command")
        print(f"{Colors.GREEN}[OK] Marked {args.replied} as 'Replied' in CRM!{Colors.ENDC}")
        export_team_crm_excel()
        return

    # Process due follow-ups mode
    if args.follow_up:
        print(f"{Colors.BOLD}{Colors.BLUE}[*] Running 3-Day Follow-Up Pipeline...{Colors.ENDC}")
        dry_run = not args.send
        process_due_follow_ups(auto_send=args.send, dry_run=dry_run)
        export_team_crm_excel()
        return

    # If single URL provided, run single audit mode
    if args.url:
        from scanner import audit_website
        from matcher import match_opportunity
        from generator import generate_cold_email
        audit_data = audit_website(args.url, mock_mode=False, custom_niche=args.niche)
        match_data = match_opportunity(audit_data)
        email_data = generate_cold_email(audit_data, match_data)
        format_terminal_box("Primary Inbox Cold Email", f"Subject: {email_data['primary_subject']}\n\n{email_data['email_body']}", Colors.CYAN)
        return

    # Autonomous Mode (Either triggered by --auto or interactive input)
    niche = args.niche
    location = args.location
    count = args.count

    if not niche and not args.auto:
        print(f"{Colors.WARNING}Welcome Tariq! Choose an action for Tariq & Co. Tech:{Colors.ENDC}")
        print("  [1] Hunt New Prospects & Generate Outreach Emails")
        print("  [2] View CRM Pipeline & Follow-Up Schedule")
        print("  [3] Process Due 3-Day Follow-Ups")
        print("  [4] Export Master Team CRM Excel Workbook")
        choice = input("\nEnter choice [1/2/3/4] (default 1): ").strip()

        if choice == "2":
            show_crm_terminal_dashboard()
            return
        elif choice == "3":
            dry_run = not args.send
            process_due_follow_ups(auto_send=args.send, dry_run=dry_run)
            export_team_crm_excel()
            return
        elif choice == "4":
            excel_info = export_team_crm_excel()
            print(f"\n{Colors.GREEN}[OK] Master Team CRM Excel Workbook ready:{Colors.ENDC} {excel_info['latest_xlsx']}")
            return

        # Default: Option 1
        niche = input("\nWhat kind of businesses are you targeting? (e.g. cafes, b2b exporters, schools, clinics): ").strip()
        if not niche:
            niche = "cafes"
        location = input("What city or country? (e.g. London, Dubai, Pakistan, or press Enter for global): ").strip()
        count_input = input("How many prospects do you want to find and email? [Default: 10]: ").strip()
        count = int(count_input) if count_input.isdigit() else 10

    dry_run = not args.send
    run_autonomous_hunt(niche=niche, location=location, count=count, auto_send=args.send, dry_run=dry_run)

if __name__ == "__main__":
    main()
