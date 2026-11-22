"""
=============================================================================
TARIQ & CO. TECH — CRM PIPELINE & AUTOMATED FOLLOW-UP TRACKER
=============================================================================
Manages the prospect lifecycle:
Discovered -> Contacted -> Followed Up -> Replied -> Meeting Booked -> Closed

Features:
1. SQLite persistent database (crm.db) with activity audit log
2. Automated 3-day and 7-day follow-up scheduler and due-date calculator
3. Multi-sheet Executive Excel Workbook generation for team sharing
4. Integrates seamlessly with hunt.py and mailer.py
"""

import os
import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

try:
    import openpyxl
    from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    from openpyxl.utils import get_column_letter
    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False

BASE_DIR = Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "crm.db"

STAGES = [
    "Discovered",
    "Contacted",
    "Followed Up",
    "Replied",
    "Meeting Booked",
    "Closed",
    "Unresponsive"
]

def get_connection(db_path: Path = DB_PATH) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def init_db(db_path: Path = DB_PATH):
    """Initializes the SQLite schema with indexes and activity log."""
    conn = get_connection(db_path)
    cur = conn.cursor()

    cur.execute("""
    CREATE TABLE IF NOT EXISTS prospects (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        company_name TEXT NOT NULL,
        domain TEXT UNIQUE,
        website_url TEXT,
        primary_email TEXT,
        all_emails TEXT,
        phone TEXT,
        niche TEXT,
        location TEXT,
        detected_gap TEXT,
        matched_case_study TEXT,
        initial_subject TEXT,
        initial_body TEXT,
        follow_up_subject TEXT,
        follow_up_body TEXT,
        whatsapp_script TEXT,
        stage TEXT DEFAULT 'Discovered',
        discovered_at TEXT,
        contacted_at TEXT,
        follow_up_due_at TEXT,
        followed_up_at TEXT,
        replied_at TEXT,
        last_notes TEXT
    )
    """)

    cur.execute("""
    CREATE TABLE IF NOT EXISTS activity_log (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        prospect_id INTEGER,
        company_name TEXT,
        action TEXT,
        details TEXT,
        created_at TEXT,
        FOREIGN KEY(prospect_id) REFERENCES prospects(id)
    )
    """)

    cur.execute("CREATE INDEX IF NOT EXISTS idx_prospects_domain ON prospects(domain)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prospects_stage ON prospects(stage)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prospects_email ON prospects(primary_email)")
    cur.execute("CREATE INDEX IF NOT EXISTS idx_prospects_due ON prospects(follow_up_due_at)")

    conn.commit()
    conn.close()

def extract_domain(url: str) -> str:
    from urllib.parse import urlparse
    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url
    return urlparse(url).netloc.replace("www.", "").lower()

def upsert_prospect_from_batch_item(item: dict, niche: str, location: str) -> int:
    """Inserts or updates a prospect discovered during a hunt run."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    target = item.get("audit", {})
    match = item.get("match", {})
    email_data = item.get("email", {})
    lead = item.get("lead", {})

    url = target.get("url") or lead.get("url", "")
    domain = extract_domain(url) if url else f"lead_{datetime.now().timestamp()}"
    company_name = email_data.get("company_name") or lead.get("name", domain.capitalize())

    emails = target.get("emails", [])
    primary_email = emails[0] if emails else ""
    all_emails = ", ".join(emails) if emails else ""

    phones = target.get("phones", [])
    phone = phones[0] if phones else ""

    detected_gap = match.get("primary_issue", "Mobile inquiry & workflow automation gap")
    matched_case = email_data.get("matched_case_study", "Crispiano Café / Yousafzai Agri Foods")
    initial_sub = email_data.get("primary_subject", f"quick question re: {company_name}")
    initial_body = email_data.get("email_body", "")
    follow_up_sub = f"Re: {initial_sub}"
    follow_up_body = email_data.get("follow_up_body", "")
    whatsapp_script = email_data.get("whatsapp_script", "")

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Check if domain exists
    cur.execute("SELECT id, stage FROM prospects WHERE domain = ?", (domain,))
    row = cur.fetchone()

    if row:
        prospect_id = row["id"]
        # Update details without overwriting progress if already contacted or replied
        cur.execute("""
            UPDATE prospects SET
                company_name = COALESCE(?, company_name),
                website_url = COALESCE(?, website_url),
                primary_email = CASE WHEN primary_email IS NULL OR primary_email = '' THEN ? ELSE primary_email END,
                all_emails = CASE WHEN all_emails IS NULL OR all_emails = '' THEN ? ELSE all_emails END,
                phone = CASE WHEN phone IS NULL OR phone = '' THEN ? ELSE phone END,
                niche = COALESCE(?, niche),
                location = COALESCE(?, location),
                detected_gap = COALESCE(?, detected_gap),
                matched_case_study = COALESCE(?, matched_case_study),
                initial_subject = COALESCE(?, initial_subject),
                initial_body = COALESCE(?, initial_body),
                follow_up_subject = COALESCE(?, follow_up_subject),
                follow_up_body = COALESCE(?, follow_up_body),
                whatsapp_script = COALESCE(?, whatsapp_script)
            WHERE id = ?
        """, (company_name, url, primary_email, all_emails, phone, niche, location,
              detected_gap, matched_case, initial_sub, initial_body, follow_up_sub,
              follow_up_body, whatsapp_script, prospect_id))
    else:
        cur.execute("""
            INSERT INTO prospects (
                company_name, domain, website_url, primary_email, all_emails,
                phone, niche, location, detected_gap, matched_case_study,
                initial_subject, initial_body, follow_up_subject, follow_up_body,
                whatsapp_script, stage, discovered_at, last_notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Discovered', ?, 'Added via Autonomous Hunt')
        """, (company_name, domain, url, primary_email, all_emails, phone, niche, location,
              detected_gap, matched_case, initial_sub, initial_body, follow_up_sub,
              follow_up_body, whatsapp_script, now_iso))
        prospect_id = cur.lastrowid

        cur.execute("""
            INSERT INTO activity_log (prospect_id, company_name, action, details, created_at)
            VALUES (?, ?, 'DISCOVERED', 'Prospect identified and audited', ?)
        """, (prospect_id, company_name, now_iso))

    conn.commit()
    conn.close()
    return prospect_id

def sync_batch_results_to_crm(batch_results: list, niche: str, location: str) -> List[int]:
    """Saves an entire batch of hunted leads into the CRM."""
    ids = []
    for item in batch_results:
        pid = upsert_prospect_from_batch_item(item, niche, location)
        ids.append(pid)
    return ids

def mark_as_contacted(email_or_id, notes: str = "Initial cold outreach email sent", follow_up_days: int = 3):
    """Moves a prospect to 'Contacted' stage and schedules a 3-day follow-up."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    now = datetime.now()
    now_iso = now.strftime("%Y-%m-%d %H:%M:%S")
    due_iso = (now + timedelta(days=follow_up_days)).strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(email_or_id, int) or str(email_or_id).isdigit():
        clause = "id = ?"
        param = int(email_or_id)
    else:
        clause = "primary_email = ?"
        param = str(email_or_id).strip()

    cur.execute(f"SELECT id, company_name FROM prospects WHERE {clause}", (param,))
    row = cur.fetchone()

    if row:
        pid = row["id"]
        cname = row["company_name"]
        cur.execute("""
            UPDATE prospects SET
                stage = 'Contacted',
                contacted_at = ?,
                follow_up_due_at = ?,
                last_notes = ?
            WHERE id = ?
        """, (now_iso, due_iso, notes, pid))

        cur.execute("""
            INSERT INTO activity_log (prospect_id, company_name, action, details, created_at)
            VALUES (?, ?, 'CONTACTED', ?, ?)
        """, (pid, cname, f"{notes} (Follow-up due: {due_iso})", now_iso))

    conn.commit()
    conn.close()

def mark_as_followed_up(email_or_id, notes: str = "Automated 3-day follow-up email dispatched"):
    """Moves a prospect to 'Followed Up' stage."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(email_or_id, int) or str(email_or_id).isdigit():
        clause = "id = ?"
        param = int(email_or_id)
    else:
        clause = "primary_email = ?"
        param = str(email_or_id).strip()

    cur.execute(f"SELECT id, company_name FROM prospects WHERE {clause}", (param,))
    row = cur.fetchone()

    if row:
        pid = row["id"]
        cname = row["company_name"]
        cur.execute("""
            UPDATE prospects SET
                stage = 'Followed Up',
                followed_up_at = ?,
                last_notes = ?
            WHERE id = ?
        """, (now_iso, notes, pid))

        cur.execute("""
            INSERT INTO activity_log (prospect_id, company_name, action, details, created_at)
            VALUES (?, ?, 'FOLLOWED_UP', ?, ?)
        """, (pid, cname, notes, now_iso))

    conn.commit()
    conn.close()

def mark_as_replied(email_or_id, reply_notes: str = "Client replied to outreach"):
    """Moves a prospect to 'Replied' stage."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    if isinstance(email_or_id, int) or str(email_or_id).isdigit():
        clause = "id = ?"
        param = int(email_or_id)
    else:
        clause = "primary_email = ?"
        param = str(email_or_id).strip()

    cur.execute(f"SELECT id, company_name FROM prospects WHERE {clause}", (param,))
    row = cur.fetchone()

    if row:
        pid = row["id"]
        cname = row["company_name"]
        cur.execute("""
            UPDATE prospects SET
                stage = 'Replied',
                replied_at = ?,
                last_notes = ?
            WHERE id = ?
        """, (now_iso, reply_notes, pid))

        cur.execute("""
            INSERT INTO activity_log (prospect_id, company_name, action, details, created_at)
            VALUES (?, ?, 'REPLIED', ?, ?)
        """, (pid, cname, reply_notes, now_iso))

    conn.commit()
    conn.close()

def get_due_follow_ups() -> List[dict]:
    """Retrieves all contacted prospects whose follow-up deadline has passed or is due today."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cur.execute("""
        SELECT * FROM prospects
        WHERE stage = 'Contacted'
          AND primary_email IS NOT NULL AND primary_email != ''
          AND (follow_up_due_at <= ? OR follow_up_due_at IS NULL)
        ORDER BY follow_up_due_at ASC
    """, (now_iso,))

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

def get_crm_stats() -> dict:
    """Calculates live KPI metrics across the pipeline."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    stats = {
        "Total Prospects": 0,
        "Discovered": 0,
        "Contacted": 0,
        "Followed Up": 0,
        "Replied": 0,
        "Meeting Booked": 0,
        "Follow-Ups Due Now": 0,
        "Response Rate": "0.0%"
    }

    cur.execute("SELECT COUNT(*) as cnt FROM prospects")
    stats["Total Prospects"] = cur.fetchone()["cnt"]

    for stage in ["Discovered", "Contacted", "Followed Up", "Replied", "Meeting Booked", "Closed", "Unresponsive"]:
        cur.execute("SELECT COUNT(*) as cnt FROM prospects WHERE stage = ?", (stage,))
        stats[stage] = cur.fetchone()["cnt"]

    now_iso = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cur.execute("""
        SELECT COUNT(*) as cnt FROM prospects
        WHERE stage = 'Contacted' AND follow_up_due_at <= ?
    """, (now_iso,))
    stats["Follow-Ups Due Now"] = cur.fetchone()["cnt"]

    total_contacted = stats["Contacted"] + stats["Followed Up"] + stats["Replied"] + stats["Meeting Booked"]
    if total_contacted > 0:
        rate = ((stats["Replied"] + stats["Meeting Booked"]) / total_contacted) * 100
        stats["Response Rate"] = f"{rate:.1f}%"

    conn.close()
    return stats

def get_all_prospects(stage_filter: Optional[str] = None) -> List[dict]:
    """Retrieves all prospects from SQLite, optionally filtered by stage."""
    init_db()
    conn = get_connection()
    cur = conn.cursor()

    if stage_filter:
        cur.execute("SELECT * FROM prospects WHERE stage = ? ORDER BY id DESC", (stage_filter,))
    else:
        cur.execute("SELECT * FROM prospects ORDER BY id DESC")

    rows = [dict(r) for r in cur.fetchall()]
    conn.close()
    return rows

# =============================================================================
# MULTI-TAB TEAM EXCEL WORKBOOK GENERATOR
# =============================================================================

def export_team_crm_excel(output_dir: str = "prospect_sheets") -> Dict[str, str]:
    """
    Generates an executive-ready, multi-tab Excel workbook formatted for Tariq & Co. Tech team.
    Tab 1: Executive KPI Dashboard & Summary
    Tab 2: Prospect CRM Pipeline & Follow-Up Schedule
    Tab 3: Email & WhatsApp Outreach Templates
    """
    init_db()
    out_path = BASE_DIR / output_dir
    out_path.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    excel_filename = out_path / f"Tariq_and_Co_Tech_Team_CRM_{date_str}.xlsx"
    latest_filename = out_path / "Tariq_and_Co_Tech_Team_CRM_Latest.xlsx"
    csv_filename = out_path / f"crm_notion_export_{timestamp}.csv"

    prospects = get_all_prospects()
    stats = get_crm_stats()

    # 1. Export CSV for Notion Database Import
    csv_headers = [
        "ID", "Company Name", "Website", "Primary Email", "Phone",
        "Niche", "Location", "Stage", "Discovered Date", "Initial Contact Date",
        "Follow-up Due Date", "Detected Gap", "Matched Case Study", "Last Notes"
    ]
    import csv
    with open(csv_filename, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(csv_headers)
        for p in prospects:
            writer.writerow([
                p.get("id"),
                p.get("company_name"),
                p.get("website_url"),
                p.get("primary_email"),
                p.get("phone"),
                p.get("niche"),
                p.get("location"),
                p.get("stage"),
                p.get("discovered_at"),
                p.get("contacted_at"),
                p.get("follow_up_due_at"),
                p.get("detected_gap"),
                p.get("matched_case_study"),
                p.get("last_notes")
            ])

    # 2. Export Styled Excel Workbook
    if not OPENPYXL_AVAILABLE:
        return {"xlsx": "", "csv": str(csv_filename)}

    wb = openpyxl.Workbook()

    # Color Palette: Tariq & Co. Tech Corporate (Deep Navy, Gold Accent, Clean Slate)
    NAVY_HEADER = PatternFill(start_color="0F172A", end_color="0F172A", fill_type="solid")       # Slate 900
    GOLD_ACCENT = PatternFill(start_color="D97706", end_color="D97706", fill_type="solid")       # Amber 600
    CARD_FILL = PatternFill(start_color="F8FAFC", end_color="F8FAFC", fill_type="solid")         # Slate 50
    ZEBRA_FILL = PatternFill(start_color="F1F5F9", end_color="F1F5F9", fill_type="solid")        # Slate 100
    
    # Stage Badges
    STAGE_FILLS = {
        "Discovered": PatternFill(start_color="E2E8F0", end_color="E2E8F0", fill_type="solid"),     # Slate 200
        "Contacted": PatternFill(start_color="DBEAFE", end_color="DBEAFE", fill_type="solid"),      # Blue 100
        "Followed Up": PatternFill(start_color="EDE9FE", end_color="EDE9FE", fill_type="solid"),    # Purple 100
        "Replied": PatternFill(start_color="DCFCE7", end_color="DCFCE7", fill_type="solid"),        # Green 100
        "Meeting Booked": PatternFill(start_color="FEF08A", end_color="FEF08A", fill_type="solid"), # Yellow 200
        "Closed": PatternFill(start_color="BBF7D0", end_color="BBF7D0", fill_type="solid"),         # Green 200
        "Unresponsive": PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")   # Red 100
    }

    THIN_BORDER = Border(
        left=Side(style='thin', color='CBD5E1'),
        right=Side(style='thin', color='CBD5E1'),
        top=Side(style='thin', color='CBD5E1'),
        bottom=Side(style='thin', color='CBD5E1')
    )
    CARD_BORDER = Border(
        left=Side(style='medium', color='0F172A'),
        right=Side(style='medium', color='0F172A'),
        top=Side(style='medium', color='0F172A'),
        bottom=Side(style='medium', color='0F172A')
    )

    FONT_TITLE = Font(name="Calibri", size=16, bold=True, color="0F172A")
    FONT_SUBTITLE = Font(name="Calibri", size=11, italic=True, color="475569")
    FONT_HEADER = Font(name="Calibri", size=11, bold=True, color="FFFFFF")
    FONT_CARD_TITLE = Font(name="Calibri", size=10, bold=True, color="64748B")
    FONT_CARD_VAL = Font(name="Calibri", size=18, bold=True, color="0F172A")
    FONT_ROW = Font(name="Calibri", size=10)
    FONT_BOLD = Font(name="Calibri", size=10, bold=True)
    FONT_LINK = Font(name="Calibri", size=10, color="2563EB", underline="single")

    # -------------------------------------------------------------
    # TAB 1: EXECUTIVE KPI DASHBOARD
    # -------------------------------------------------------------
    ws_dash = wb.active
    ws_dash.title = "Executive Dashboard"
    ws_dash.views.sheetView[0].showGridLines = True

    # Title Block
    ws_dash["B2"] = "Tariq & Co. Tech — Client Hunting & CRM Executive Dashboard"
    ws_dash["B2"].font = FONT_TITLE
    ws_dash["B3"] = f"Report Date: {datetime.now().strftime('%B %d, %Y - %I:%M %p')}  |  Website: https://tariq-co-tech.vercel.app"
    ws_dash["B3"].font = FONT_SUBTITLE

    # KPI Metric Cards (Rows 5 to 7)
    kpis = [
        ("TOTAL LEADS", stats["Total Prospects"], "B", "C"),
        ("INITIAL SENT", stats["Contacted"], "D", "E"),
        ("FOLLOW-UPS DUE", stats["Follow-Ups Due Now"], "F", "G"),
        ("FOLLOWED UP", stats["Followed Up"], "H", "I"),
        ("REPLIED / WON", stats["Replied"] + stats["Meeting Booked"], "J", "K"),
        ("RESPONSE RATE", stats["Response Rate"], "L", "M")
    ]

    for title, val, start_col, end_col in kpis:
        c1, c2 = f"{start_col}5", f"{end_col}5"
        ws_dash.merge_cells(f"{c1}:{c2}")
        top_cell = ws_dash[c1]
        top_cell.value = title
        top_cell.font = FONT_CARD_TITLE
        top_cell.fill = CARD_FILL
        top_cell.alignment = Alignment(horizontal="center", vertical="center")

        v1, v2 = f"{start_col}6", f"{end_col}7"
        ws_dash.merge_cells(f"{v1}:{v2}")
        val_cell = ws_dash[v1]
        val_cell.value = val
        val_cell.font = FONT_CARD_VAL
        val_cell.fill = CARD_FILL
        val_cell.alignment = Alignment(horizontal="center", vertical="center")

        for r in range(5, 8):
            for c in [start_col, end_col]:
                ws_dash[f"{c}{r}"].border = THIN_BORDER

    # Pipeline Breakdown Table (Row 9 onward)
    ws_dash["B10"] = "Pipeline Stage Breakdown"
    ws_dash["B10"].font = Font(name="Calibri", size=13, bold=True, color="0F172A")

    breakdown_headers = ["Pipeline Stage", "Prospect Count", "% of Total", "Target Action for Team"]
    for idx, h in enumerate(breakdown_headers, 2):
        cell = ws_dash.cell(row=11, column=idx, value=h)
        cell.font = FONT_HEADER
        cell.fill = NAVY_HEADER
        cell.alignment = Alignment(horizontal="center" if idx in [3, 4] else "left", vertical="center")
        cell.border = THIN_BORDER

    total_prospects = max(stats["Total Prospects"], 1)
    stage_actions = {
        "Discovered": "Run hunt.py to review audits and dispatch initial plain-text emails",
        "Contacted": "Awaiting 3-day window; monitor inbox for client replies",
        "Followed Up": "Dispatched conversational 3-day follow-up; check WhatsApp",
        "Replied": "HIGH PRIORITY: Hop on 10-min scoping call or WhatsApp +92 314 9574681",
        "Meeting Booked": "Conduct technical scoping review and prepare project milestone agreement",
        "Closed": "Onboard client into PMS; begin sprint kickoff",
        "Unresponsive": "Archive; re-engage in 90 days with new case study proof"
    }

    current_row = 12
    for stage in ["Discovered", "Contacted", "Followed Up", "Replied", "Meeting Booked", "Closed", "Unresponsive"]:
        cnt = stats.get(stage, 0)
        pct = f"{(cnt / total_prospects) * 100:.1f}%"
        action = stage_actions.get(stage, "")

        ws_dash.cell(row=current_row, column=2, value=stage).font = FONT_BOLD
        ws_dash.cell(row=current_row, column=2).fill = STAGE_FILLS.get(stage, ZEBRA_FILL)
        ws_dash.cell(row=current_row, column=2).border = THIN_BORDER

        cnt_cell = ws_dash.cell(row=current_row, column=3, value=cnt)
        cnt_cell.alignment = Alignment(horizontal="center")
        cnt_cell.border = THIN_BORDER
        cnt_cell.font = FONT_ROW

        pct_cell = ws_dash.cell(row=current_row, column=4, value=pct)
        pct_cell.alignment = Alignment(horizontal="center")
        pct_cell.border = THIN_BORDER
        pct_cell.font = FONT_ROW

        act_cell = ws_dash.cell(row=current_row, column=5, value=action)
        act_cell.border = THIN_BORDER
        act_cell.font = FONT_ROW

        current_row += 1

    # -------------------------------------------------------------
    # TAB 2: ACTIVE PROSPECTS & FOLLOW-UP SCHEDULE
    # -------------------------------------------------------------
    ws_leads = wb.create_sheet(title="Prospect Tracker")
    ws_leads.views.sheetView[0].showGridLines = True

    tracker_headers = [
        "ID", "Company Name", "Website", "Primary Email", "Phone",
        "Niche", "Location", "Current Stage", "Initial Contact Date",
        "Follow-Up Due Date", "Follow-Up Urgency", "Matched Case Study",
        "Detected Website Bottleneck", "Latest Notes"
    ]

    for col_num, h in enumerate(tracker_headers, 1):
        cell = ws_leads.cell(row=1, column=col_num, value=h)
        cell.font = FONT_HEADER
        cell.fill = NAVY_HEADER
        cell.alignment = Alignment(horizontal="center" if col_num in [1, 8, 9, 10, 11] else "left", vertical="center")
        cell.border = THIN_BORDER

    now = datetime.now()
    for row_num, p in enumerate(prospects, 2):
        # Calculate urgency
        stage = p.get("stage", "Discovered")
        due_at = p.get("follow_up_due_at")
        urgency = "—"
        if stage == "Contacted":
            if due_at:
                try:
                    due_dt = datetime.strptime(due_at, "%Y-%m-%d %H:%M:%S")
                    if due_dt <= now:
                        urgency = "DUE TODAY"
                    elif due_dt <= now + timedelta(days=1):
                        urgency = "DUE TOMORROW"
                    else:
                        days = (due_dt - now).days
                        urgency = f"In {days} Days"
                except Exception:
                    urgency = "Pending"
            else:
                urgency = "Due for Follow-Up"
        elif stage == "Followed Up":
            urgency = "Completed"
        elif stage == "Replied":
            urgency = "ACTION: REPLIED!"

        row_data = [
            p.get("id"),
            p.get("company_name"),
            p.get("website_url"),
            p.get("primary_email") or "Not found",
            p.get("phone") or "—",
            p.get("niche") or "—",
            p.get("location") or "Global",
            stage,
            p.get("contacted_at") or "—",
            p.get("follow_up_due_at") or "—",
            urgency,
            p.get("matched_case_study"),
            p.get("detected_gap"),
            p.get("last_notes")
        ]

        fill = ZEBRA_FILL if row_num % 2 == 0 else PatternFill(fill_type=None)
        for col_num, val in enumerate(row_data, 1):
            cell = ws_leads.cell(row=row_num, column=col_num, value=val)
            cell.border = THIN_BORDER
            cell.font = FONT_ROW
            if fill.fill_type:
                cell.fill = fill

            # Special styling
            if col_num == 3 and val and str(val).startswith("http"):
                cell.font = FONT_LINK
            elif col_num == 8:  # Stage
                cell.font = FONT_BOLD
                cell.fill = STAGE_FILLS.get(stage, fill)
                cell.alignment = Alignment(horizontal="center")
            elif col_num == 11:  # Urgency
                cell.alignment = Alignment(horizontal="center")
                if "DUE TODAY" in urgency or "ACTION" in urgency:
                    cell.font = Font(name="Calibri", size=10, bold=True, color="991B1B")  # Red
                    cell.fill = PatternFill(start_color="FEE2E2", end_color="FEE2E2", fill_type="solid")
                elif "Completed" in urgency:
                    cell.font = Font(name="Calibri", size=10, bold=True, color="166534")  # Green

    # -------------------------------------------------------------
    # TAB 3: OUTREACH TEMPLATES & SCRIPTS
    # -------------------------------------------------------------
    ws_scripts = wb.create_sheet(title="Outreach Copy Vault")
    ws_scripts.views.sheetView[0].showGridLines = True

    script_headers = [
        "Company Name", "Target Email", "Initial Cold Email Subject",
        "Initial Cold Email Body", "3-Day Follow-Up Email Body", "WhatsApp Direct Script"
    ]

    for col_num, h in enumerate(script_headers, 1):
        cell = ws_scripts.cell(row=1, column=col_num, value=h)
        cell.font = FONT_HEADER
        cell.fill = NAVY_HEADER
        cell.alignment = Alignment(horizontal="left", vertical="center")
        cell.border = THIN_BORDER

    for row_num, p in enumerate(prospects, 2):
        script_row = [
            p.get("company_name"),
            p.get("primary_email") or "Contact Form",
            p.get("initial_subject"),
            p.get("initial_body"),
            p.get("follow_up_body"),
            p.get("whatsapp_script")
        ]
        fill = ZEBRA_FILL if row_num % 2 == 0 else PatternFill(fill_type=None)
        for col_num, val in enumerate(script_row, 1):
            cell = ws_scripts.cell(row=row_num, column=col_num, value=val)
            cell.border = THIN_BORDER
            cell.font = FONT_ROW
            if fill.fill_type:
                cell.fill = fill
            if col_num in [4, 5, 6]:
                cell.alignment = Alignment(wrap_text=True, vertical="top")

    # Auto-adjust column widths across all sheets
    for sheet in [ws_dash, ws_leads, ws_scripts]:
        for col in sheet.columns:
            max_len = 0
            col_letter = get_column_letter(col[0].column)
            for cell in col:
                val_str = str(cell.value or '')
                if '\n' in val_str:
                    val_str = val_str.split('\n')[0]
                max_len = max(max_len, len(val_str))
            sheet.column_dimensions[col_letter].width = min(max(max_len + 3, 12), 48)

    # Save to disk
    wb.save(excel_filename)
    wb.save(latest_filename)

    return {
        "xlsx": str(excel_filename),
        "latest_xlsx": str(latest_filename),
        "csv": str(csv_filename)
    }

# =============================================================================
# AUTOMATED FOLLOW-UP RUNNER
# =============================================================================

def process_due_follow_ups(auto_send: bool = False, dry_run: bool = True) -> List[dict]:
    """
    Checks the CRM for all leads whose 3-day follow-up deadline has passed.
    Dispatches follow-up emails via mailer.py and updates their stage in SQLite.
    """
    from mailer import send_outreach_email, get_email_credentials

    due_leads = get_due_follow_ups()
    if not due_leads:
        print("[*] No follow-ups are due at this moment. All contacted leads are within schedule!")
        return []

    print(f"\n[*] Found {len(due_leads)} prospects due for follow-up outreach!")
    results = []

    for idx, lead in enumerate(due_leads, 1):
        cname = lead["company_name"]
        email = lead["primary_email"]
        subject = lead["follow_up_subject"] or f"Re: quick question re: {cname}"
        body = lead["follow_up_body"] or (
            f"Hi,\n\nJust floating this back to the top of your inbox in case it got buried. "
            f"Are you open to seeing how we solved this for our recent clients, or is {cname}'s website "
            f"already scheduled for an update?\n\nBest regards,\nTariq\n+92 314 9574681"
        )

        print(f"  [{idx}/{len(due_leads)}] Follow-up for {cname} ({email})...")

        if auto_send and not dry_run:
            res = send_outreach_email(
                recipient_email=email,
                subject=subject,
                body_text=body,
                attach_catalog=False,  # Plain text guarantees 100% Primary Inbox
                dry_run=False
            )
            if res.get("status") == "sent":
                mark_as_followed_up(lead["id"], notes="3-day follow-up sent automatically via Gmail SMTP")
                results.append({"company": cname, "email": email, "status": "sent"})
            else:
                results.append({"company": cname, "email": email, "status": "failed", "error": res.get("message")})
        else:
            print(f"      [Simulated] Subject: {subject}")
            results.append({"company": cname, "email": email, "status": "simulated"})

    return results

def import_existing_leads_from_sheets():
    """Scans prospect_sheets/ directory and imports existing CSV/JSON prospects into SQLite."""
    import csv
    init_db()
    sheets_dir = BASE_DIR / "prospect_sheets"
    if not sheets_dir.exists():
        return 0

    imported_count = 0
    csv_files = list(sheets_dir.glob("*.csv"))
    
    for f in csv_files:
        if "crm_notion_export" in f.name:
            continue
        try:
            with open(f, "r", encoding="utf-8", errors="replace") as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    url = row.get("Website URL") or row.get("Website") or ""
                    if not url:
                        continue
                    domain = extract_domain(url)
                    company = row.get("Company Name") or row.get("Company") or domain.capitalize()
                    email = row.get("Primary Email") or ""
                    if "Not detected" in email:
                        email = ""
                    all_emails = row.get("All Emails Found") or email
                    phone = row.get("Phone Number") or row.get("Phone") or ""
                    if "Not detected" in phone:
                        phone = ""
                    niche = row.get("Industry / Niche") or row.get("Niche") or ""
                    location = row.get("Target Location") or row.get("Location") or ""
                    gap = row.get("Detected AI / Automation Gap") or row.get("Detected Gap") or ""
                    case_study = row.get("Matched Portfolio Case Study") or ""
                    subject = row.get("Email Subject") or f"quick question re: {company}"
                    disc_date = row.get("Date Discovered") or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                    conn = get_connection()
                    cur = conn.cursor()
                    cur.execute("SELECT id FROM prospects WHERE domain = ?", (domain,))
                    existing = cur.fetchone()
                    if not existing:
                        cur.execute("""
                            INSERT INTO prospects (
                                company_name, domain, website_url, primary_email, all_emails,
                                phone, niche, location, detected_gap, matched_case_study,
                                initial_subject, stage, discovered_at, last_notes
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Discovered', ?, 'Imported from past batch sheet')
                        """, (company, domain, url, email, all_emails, phone, niche, location, gap, case_study, subject, disc_date))
                        imported_count += 1
                    conn.commit()
                    conn.close()
        except Exception as e:
            print(f"Skipping {f.name}: {e}")

    return imported_count

if __name__ == "__main__":
    init_db()
    imported = import_existing_leads_from_sheets()
    if imported > 0:
        print(f"[*] Ingested {imported} historical leads from prospect_sheets into SQLite CRM!")
    stats = get_crm_stats()
    print("==================================================================")
    print("       TARIQ & CO. TECH | CRM PIPELINE & FOLLOW-UP ENGINE")
    print("==================================================================")
    for k, v in stats.items():
        print(f"  {k:<22}: {v}")
    print("------------------------------------------------------------------")
    excel_result = export_team_crm_excel()
    if excel_result.get("xlsx"):
        print(f"[OK] Team Excel Workbook created: {excel_result['xlsx']}")
    print(f"[OK] Notion CSV Database created: {excel_result['csv']}")
    print("==================================================================")
