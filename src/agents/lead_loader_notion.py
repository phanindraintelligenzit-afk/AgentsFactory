"""
Load leads from SQLite database into Notion.
"""
import os
import sys
import json
import sqlite3
import urllib.request
import urllib.error
from datetime import datetime

NOTION_KEY = "ntn_203159...laEt"  # Will be read from env
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "..", "..", "agentsfactory_metrics.db")
# Fix path
DB_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agentsfactory_metrics.db"))

def get_notion_key():
    """Read Notion API key from hermes config."""
    config_path = os.path.join(os.path.expanduser("~"), ".hermes", ".env")
    if os.path.exists(config_path):
        with open(config_path) as f:
            for line in f:
                if line.strip().startswith("NOTION_API_KEY="):
                    return line.strip().split("=", 1)[1].strip()
    return os.environ.get("NOTION_API_KEY", "")


def notion_request(method, path, data=None):
    """Make a Notion API request."""
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


def find_leads_database():
    """Find the leads database in the AgentsFactory Notion workspace."""
    # Search for databases
    result = notion_request("POST", "/search", {
        "query": "Leads",
        "filter": {"value": "database", "property": "object"}
    })
    if "results" in result:
        for db in result["results"]:
            print(f"Found database: {db.get('title', [{}])[0].get('plain_text', 'Unknown')} | ID: {db['id']}")
        return result["results"]
    return []


def create_leads_database(parent_page_id="37d4baec-8165-8126-ae73-e56e6d5d235d"):
    """Create a leads database in Notion."""
    result = notion_request("POST", "/databases", {
        "parent": {"page_id": parent_page_id},
        "title": [{"text": {"content": "Leads"}}],
        "properties": {
            "Company": {"title": {}},
            "Email": {"email": {}},
            "Phone": {"phone_number": {}},
            "Website": {"url": {}},
            "Category": {"select": {}},
            "Lead Status": {"select": {"options": [
                {"name": "New", "color": "blue"},
                {"name": "Contacted", "color": "yellow"},
                {"name": "Qualified", "color": "green"},
                {"name": "Converted", "color": "purple"},
                {"name": "Lost", "color": "red"},
            ]}},
            "Social Score": {"select": {"options": [
                {"name": "HOT", "color": "red"},
                {"name": "Great", "color": "orange"},
                {"name": "Good", "color": "yellow"},
                {"name": "Poor", "color": "gray"},
            ]}},
            "Facebook Followers": {"number": {}},
            "Twitter Followers": {"number": {}},
            "Facebook URL": {"url": {}},
            "Twitter URL": {"url": {}},
            "GMB URL": {"url": {}},
            "Keyword": {"rich_text": {}},
            "Created": {"created_time": {}},
        }
    })
    return result


def add_lead_to_notion(db_id, lead):
    """Add a single lead to Notion database."""
    properties = {
        "Company": {"title": [{"text": {"content": lead["company"][:200]}}]},
    }
    if lead.get("email"):
        properties["Email"] = {"email": lead["email"]}
    if lead.get("phone"):
        properties["Phone"] = {"phone_number": lead["phone"]}
    if lead.get("website"):
        properties["Website"] = {"url": lead["website"]}
    if lead.get("category"):
        properties["Category"] = {"select": {"name": lead["category"][:100]}}
    if lead.get("social_lead_score") in ("HOT", "Great", "Good", "Poor"):
        properties["Social Score"] = {"select": {"name": lead["social_lead_score"]}}
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
        properties["Keyword"] = {"rich_text": [{"text": {"content": lead["keyword"][:200]}}]}

    result = notion_request("POST", "/pages", {
        "parent": {"database_id": db_id},
        "properties": properties
    })
    return result


def load_leads_to_notion(db_id, batch_size=50):
    """Load all leads from SQLite to Notion in batches."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    leads = conn.execute("""
        SELECT company, email, phone, website, category, social_lead_score,
               facebook_followers, twitter_followers, facebook_url, twitter_url,
               gmb_url, keyword
        FROM leads ORDER BY
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
    total = len(leads)
    success = 0
    errors = 0

    for i in range(0, total, batch_size):
        batch = leads[i:i+batch_size]
        for lead in batch:
            result = add_lead_to_notion(db_id, lead)
            if "error" in result:
                errors += 1
            else:
                success += 1
        print(f"  Progress: {min(i+batch_size, total)}/{total} | Success: {success} | Errors: {errors}")

    return {"total": total, "success": success, "errors": errors}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load leads to Notion")
    parser.add_argument("--find-db", action="store_true", help="Find existing leads database")
    parser.add_argument("--create-db", action="store_true", help="Create leads database")
    parser.add_argument("--load", action="store_true", help="Load leads to Notion")
    parser.add_argument("--db-id", type=str, help="Notion database ID")
    args = parser.parse_args()

    if args.find_db:
        find_leads_database()
    elif args.create_db:
        result = create_leads_database()
        print(json.dumps(result, indent=2))
    elif args.load and args.db_id:
        results = load_leads_to_notion(args.db_id)
        print(json.dumps(results, indent=2))
    else:
        print("Usage: --find-db | --create-db | --load --db-id <id>")
