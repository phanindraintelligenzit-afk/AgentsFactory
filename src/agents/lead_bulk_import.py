"""
Bulk load leads from SQLite to Notion database.
"""
import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error
import time

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agentsfactory_metrics.db")
NOTION_DB_ID = "37d4baec-8165-81fe-ab68-d2c3c347589d"

def get_notion_key():
    path = os.path.join(os.path.expanduser("~"), ".hermes", ".env")
    with open(path) as f:
        for line in f:
            if line.strip().startswith("NOTION_API_KEY="):
                return line.strip().split("=", 1)[1].strip()
    return ""

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
        return {"error": True, "status": e.code, "message": e.read().decode()}

def row_to_notion(lead):
    """Convert a lead row to Notion page properties."""
    props = {
        "Name": {"title": [{"text": {"content": (lead["company"] or "Unknown")[:200]}}]},
    }
    if lead.get("email"):
        props["Email"] = {"email": lead["email"]}
    if lead.get("phone"):
        props["Phone"] = {"phone_number": lead["phone"]}
    if lead.get("category"):
        props["Source"] = {"select": {"name": lead["category"][:100]}}
    # Map social score to stage
    score = lead.get("social_lead_score", "")
    if score == "HOT":
        props["Stage"] = {"select": {"name": "Hot Lead"}}
        props["Score"] = {"number": 90}
    elif score == "Great":
        props["Stage"] = {"select": {"name": "Qualified"}}
        props["Score"] = {"number": 75}
    elif score == "Good":
        props["Stage"] = {"select": {"name": "Contacted"}}
        props["Score"] = {"number": 60}
    else:
        props["Stage"] = {"select": {"name": "New"}}
        props["Score"] = {"number": 40}
    return props

def batch_create_pages(pages_data):
    """Create multiple pages using batch API."""
    results = {"success": 0, "errors": 0}
    for page_data in pages_data:
        result = notion_request("POST", "/pages", page_data)
        if "error" in result:
            results["errors"] += 1
        else:
            results["success"] += 1
    return results

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    # Get total count
    total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
    print(f"Total leads in DB: {total}")

    # Get existing count in Notion
    existing = conn.execute("SELECT COUNT(*) FROM leads WHERE email != ''").fetchone()[0]
    print(f"Leads with email: {existing}")

    # Load leads ordered by score
    leads = conn.execute("""
        SELECT company, email, phone, website, category, social_lead_score,
               facebook_followers, twitter_followers, facebook_url, twitter_url,
               gmb_url, keyword
        FROM leads
        WHERE email != '' OR phone != ''
        ORDER BY
            CASE social_lead_score
                WHEN 'HOT' THEN 1
                WHEN 'Great' THEN 2
                WHEN 'Good' THEN 3
                ELSE 4
            END,
            facebook_followers DESC
    """).fetchall()
    conn.close()

    leads = [dict(l) for l in leads]
    print(f"Leads to import: {len(leads)}")

    # Batch import
    batch_size = 10
    total_success = 0
    total_errors = 0

    for i in range(0, len(leads), batch_size):
        batch = leads[i:i+batch_size]
        pages = []
        for lead in batch:
            props = row_to_notion(lead)
            pages.append({
                "parent": {"database_id": NOTION_DB_ID},
                "properties": props
            })

        results = batch_create_pages(pages)
        total_success += results["success"]
        total_errors += results["errors"]

        if (i // batch_size) % 10 == 0:
            print(f"  Progress: {min(i+batch_size, len(leads))}/{len(leads)} | Success: {total_success} | Errors: {total_errors}")

        # Rate limit: Notion allows ~3 requests/second
        time.sleep(0.4)

    print(f"\n✅ Import complete!")
    print(f"  Total: {len(leads)}")
    print(f"  Success: {total_success}")
    print(f"  Errors: {total_errors}")

if __name__ == "__main__":
    main()
