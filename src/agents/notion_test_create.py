"""Test Notion lead creation with fixed schema."""
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

# Test with first lead
conn = sqlite3.connect("agentsfactory_metrics.db")
conn.row_factory = sqlite3.Row
lead = conn.execute("SELECT * FROM leads LIMIT 1").fetchone()
conn.close()

if lead:
    lead = dict(lead)
    print("Lead:", lead["company"])
    
    properties = {
        "Name": {"title": [{"text": {"content": str(lead.get("company", ""))[:200]}}]},
        "Company": {"rich_text": [{"text": {"content": str(lead.get("company", ""))[:200]}}]},
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
    
    result = notion_req("POST", "/pages", {
        "parent": {"database_id": NOTION_DB_ID},
        "properties": properties
    })
    if "error" in result:
        print("Error:", result.get("message", "")[:400])
    else:
        print("SUCCESS! Page ID:", result.get("id"))
