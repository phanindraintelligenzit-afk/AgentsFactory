"""Bulk sync leads to Notion - corrected schema mapping."""
import os, json, sqlite3, time, urllib.request, urllib.error

def get_notion_key():
    cp = os.path.join(os.path.expanduser("~"), ".hermes", ".env")
    with open(cp) as f:
        for line in f:
            if "NOTION_API_KEY" in line.strip() and "=" in line:
                v = line.strip().split("=", 1)[1].strip()
                if v and not v.startswith("#"):
                    return v
    return ""

KEY = get_notion_key()
DB_ID = "37d4baec-8165-81fe-ab68-d2c3c347589d"
DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agentsfactory_metrics.db")
DB_PATH = os.path.normpath(DB_PATH)

def notion_post(path, data):
    url = "https://api.notion.com/v1" + path
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, method="POST")
    req.add_header("Authorization", "Bearer " + KEY)
    req.add_header("Content-Type", "application/json")
    req.add_header("Notion-Version", "2022-06-28")
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()), None
    except urllib.error.HTTPError as e:
        return None, json.loads(e.read().decode())

def build_props(lead):
    p = {
        "Name": {"title": [{"text": {"content": str(lead.get("company",""))[:200]}}]},
    }
    if lead.get("email"): p["Email"] = {"email": lead["email"]}
    if lead.get("phone"): p["Phone"] = {"phone_number": lead["phone"]}
    if lead.get("website"): p["Website"] = {"url": lead["website"]}
    if lead.get("category"): p["Category"] = {"select": {"name": str(lead["category"])[:100]}}
    s = lead.get("social_lead_score","")
    if s in ("HOT","Great","Good","Poor"): p["Social Score"] = {"select": {"name": s}}
    if lead.get("facebook_followers"): p["Facebook Followers"] = {"number": lead["facebook_followers"]}
    if lead.get("twitter_followers"): p["Twitter Followers"] = {"number": lead["twitter_followers"]}
    if lead.get("facebook_url"): p["Facebook URL"] = {"url": lead["facebook_url"]}
    if lead.get("twitter_url"): p["Twitter URL"] = {"url": lead["twitter_url"]}
    if lead.get("gmb_url"): p["GMB URL"] = {"url": lead["gmb_url"]}
    if lead.get("keyword"): p["Keyword"] = {"rich_text": [{"text": {"content": str(lead["keyword"])[:200]}}]}
    return p

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
leads = conn.execute("SELECT * FROM leads ORDER BY CASE social_lead_score WHEN 'HOT' THEN 1 WHEN 'Great' THEN 2 WHEN 'Good' THEN 3 ELSE 4 END, facebook_followers DESC").fetchall()
leads = [dict(l) for l in leads]
total = len(leads)
print(f"Syncing {total} leads...")

ok = 0; err = 0; backoff = 1.0
for i, lead in enumerate(leads):
    props = build_props(lead)
    result, error = notion_post("/pages", {"parent": {"database_id": DB_ID}, "properties": props})
    if error:
        if error.get("status") == 429:
            time.sleep(backoff); backoff = min(backoff * 2, 30)
            result, error = notion_post("/pages", {"parent": {"database_id": DB_ID}, "properties": props})
        if error:
            err += 1
            if err <= 3: print(f"  Err {i}: {error.get('message','?')[:120]}")
        else: ok += 1; backoff = 1.0
    else: ok += 1; backoff = 1.0
    conn.execute("UPDATE leads SET notion_synced=1 WHERE id=?", (lead["id"],)); conn.commit()
    if (i+1) % 50 == 0:
        print(f"  {i+1}/{total} | OK:{ok} Err:{err}"); time.sleep(0.5)
    else: time.sleep(0.3)

print(f"\nDone! OK:{ok} Err:{err} Total:{total}")
conn.close()
