"""
Bulk sync leads from SQLite to Notion with resume support.
"""
import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error
import time
from datetime import datetime

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agentsfactory_metrics.db"))
NOTION_DB_ID = "37d4baec-8165-81fe-ab68-d2c3c347589d"

def get_notion_key():
    config_path = os.path.join(os.path.expanduser("~"), ".hermes", ".env")
    if os.path.exists(config_path):
        with open(config_path) as f:
            for line in f:
                if line.strip().startswith("NOTION_API_KEY="):
                    return line.strip().split("=", 1)[1].strip()
    return os.environ.get("NOTION_API_KEY", "")

def notion_request(method, path, data=None):
    key = get_notion_key()
    url = f"https://api.notion.com/v1{path}"
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    req.add_header("Content-Type", "application/json")
    req.add_header("Notion-Version", "2022-06-28")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()
        return {"error": True, "status": e.code, "message": error_body}

def add_lead_to_notion(lead):
    properties = {
        "Company": {"title": [{"text": {"content": str(lead.get("company", ""))[:200]}}]},
    }
    if lead.get("email"):
        properties["Email"] = {"email": lead["email"]}
    if lead.get("phone"):
        properties["Phone"] = {"phone_number": lead["phone"]}
    if lead.get("website"):
        properties["Website"] = {"url": lead["website"]}
    if lead.get("category"):
        properties["Category"] = {"select": {"name": str(lead["category"])[:100]}}
    score = lead.get("social_lead_score", "")
    if score in ("HOT", "Great", "Good", "Poor"):
        properties["Social Score"] = {"select": {"name": score}}
    if lead.get("facebook_followers"):
        properties["Facebook Followers"] = {"number": lead["facebook_followers"]}
    if lead.get("twitter_followers"):
        properties["Twitter Followers"] = {"number": lead["twitter_followers"]}
    if lead.get("facebook_url"):
        properties["Facebook URL"] = {"url": lead["facebook_url"]}
    if lead.get("twitter_url"):
        properties["Twitter URL"] = {"url": lead["twitter_url"]}
    if lead.get("gmb_url"):
        properties["GMB URL"] = {"url": lead["gmb_url"]}
    if lead.get("keyword"):
        properties["Keyword"] = {"rich_text": [{"text": {"content": str(lead["keyword"])[:200]}}]}

    result = notion_request("POST", "/pages", {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": properties
    })
    return result

def sync_leads():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Add notion_synced column if not exists
    cols = [col[1] for col in conn.execute("PRAGMA table_info(leads)").fetchall()]
    if "notion_synced" not in cols:
        conn.execute("ALTER TABLE leads ADD COLUMN notion_synced INTEGER DEFAULT 0")
        conn.commit()

    # Get unsynced leads
    leads = conn.execute("""
        SELECT id, company, email, phone, website, category, social_lead_score,
               facebook_followers, twitter_followers, facebook_url, twitter_url,
               gmb_url, keyword
        FROM leads
        WHERE notion_synced = 0 OR notion_synced IS NULL
        ORDER BY
            CASE social_lead_score
                WHEN 'HOT' THEN 1 WHEN 'Great' THEN 2 WHEN 'Good' THEN 3 ELSE 4
            END,
            facebook_followers DESC
    """).fetchall()
    leads = [dict(l) for l in leads]
    total = len(leads)
    print(f"Leads to sync: {total}")

    success = 0
    errors = 0
    rate_limit_backoff = 1.0

    for i, lead in enumerate(leads):
        result = add_lead_to_notion(lead)
        if "error" in result:
            if result.get("status") == 429:
                print(f"  Rate limited, waiting {rate_limit_backoff}s...")
                time.sleep(rate_limit_backoff)
                rate_limit_backoff = min(rate_limit_backoff * 2, 30)
                # Retry
                result = add_lead_to_notion(lead)
            if "error" in result:
                errors += 1
                if errors <= 5:
                    print(f"  Error: {result.get('message', '')[:100]}")
            else:
                success += 1
        else:
            success += 1
            rate_limit_backoff = 1.0

        # Mark as synced
        conn.execute("UPDATE leads SET notion_synced = 1 WHERE id = ?", (lead["id"],))
        conn.commit()

        if (i + 1) % 50 == 0:
            print(f"  Progress: {i+1}/{total} | Success: {success} | Errors: {errors}")
            time.sleep(0.5)  # Rate limit buffer
        else:
            time.sleep(0.3)  # ~3 requests/second

    print(f"\nDone! Synced: {success}, Errors: {errors}, Total: {total}")
    conn.close()

if __name__ == "__main__":
    sync_leads()
