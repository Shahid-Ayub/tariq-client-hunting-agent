"""
Configuration and knowledge base loader for Tariq & Co. Tech Client Hunter.
"""

import json
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
PROFILE_PATH = BASE_DIR / "company_profile.json"

DEFAULT_PROFILE = {
    "company": {
        "name": "Tariq & Co. Tech",
        "tagline": "Engineering the Future. Building What Matters.",
        "website": "https://tariq-co-tech.vercel.app",
        "portfolio_url": "https://tariq-co-tech.vercel.app/work",
        "email": "tariqcotech@gmail.com",
        "whatsapp": "+92 314 9574681",
        "positioning": "Technology company building software solutions, digital experiences, and business automation for small and growing businesses."
    }
}

def load_company_profile():
    if PROFILE_PATH.exists():
        try:
            with open(PROFILE_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"[Warning] Could not parse company_profile.json: {e}")
    return DEFAULT_PROFILE
