"""Check Notion DB schema and fix lead sync."""
import os, json, urllib.request, urllib.error, sqlite3

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

# Step 1: Get DB schema
print("=== Notion DB Schema ===")
db = notion_req("GET", "/databases/" + NOTION_DB_ID)
if "error" in db:
    print("Error:", db)
    exit(1)

prop_types = {}
for name, prop in db["properties"].items():
    ptype = prop["type"]
    details = ""
    if ptype == "select":
        opts = [o["name"] for o in prop.get("select", {}).get("options", [])]
        details = "options: " + str(opts)
    prop_types[name] = ptype
    print("  " + name + ": " + ptype + " " + details)

# Step 2: Fix DB - add missing properties
print("\n=== Adding missing properties ===")
updates = {}

# We need: Company (title), Email (email), Phone, Website, Category (select),
# Social Score (select: HOT/Great/Good/Poor), Lead Status (select),
# Facebook Followers, Twitter Followers, etc.

# Check what needs to be added
needed = {
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
}

for prop_name, prop_def in needed.items():
    if prop_name not in prop_types:
        updates[prop_name] = prop_def
        print("  Adding: " + prop_name)
    else:
        print("  Exists: " + prop_name)

# Rename 'Name' to handle company names - check if we can use 'Company' prop or use existing
# The existing 'Name' property is actually what we want for company name
# But we mapped it wrong - SQLite has 'company', Notion has 'Name'
# Actually looking at the schema: 'Company' (rich_text), 'Name' (title?)

# Check if 'Company' is rich_text (wrong) and needs to be title
# If there's a 'Name' property that IS the title, use that instead
has_title = False
title_prop = None
for name, ptype in prop_types.items():
    if name in db["properties"] and db["properties"][name].get("type") == "title":
        has_title = True
        title_prop = name
        break

print("\nTitle property: " + str(title_prop) + " (type: title)")
print("Company property type: " + prop_types.get("Company", "MISSING"))

# Update properties if needed
if updates:
    result = notion_req("PATCH", "/databases/" + NOTION_DB_ID, {"properties": updates})
    if "error" in result:
        print("Error updating DB:", result.get("message", "")[:300])
    else:
        print("DB properties updated!")

# Step 3: Test creating a single lead with correct mapping
print("\n=== Test creating a lead ===")
conn = sqlite3.connect("agentsfactory_metrics.db")
conn.row_factory = sqlite3.Row
lead = conn.execute("SELECT * FROM leads LIMIT 1").fetchone()
conn.close()

if lead:
    lead = dict(lead)
    # Build properties mapping to actual Notion schema
    properties = {}
    
    # Use 'Name' as title (since 'Company' is rich_text in this DB)
    # Or if 'Company' is the title prop, use that
    if title_prop == "Company":
        properties["Company"] = {"title": [{"text": {"content": str(lead.get("company", ""))[:200]}}]}
    elif title_prop == "Name":
        properties["Name"] = {"title": [{"text": {"content": str(lead.get("company", ""))[:200]}}]}
    elif title_prop:
        properties[title_prop] = {"title": [{"text": {"content": str(lead.get("company", ""))[:200]}}]}
    
    if lead.get("email"):
        properties["Email"] = {"email": lead["email"]}
    if lead.get("phone"):
        properties["Phone"] = {"phone_number": lead["phone"]}
    if lead.get("website"):
        properties["Website"] = {"url": lead["website"]}
    # Skip Category - not in DB
    # Use Score property for social_lead_score
    score = lead.get("social_lead_score", "")
    if score in ("HOT", "Great", "Good", "Poor"):
        properties["Social Score"] = {"select": {"name": score}}
    elif score:
        properties["Score"] = {"select": {"name": score}}
    if lead.get("facebook_followers"):
        properties["Facebook Followers"] = {"number": lead["facebook_followers"]}
    if lead.get("twitter_followers"):
        properties["Twitter Followers"] = {"number": lead["twitter_followers"]}
    
    print("Payload properties: " + str(list(properties.keys())))
    
    result = notion_req("POST", "/pages", {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": properties
    })
    if "error" in result:
        print("Error:", result.get("message", "")[:400])
    else:
        print("SUCCESS! Page ID: " + result.get("id", "?"))
