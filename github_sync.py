"""
GitHub Sync Engine for Tariq & Co. Tech Client Hunting AI Agent.
Syncs the agent codebase to https://github.com/Shahid-Ayub/tariq-client-hunting-agent
Uses pure Python with standard libraries (zero third-party dependencies required).
"""

import os
import sys
import json
import base64
import urllib.request
import urllib.error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
REPO_NAME = "tariq-client-hunting-agent"
GITHUB_OWNER = "Shahid-Ayub"

# Files and directories to NEVER upload to GitHub
IGNORED_PATTERNS = [
    ".env",
    ".git",
    "__pycache__",
    "outreach_drafts",
    "prospect_sheets",
    "*.pyc"
]

def should_ignore(rel_path: str) -> bool:
    parts = Path(rel_path).parts
    for p in parts:
        if p == ".env" or p.startswith(".env.") and not p == ".env.example":
            return True
        if p in ["__pycache__", "outreach_drafts", "prospect_sheets", ".git"]:
            return True
        if p.endswith(".pyc") or p.endswith(".log") or p.endswith(".db"):
            return True
    return False

def get_repo_files() -> dict:
    files = {}
    # Ensure README.md is uploaded first to initialize the default branch
    readme_path = BASE_DIR / "README.md"
    if readme_path.exists():
        with open(readme_path, "rb") as f:
            files["README.md"] = f.read()

    for item in sorted(BASE_DIR.rglob("*")):
        if item.is_file():
            rel = item.relative_to(BASE_DIR).as_posix()
            if rel != "README.md" and not should_ignore(rel):
                try:
                    with open(item, "rb") as f:
                        files[rel] = f.read()
                except Exception as e:
                    print(f"Skipping {rel}: {e}")
    return files

def github_api_request(url: str, method: str = "GET", token: str = "", data: dict = None):
    headers = {
        "User-Agent": "TariqCoTech-AgentSync",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28"
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    body = json.dumps(data).encode("utf-8") if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    
    with urllib.request.urlopen(req, timeout=25) as resp:
        return json.loads(resp.read().decode("utf-8"))

def ensure_repository(token: str, repo_name: str = REPO_NAME, private: bool = False):
    check_url = f"https://api.github.com/repos/{GITHUB_OWNER}/{repo_name}"
    try:
        repo_info = github_api_request(check_url, method="GET", token=token)
        print(f"[OK] Repository found: {repo_info['html_url']}")
        return repo_info
    except urllib.error.HTTPError as e:
        if e.code == 404:
            print(f"[*] Repository '{repo_name}' not found under https://github.com/{GITHUB_OWNER}.")
            print(f"[*] Attempting to create it via GitHub REST API...")
            create_url = "https://api.github.com/user/repos"
            payload = {
                "name": repo_name,
                "description": "Autonomous AI Agent for Lead Discovery, Website Auditing & Hyper-Personalized Email Outreach | Tariq & Co. Tech",
                "private": private,
                "auto_init": True
            }
            try:
                return github_api_request(create_url, method="POST", token=token, data=payload)
            except urllib.error.HTTPError as create_err:
                if create_err.code == 403:
                    print("\n[Notice] Fine-grained tokens (github_pat_...) are restricted by GitHub from creating new repositories.")
                    print(f"Please create the repository manually in 10 seconds:")
                    print(f"1. Open https://github.com/new")
                    print(f"2. Repository name: {repo_name}")
                    print(f"3. Click 'Create repository'")
                    print(f"Then re-run this script to upload all files automatically!\n")
                raise create_err
        else:
            raise

def push_file_to_github(token: str, repo_name: str, path: str, content_bytes: bytes):
    url = f"https://api.github.com/repos/{GITHUB_OWNER}/{repo_name}/contents/{path}"
    sha = None
    try:
        existing = github_api_request(url, method="GET", token=token)
        sha = existing.get("sha")
    except urllib.error.HTTPError as e:
        if e.code != 404:
            raise

    b64_content = base64.b64encode(content_bytes).decode("utf-8")
    payload = {
        "message": f"Sync {path}",
        "content": b64_content
    }
    if sha:
        payload["sha"] = sha

    return github_api_request(url, method="PUT", token=token, data=payload)

def sync_all(token: str = ""):
    if not token:
        token = os.getenv("GITHUB_TOKEN", "").strip()
    
    if not token:
        print("\n==============================================================")
        print("          GITHUB REPOSITORY SYNC FOR TARIQ & CO. TECH")
        print("==============================================================")
        print(f"Target Account: https://github.com/{GITHUB_OWNER}")
        print(f"Target Repo:    https://github.com/{GITHUB_OWNER}/{REPO_NAME}")
        print("\nTo create/sync this repo automatically on your GitHub:")
        print("1. Go to https://github.com/settings/tokens?type=beta (or Classic tokens)")
        print("2. Generate a token with 'Repository: Read and Write' permissions")
        print("3. Paste the token when prompted below (or set GITHUB_TOKEN in your terminal)\n")
        token = input("Enter your GitHub Personal Access Token: ").strip()

    if not token:
        print("[!] No token provided. Aborting sync.")
        return

    try:
        repo = ensure_repository(token)
        print(f"[OK] Target repo confirmed: {repo['html_url']}")
        
        files = get_repo_files()
        print(f"[*] Uploading {len(files)} files to {repo['html_url']}...")
        
        for idx, (path, content) in enumerate(files.items(), 1):
            print(f"  [{idx}/{len(files)}] Uploading {path}...")
            push_file_to_github(token, REPO_NAME, path, content)
            
        print("\n[SUCCESS] All files successfully uploaded to GitHub!")
        print(f"View your repository here: {repo['html_url']}\n")
    except Exception as e:
        print(f"\n[Error] GitHub sync failed: {e}")

if __name__ == "__main__":
    token_arg = sys.argv[1] if len(sys.argv) > 1 else ""
    sync_all(token_arg)
