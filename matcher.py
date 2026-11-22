"""
Matches detected website flaws with Tariq & Co. Tech's core services and case studies.
"""

from config import load_company_profile

def match_opportunity(audit_data: dict) -> dict:
    profile = load_company_profile()
    niche = audit_data.get("inferred_niche", "services_smb")
    issues = audit_data.get("detected_issues", [])
    issue_types = [i["type"] for i in issues]

    # Default fallback match
    chosen_case_study = None
    chosen_service = None
    value_angle = ""
    problem_summary = ""

    # 1. Hospitality / Cafes / Restaurants -> Crispiano Café Case Study
    if niche == "hospitality" or "missing_instant_order" in issue_types:
        chosen_service = next((s for s in profile["core_services"] if s["id"] == "web_dev"), None)
        chosen_case_study = next((c for c in profile["case_studies"] if c["name"] == "Crispiano Café"), None)
        problem_summary = "Customer ordering or inquiries appear scattered across social media DMs without a 1-click ordering path on the website."
        value_angle = "Replacing scattered DM inquiries with a streamlined, menu-focused mobile web experience and direct 1-click WhatsApp ordering."

    # 2. B2B / Exporters / Manufacturers -> Yousafzai Agri Foods Case Study
    elif niche == "b2b_export" or "manual_b2b_quotes" in issue_types:
        chosen_service = next((s for s in profile["core_services"] if s["id"] == "web_dev"), None)
        chosen_case_study = next((c for c in profile["case_studies"] if c["name"] == "Yousafzai Agri Foods"), None)
        problem_summary = "Product inquiries and price quotes are handled manually, with no automated digital catalog or direct quote request workflow."
        value_angle = "Deploying a structured B2B digital catalog and direct quote engine backed by a simple backend PMS for live inventory updates without code."

    # 3. Education / Institutions / Static Sites -> University Website & CMS Case Study
    elif niche == "education" or "outdated_content" in issue_types:
        chosen_service = next((s for s in profile["core_services"] if s["id"] == "web_dev"), None)
        chosen_case_study = next((c for c in profile["case_studies"] if "University" in c["name"]), None)
        problem_summary = "Content updates and announcements appear static or slow to update, requiring developer time for simple text changes."
        value_angle = "Building a lightweight, custom dynamic admin panel so non-technical team members can manage announcements, media, and listings independently."

    # 4. Tech / SaaS / AI -> VidaAI or AI Business SaaS
    elif niche == "tech_saas" or "slow_speed" in issue_types:
        chosen_service = next((s for s in profile["core_services"] if s["id"] == "ai_integration"), None)
        chosen_case_study = next((c for c in profile["case_studies"] if c["name"] == "VidaAI"), None)
        problem_summary = "High interaction latency or complex workflows slowing down users during request handling."
        value_angle = "Implementing asynchronous background processing (worker queues) and clean interface architecture so users get real-time feedback with zero lag."

    # 5. AI Era Customer Support & Automation Gap
    elif "missing_ai_support" in issue_types and niche in ["services_smb", "tech_saas"]:
        chosen_service = next((s for s in profile["core_services"] if s["id"] == "workflow_automation"), None)
        chosen_case_study = next((c for c in profile["case_studies"] if c["name"] == "AI Business SaaS"), None)
        problem_summary = "Lacks 24/7 automated AI customer support or smart inquiry routing, forcing visitors to wait hours for manual staff replies."
        value_angle = "Integrating an automated AI customer assistant and direct workflow automation so client inquiries are answered in 3 seconds and synced straight to your team."

    # 6. UI/UX & Form Friction / General SMB -> UI/UX Design & Workflow Automation
    else:
        chosen_service = next((s for s in profile["core_services"] if s["id"] == "ui_ux_design"), None)
        chosen_case_study = next((c for c in profile["case_studies"] if c["name"] == "AI Business SaaS"), None)
        problem_summary = "Visitor conversion friction on the website (crowded structure, unoptimized mobile layout, or multi-step contact barrier)."
        value_angle = "Streamlining the page architecture and inquiry flow into an intuitive, high-converting digital experience."

    # Top detected issue to highlight
    primary_issue = issues[0]["summary"] if issues else "Unoptimized mobile conversion and contact flow."

    return {
        "niche": niche,
        "primary_issue": primary_issue,
        "problem_summary": problem_summary,
        "value_angle": value_angle,
        "service": chosen_service,
        "case_study": chosen_case_study,
        "company_info": profile["company"]
    }
