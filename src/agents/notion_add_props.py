"""Add missing properties to Notion DB."""
import os, json, urllib.request, urllib.error

def get_notion_key():
    config_path = os.path.join(os.path.expanduser("~"), ".hermes", ".env")
    with open(config_path) as f:
        for line in f:
            if "NOTION_API_KEY" in line.strip() and "=" in line:
                val = line.strip().split("=", 1)[1].strip()
                if val and not val.startswith("#"):
                    return val
    return ""

key = get_notion_key()
NOTION_DB_ID = "37d4baec-8165-81fe-ab68-d2c3c347589d"

def notion_req(method, path, data=None):
    url = "https://api.notion.com/v1" + path
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header("Authorization", "Bearer " + key)
    req.add_header("Content-Type", "application/json")
    req.add_header("Notion-Version", "2022-06-28")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": True, "status": e.code, "message": e.read().decode()}

# Add missing properties
updates = {
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
    "Category": {"select": {}},
    "Website": {"url": {}},
    "Facebook Followers": {"number": {}},
    "Twitter Followers": {"number": {}},
    "Facebook URL": {"url": {}},
    "Twitter URL": {"url": {}},
    "GMB URL": {"url": {}},
    "Keyword": {"rich_text": {}},
}

print("Adding properties...")
result = notion_req("PATCH", "/databases/" + NOTION_DB_ID, {"properties": updates})
if "error" in result:
    print("Error:", result.get("message", "")[:300])
else:
    print("Success! Properties added.")
