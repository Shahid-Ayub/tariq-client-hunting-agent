# Tariq & Co. Tech — Autonomous Client Hunting & Mailing AI 🎯

An autonomous AI engine built specifically for **Tariq & Co. Tech** (`tariq-co-tech.vercel.app`).

---

## ⚡ What Changed (100% Autonomous)
You **never need to copy and paste website links or emails manually again**. 

Whenever you need new clients:
1. **You tell the agent:** *"Find me 10 prospects for [cafes / b2b exporters / clinics / education] in [city/country]"*.
2. **The agent finds the businesses automatically:** Discovers 10 target companies, their website URLs, emails, and phone numbers.
3. **Audits their sites for AI-era & automation bottlenecks:**
   - Missing 24/7 AI customer support or smart inquiry agents
   - Missing automated order routing / WhatsApp 1-click ordering
   - Outdated static catalogs without instant B2B quote engines
   - Mobile friction and high-dropoff forms
4. **Drafts hyper-tailored emails anchored to your past work:**
   - Pairs with your real case studies (**Crispiano Café**, **Yousafzai Agri Foods**, **VidaAI**, **University CMS**, **AI Business SaaS**).
5. **Attaches your Company Catalog & Sends:**
   - Automatically attaches `Tariq_and_Co_Tech_Catalog.pdf`.
   - Sends directly from your company email (`tariqcotech@gmail.com`) via secure Gmail SMTP with deliverability throttling.

---

## 🚀 How to Run It

### 1. The Simplest Way (Interactive Wizard)
Open your terminal in this folder and simply type:
```bash
python hunt.py
```
The agent will ask you 3 quick questions:
```text
What kind of businesses are you targeting? (e.g. cafes, b2b exporters, clinics): 
What city or country? (e.g. London, Dubai, Pakistan, or Enter for global): 
How many prospects do you want to find and email? [Default: 10]: 
```
It immediately finds them, audits them, writes the emails, and asks if you want to send them!

---

### 2. Fast 1-Line Command
```bash
# Find 10 cafes in London
python hunt.py --auto --niche "cafes" --location "London" --count 10

# Find 10 B2B exporters in Pakistan
python hunt.py --auto --niche "b2b exporters" --location "Pakistan" --count 10

# Find 10 educational institutes in the UK
python hunt.py --auto --niche "schools" --location "UK" --count 10
```

---

## 📧 Connecting Your Company Gmail (`tariqcotech@gmail.com`)

To let the agent send live emails with the catalog attached:
1. Go to your **Google Account** $\rightarrow$ **Security**.
2. Make sure **2-Step Verification** is turned ON.
3. Search for **App Passwords** in the search bar.
4. Create an App Password (name it `Client Hunter`). Google will give you a 16-letter code.
5. Create a file named `.env` in this folder (or edit `.env.example` and rename it to `.env`):
   ```env
   SENDER_EMAIL=tariqcotech@gmail.com
   SENDER_PASSWORD=your_16_character_app_password
   SMTP_SERVER=smtp.gmail.com
   SMTP_PORT=587
   ```
6. That's it! When you run `hunt.py`, choose Option `1` to send live emails with your catalog attached!

---

## 📂 Output Dossiers
All discovered leads and drafted emails are saved in:
- `outreach_drafts/batch_<niche>_<location>_<timestamp>.md`
- `prospect_sheets/prospects_<niche>_<location>_<timestamp>.xlsx` (Excel workbook)
- `prospect_sheets/prospects_<niche>_<location>_<timestamp>.csv` (Notion database import)

---

## 📊 Automated CRM Pipeline & Follow-Up Scheduler

The agent features an integrated **SQLite CRM (`crm.db`)** that tracks every prospect from discovery to closing:
`Discovered` $\rightarrow$ `Contacted` $\rightarrow$ `Followed Up` $\rightarrow$ `Replied` $\rightarrow$ `Closed`

### Useful Commands:
```bash
# 1. View live CRM dashboard & conversion rates
python hunt.py --crm

# 2. Process automated 3-day follow-ups for due prospects
python hunt.py --follow-up

# 3. Send due follow-ups live via Gmail SMTP
python hunt.py --follow-up --send

# 4. Generate the latest multi-tab Team Excel Workbook
python hunt.py --export-crm

# 5. Mark a prospect as 'Replied' when they respond
python hunt.py --replied "client@example.com"
```

### 📑 Shareable Team Excel Workbook
Saved at: `prospect_sheets/Tariq_and_Co_Tech_Team_CRM_Latest.xlsx`
- **Tab 1: Executive KPI Dashboard** (Total Leads, Contacted, Awaiting Follow-up, Response Rate).
- **Tab 2: Prospect Tracker** (Company, Email, Stage, Urgency, Follow-Up Due Date, Matched Case Study).
- **Tab 3: Outreach Copy Vault** (Cold Email Body, 3-Day Follow-Up, WhatsApp DM script).

---

## 🐙 Sync to GitHub

Target repository: `https://github.com/Shahid-Ayub/tariq-client-hunting-agent`

To create and sync this codebase to your GitHub account:
```bash
python github_sync.py
```
Or provide your GitHub Personal Access Token directly:
```bash
python github_sync.py <YOUR_GITHUB_TOKEN>
```
*(Your `.env` credentials and client drafts are automatically protected and excluded from sync).*

