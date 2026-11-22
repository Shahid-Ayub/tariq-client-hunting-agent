"""
Website auditing and data extraction engine for prospect sites.
Uses standard library tools (urllib + html.parser) with zero required dependencies,
falling back gracefully to mock analysis if the site is offline or unreachable.
"""

import re
import ssl
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser

class SimpleHTMLAuditor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.title = ""
        self.meta_description = ""
        self.has_viewport = False
        self.in_title = False
        self.headings = []
        self.current_heading_tag = None
        self.current_heading_text = []
        self.links = []
        self.forms = []
        self.current_form = None
        self.text_content = []
        self.script_srcs = []
        self.generator = ""
        self.has_whatsapp_link = False
        self.has_chat_widget = False
        self.social_links = {
            "instagram": [],
            "facebook": [],
            "linkedin": [],
            "twitter": []
        }

    def handle_starttag(self, tag, attrs):
        attrs_dict = {k.lower(): (v or "") for k, v in attrs}
        
        if tag == "title":
            self.in_title = True
        elif tag == "meta":
            name = attrs_dict.get("name", "").lower()
            prop = attrs_dict.get("property", "").lower()
            content = attrs_dict.get("content", "")
            
            if name == "viewport":
                self.has_viewport = True
            elif name == "description" or prop == "og:description":
                if not self.meta_description:
                    self.meta_description = content
            elif name == "generator":
                self.generator = content
                
        elif tag in ["h1", "h2"]:
            self.current_heading_tag = tag
            self.current_heading_text = []
            
        elif tag == "a":
            href = attrs_dict.get("href", "")
            if href:
                self.links.append(href)
                lower_href = href.lower()
                if "wa.me/" in lower_href or "api.whatsapp.com" in lower_href or "whatsapp.com" in lower_href:
                    self.has_whatsapp_link = True
                if "instagram.com" in lower_href:
                    self.social_links["instagram"].append(href)
                elif "facebook.com" in lower_href:
                    self.social_links["facebook"].append(href)
                elif "linkedin.com" in lower_href:
                    self.social_links["linkedin"].append(href)
                elif "twitter.com" in lower_href or "x.com" in lower_href:
                    self.social_links["twitter"].append(href)

        elif tag == "form":
            self.current_form = {"action": attrs_dict.get("action", ""), "method": attrs_dict.get("method", "get"), "inputs": 0}
            self.forms.append(self.current_form)

        elif tag in ["input", "textarea", "select"] and self.current_form is not None:
            input_type = attrs_dict.get("type", "text").lower()
            if input_type != "hidden":
                self.current_form["inputs"] += 1

        elif tag == "script":
            src = attrs_dict.get("src", "")
            if src:
                self.script_srcs.append(src)
                lower_src = src.lower()
                # Check for live chat / AI bot widgets
                if any(bot in lower_src for bot in ["intercom", "crisp.chat", "tawk.to", "zendesk", "drift", "tidio", "chatbase", "botpress", "livechat"]):
                    self.has_chat_widget = True

    def handle_endtag(self, tag):
        if tag == "title":
            self.in_title = False
        elif tag in ["h1", "h2"] and self.current_heading_tag == tag:
            text = " ".join("".join(self.current_heading_text).split())
            if text:
                self.headings.append((tag, text))
            self.current_heading_tag = None
            self.current_heading_text = []
        elif tag == "form":
            self.current_form = None

    def handle_data(self, data):
        clean_data = data.strip()
        if not clean_data:
            return
        if self.in_title:
            self.title += " " + clean_data
        elif self.current_heading_tag:
            self.current_heading_text.append(clean_data)
        self.text_content.append(clean_data)

def extract_contacts_from_text(raw_html, full_text):
    combined = raw_html + " " + full_text
    
    # Email regex
    email_pattern = r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+'
    found_emails = set(re.findall(email_pattern, combined))
    
    # Filter common garbage emails
    clean_emails = []
    ignored_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.svg', '.webp', '.js', '.css')
    ignored_domains = ('example.com', 'domain.com', 'wixpress.com', 'sentry.io')
    
    for email in found_emails:
        lower_email = email.lower()
        if lower_email.endswith(ignored_extensions):
            continue
        if any(d in lower_email for d in ignored_domains):
            continue
        clean_emails.append(email)

    # Phone regex
    phone_pattern = r'(?:\+?\d{1,3}[-.\s]?)?\(?\d{2,4}\)?[-.\s]?\d{3,4}[-.\s]?\d{3,5}'
    raw_phones = re.findall(phone_pattern, full_text)
    clean_phones = list(set([p.strip() for p in raw_phones if len(re.sub(r'\D', '', p)) >= 9]))[:3]
    
    return clean_emails[:5], clean_phones

def audit_website(url: str, timeout: int = 10, mock_mode: bool = False, custom_niche: str = ""):
    """
    Audits a website URL, extracts technical and business characteristics,
    and returns an organized diagnostic dictionary.
    """
    if mock_mode:
        return generate_mock_audit(url, custom_niche)

    if not url.startswith("http://") and not url.startswith("https://"):
        url = "https://" + url

    parsed_url = urllib.parse.urlparse(url)
    domain = parsed_url.netloc or parsed_url.path

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }

    start_time = time.time()
    raw_html = ""
    status_code = 200
    
    # Ignore self-signed/expired cert issues during audit
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=timeout, context=ctx) as response:
            status_code = response.getcode()
            charset = response.headers.get_content_charset() or "utf-8"
            raw_html = response.read().decode(charset, errors="replace")
    except Exception as e:
        # Fallback to mock data if network is inaccessible (e.g. offline or strict sandbox)
        return {
            "status": "error_fallback",
            "url": url,
            "domain": domain,
            "error": str(e),
            "fallback_audit": generate_mock_audit(url, custom_niche)
        }

    response_time_ms = int((time.time() - start_time) * 1000)

    parser = SimpleHTMLAuditor()
    try:
        parser.feed(raw_html)
    except Exception:
        pass

    full_text = " ".join(parser.text_content)
    emails, phones = extract_contacts_from_text(raw_html, full_text)

    # Detect copyright year
    copyright_match = re.search(r'(?:©|copyright)\s*(?:20\d{2}-)?(20\d{2})', full_text, re.IGNORECASE)
    copyright_year = copyright_match.group(1) if copyright_match else None

    # Detect CMS / Framework hints
    tech_stack_detected = []
    if "wp-content" in raw_html or "wordpress" in parser.generator.lower():
        tech_stack_detected.append("WordPress")
    if "shopify" in raw_html:
        tech_stack_detected.append("Shopify")
    if "_next" in raw_html or "next.js" in raw_html:
        tech_stack_detected.append("Next.js")
    if "wix" in raw_html:
        tech_stack_detected.append("Wix")
    if "squarespace" in raw_html:
        tech_stack_detected.append("Squarespace")

    # Business signals & pain points
    text_lower = full_text.lower()
    inferred_niche = custom_niche.lower() if custom_niche else ""
    if not inferred_niche:
        if any(w in text_lower for w in ["menu", "coffee", "cafe", "restaurant", "dining", "breakfast", "burger", "pastry"]):
            inferred_niche = "hospitality"
        elif any(w in text_lower for w in ["manufacturer", "export", "b2b", "wholesale", "supplier", "industrial"]):
            inferred_niche = "b2b_export"
        elif any(w in text_lower for w in ["course", "academy", "university", "school", "curriculum", "students"]):
            inferred_niche = "education"
        elif any(w in text_lower for w in ["saas", "platform", "software", "ai ", "app", "api"]):
            inferred_niche = "tech_saas"
        else:
            inferred_niche = "services_smb"

    detected_issues = []
    
    # 1. Mobile viewport
    if not parser.has_viewport:
        detected_issues.append({
            "type": "mobile_unfriendly",
            "severity": "HIGH",
            "summary": "Missing mobile viewport meta tag - site looks zoomed-out or broken on mobile devices."
        })

    # 2. Page speed / latency
    if response_time_ms > 2500:
        detected_issues.append({
            "type": "slow_speed",
            "severity": "MEDIUM",
            "summary": f"Initial server response was slow ({response_time_ms}ms), which frustrates visitors on mobile."
        })

    # 3. Form / Inquiry flow friction
    if not parser.forms:
        detected_issues.append({
            "type": "no_inquiry_form",
            "severity": "HIGH",
            "summary": "No interactive inquiry or quote form found; visitors must manually copy an email address."
        })
    else:
        # Check if form has excessive inputs (> 6)
        large_forms = [f for f in parser.forms if f["inputs"] >= 7]
        if large_forms:
            detected_issues.append({
                "type": "high_form_friction",
                "severity": "MEDIUM",
                "summary": f"Inquiry form asks for {large_forms[0]['inputs']} fields, increasing visitor drop-off."
            })

    # AI Era Gap: Missing 24/7 AI Customer Support / Chat Assistant
    if not parser.has_chat_widget:
        detected_issues.append({
            "type": "missing_ai_support",
            "severity": "HIGH",
            "summary": "No 24/7 AI customer support or smart assistant found on site; customer inquiries must wait for manual staff response."
        })

    # 4. WhatsApp / Instant Ordering for hospitality & local services
    if inferred_niche in ["hospitality", "services_smb"] and not parser.has_whatsapp_link:
        detected_issues.append({
            "type": "missing_instant_order",
            "severity": "HIGH",
            "summary": "No direct WhatsApp or 1-click ordering button found; customers must navigate multiple pages or DM on social media."
        })

    # 5. Outdated CMS / Copyright
    if copyright_year and int(copyright_year) <= 2023:
        detected_issues.append({
            "type": "outdated_content",
            "severity": "MEDIUM",
            "summary": f"Footer shows copyright {copyright_year}, indicating static content that hasn't been refreshed."
        })

    # 6. B2B Catalog / Direct Quote
    if inferred_niche == "b2b_export" and ("request quote" not in text_lower and "quote" not in text_lower):
        detected_issues.append({
            "type": "manual_b2b_quotes",
            "severity": "HIGH",
            "summary": "Lacks an automated or structured quote request workflow for B2B buyers."
        })

    return {
        "status": "success",
        "url": url,
        "domain": domain,
        "title": parser.title.strip(),
        "meta_description": parser.meta_description.strip(),
        "headings": parser.headings[:5],
        "emails": emails,
        "phones": phones,
        "whatsapp_present": parser.has_whatsapp_link,
        "social_links": {k: list(set(v)) for k, v in parser.social_links.items()},
        "inferred_niche": inferred_niche,
        "tech_stack": tech_stack_detected,
        "response_time_ms": response_time_ms,
        "detected_issues": detected_issues,
        "copyright_year": copyright_year
    }

def generate_mock_audit(url: str, custom_niche: str = ""):
    """Generates a realistic audit report for demonstration and testing."""
    parsed = urllib.parse.urlparse(url if "://" in url else "https://" + url)
    domain = parsed.netloc or parsed.path or "example-business.com"
    clean_name = domain.replace("www.", "").split(".")[0].capitalize()

    niche = custom_niche.lower() if custom_niche else "hospitality"

    mock_db = {
        "hospitality": {
            "title": f"{clean_name} | Artisan Café & Bistro",
            "meta_description": f"Welcome to {clean_name}. Enjoy freshly brewed organic coffee and artisan pastries.",
            "inferred_niche": "hospitality",
            "emails": [f"hello@{domain}", f"orders@{domain}"],
            "phones": ["+1 (555) 234-8901"],
            "whatsapp_present": False,
            "detected_issues": [
                {
                    "type": "missing_instant_order",
                    "severity": "HIGH",
                    "summary": "No direct WhatsApp or 1-click mobile ordering path found; customers are instructed to DM on Instagram."
                },
                {
                    "type": "slow_speed",
                    "severity": "MEDIUM",
                    "summary": "Heavy uncompressed food images causing 3.2s mobile loading delay."
                }
            ]
        },
        "b2b_export": {
            "title": f"{clean_name} International | Global Wholesale & Trade",
            "meta_description": f"Exporter and distributor of premium goods across Europe and Asia.",
            "inferred_niche": "b2b_export",
            "emails": [f"sales@{domain}", f"inquiry@{domain}"],
            "phones": ["+44 20 7946 0912"],
            "whatsapp_present": False,
            "detected_issues": [
                {
                    "type": "manual_b2b_quotes",
                    "severity": "HIGH",
                    "summary": "Product catalog is listed as static text/downloadable PDF with no structured online quote system."
                },
                {
                    "type": "no_inquiry_form",
                    "severity": "HIGH",
                    "summary": "Lacks a fast quote calculator or dynamic enquiry routing for international buyers."
                }
            ]
        },
        "education": {
            "title": f"{clean_name} Institute of Applied Sciences",
            "meta_description": "Accredited educational programs and professional diplomas.",
            "inferred_niche": "education",
            "emails": [f"admissions@{domain}", f"info@{domain}"],
            "phones": ["+1 (800) 555-0199"],
            "whatsapp_present": False,
            "detected_issues": [
                {
                    "type": "outdated_content",
                    "severity": "HIGH",
                    "summary": "Static content structure where news and faculty announcements require developer intervention to update."
                },
                {
                    "type": "high_form_friction",
                    "severity": "MEDIUM",
                    "summary": "Admissions contact form has 11 input fields, leading to prospective student drop-off."
                }
            ]
        },
        "tech_saas": {
            "title": f"{clean_name} - Smart Analytics Platform",
            "meta_description": "Data analytics and AI automation for enterprise teams.",
            "inferred_niche": "tech_saas",
            "emails": [f"contact@{domain}", f"team@{domain}"],
            "phones": [],
            "whatsapp_present": False,
            "detected_issues": [
                {
                    "type": "slow_speed",
                    "severity": "HIGH",
                    "summary": "Dashboard and demo interaction hangs during AI processing requests."
                },
                {
                    "type": "high_form_friction",
                    "severity": "MEDIUM",
                    "summary": "Multi-step trial signup friction with confusing menu hierarchy."
                }
            ]
        }
    }

    selected = mock_db.get(niche, mock_db["hospitality"])
    return {
        "status": "success",
        "url": f"https://{domain}",
        "domain": domain,
        "title": selected["title"],
        "meta_description": selected["meta_description"],
        "headings": [("h1", selected["title"]), ("h2", "Our Services & Products")],
        "emails": selected["emails"],
        "phones": selected["phones"],
        "whatsapp_present": selected["whatsapp_present"],
        "social_links": {"instagram": [f"https://instagram.com/{clean_name.lower()}"], "facebook": [], "linkedin": [], "twitter": []},
        "inferred_niche": selected["inferred_niche"],
        "tech_stack": ["HTML", "CSS", "jQuery"],
        "response_time_ms": 1850,
        "detected_issues": selected["detected_issues"],
        "copyright_year": "2023"
    }
