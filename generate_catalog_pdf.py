"""
Generates a clean, professional PDF summary of Tariq & Co. Tech's company catalog.
Uses pure Python with standard libraries (zero third-party dependencies required).
"""

from pathlib import Path

def create_catalog_pdf(output_path: str = "Tariq_and_Co_Tech_Catalog.pdf"):
    out_file = Path(output_path)
    
    # We construct a well-formatted PDF 1.4 document containing Tariq & Co. Tech's complete profile
    lines = [
        "Tariq & Co. Tech - Company Catalog & Capabilities",
        "Engineering the Future. Building What Matters.",
        "Website: https://tariq-co-tech.vercel.app  |  Email: tariqcotech@gmail.com  |  WhatsApp: +92 314 9574681",
        "----------------------------------------------------------------------------------------------------",
        "",
        "1. WHO WE ARE",
        "Tariq & Co. Tech builds software solutions, digital experiences, and workflow automation for growing businesses.",
        "We start with your business problem, build something practical, and keep you informed along the way.",
        "",
        "2. CORE SERVICES",
        "* Full-Stack Web Development: Custom web applications, admin dashboards, database-driven apps, logins & accounts.",
        "* Workflow Automation: Connecting tools (sheets, messages, databases) to eliminate manual copying and repetitive work.",
        "* UI/UX Design: Clean interface redesigns, wireframes, and usability reviews that eliminate visitor friction.",
        "* AI Integration: Smart document extraction, in-app AI features, and background worker queues (BullMQ/Redis).",
        "* Technical Consulting & Scoping: Clear written scope, tech stack evaluation, and phased delivery roadmaps.",
        "",
        "3. PROVEN CASE STUDIES",
        "* Crispiano Cafe (Hospitality Web Experience):",
        "  - Problem: Orders and customer inquiries scattered across social media DMs.",
        "  - Solution: Clean mobile web experience with direct 1-click WhatsApp ordering flow.",
        "",
        "* Yousafzai Agri Foods (B2B Website + Backend PMS):",
        "  - Problem: Manual buyer inquiries and static PDF catalogs consuming excessive staff time.",
        "  - Solution: Structured B2B digital catalog and direct quote engine with a custom management portal.",
        "",
        "* VidaAI (AI Assessment Platform):",
        "  - Problem: AI content generation held up normal app requests and caused user lag.",
        "  - Solution: Built asynchronous background queue workers with BullMQ & Redis for live progress updates.",
        "",
        "* University Website & Dynamic CMS:",
        "  - Problem: Static site required a software developer for every simple announcement change.",
        "  - Solution: Custom dynamic admin panel so non-technical staff manage pages, announcements, and media.",
        "",
        "* AI Business SaaS (Natural Language Operations):",
        "  - Problem: Complex, menu-heavy dashboards overwhelming non-technical owners.",
        "  - Solution: Plain-English conversational commands powered by Gemini API executing database actions in ~3s.",
        "",
        "4. HOW TO GET STARTED",
        "Message us on WhatsApp (+92 314 9574681) for a free first conversation, or email tariqcotech@gmail.com.",
        "Full case studies and live demos: tariq-co-tech.vercel.app/work"
    ]
    
    # Generate PDF stream content
    stream_content = "BT\n/F1 10 Tf\n40 800 Td\n14 TL\n"
    for line in lines:
        escaped_line = line.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")
        if line.startswith("Tariq & Co. Tech"):
            stream_content += f"/F1 16 Tf ({escaped_line}) Tj T* /F1 10 Tf\n"
        elif line and line[0].isdigit() and line[1] == ".":
            stream_content += f"T* /F1 12 Tf ({escaped_line}) Tj T* /F1 10 Tf\n"
        else:
            stream_content += f"({escaped_line}) Tj T*\n"
    stream_content += "ET\n"
    
    stream_bytes = stream_content.encode("latin-1", errors="replace")
    stream_len = len(stream_bytes)
    
    # PDF Object Assembly
    pdf_parts = []
    offsets = []
    
    def add_object(obj_num, content_bytes):
        offsets.append(sum(len(p) for p in pdf_parts))
        pdf_parts.append(f"{obj_num} 0 obj\n".encode("latin-1"))
        pdf_parts.append(content_bytes)
        pdf_parts.append(b"\nendobj\n")

    pdf_parts.append(b"%PDF-1.4\n")
    
    # 1: Catalog
    add_object(1, b"<</Type/Catalog/Pages 2 0 R>>")
    # 2: Pages
    add_object(2, b"<</Type/Pages/Kids[3 0 R]/Count 1>>")
    # 3: Page
    add_object(3, b"<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Resources<</Font<</F1 5 0 R>>>>/Contents 4 0 R>>")
    # 4: Contents Stream
    add_object(4, f"<</Length {stream_len}>>\nstream\n".encode("latin-1") + stream_bytes + b"endstream")
    # 5: Font Helvetica
    add_object(5, b"<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>")
    
    startxref = sum(len(p) for p in pdf_parts)
    xref = f"xref\n0 {len(offsets) + 1}\n0000000000 65535 f \n"
    for off in offsets:
        xref += f"{off:010d} 00000 n \n"
    
    trailer = f"trailer\n<</Size {len(offsets) + 1}/Root 1 0 R>>\nstartxref\n{startxref}\n%%EOF\n"
    pdf_parts.append(xref.encode("latin-1"))
    pdf_parts.append(trailer.encode("latin-1"))
    
    with open(out_file, "wb") as f:
        for part in pdf_parts:
            f.write(part)
            
    return out_file

if __name__ == "__main__":
    path = create_catalog_pdf()
    print(f"[OK] Generated company catalog PDF: {path}")
