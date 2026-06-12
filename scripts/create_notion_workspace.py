#!/usr/bin/env python3
"""Create AgentsFactory Notion workspace databases."""

import json
import subprocess

PARENT_PAGE_ID = "37d4baec-8165-8126-ae73-e56e6d5d235d"

def get_api_key():
    with open(r"C:\Users\Admin\.hermes\.env") as f:
        for line in f:
            line = line.strip()
            if "NOTION_API_KEY" in line and "=" in line:
                return line.split("=", 1)[1].strip()
    raise ValueError("NOTION_API_KEY not found")

def create_database(api_key, title, description, properties):
    payload = {
        "parent": {"type": "page_id", "page_id": PARENT_PAGE_ID},
        "title": [{"text": {"content": title}}],
        "description": [{"text": {"content": description}}],
        "is_inline": False,
        "properties": properties,
    }
    cmd = [
        "curl", "-s", "-X", "POST",
        "https://api.notion.com/v1/databases",
        "-H", "Authorization: Bearer " + api_key,
        "-H", "Notion-Version: 2022-06-28",
        "-H", "Content-Type: application/json",
        "-d", json.dumps(payload),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    data = json.loads(result.stdout)
    db_id = data.get("id")
    if db_id:
        print(f"OK  {title} — {db_id}")
    else:
        print(f"FAIL {title} — {data}")
    return db_id

api_key = get_api_key()

# 1. Leads
create_database(api_key, "Leads", "All potential clients and prospects",
    {"Name": {"title": {}}, "Company": {"rich_text": {}}, "Email": {"email": {}},
     "Phone": {"phone_number": {}},
     "Source": {"select": {"options": [{"name": n} for n in ["inbound","outbound","referral","website","social","linkedin","twitter","reddit","google_maps"]]}},
     "Stage": {"select": {"options": [{"name": n} for n in ["new","contacted","qualified","proposal","negotiation","won","lost","nurture"]]}},
     "Score": {"number": {"format": "number"}},
     "Deal Value": {"number": {"format": "dollar"}},
     "Notes": {"rich_text": {}}, "Created": {"created_time": {}}})

# 2. Clients
create_database(api_key, "Clients", "Active and past clients",
    {"Name": {"title": {}},
     "Industry": {"select": {"options": [{"name": n} for n in ["e-commerce","saas","healthcare","local_business","agency","education","restaurant","other"]]}},
     "Contact Name": {"rich_text": {}}, "Email": {"email": {}}, "Phone": {"phone_number": {}},
     "Status": {"select": {"options": [{"name": n} for n in ["lead","active","paused","churned","founding"]]}},
     "Tier": {"select": {"options": [{"name": n} for n in ["starter","growth","scale","custom"]]}},
     "Deal Value": {"number": {"format": "dollar"}},
     "Notes": {"rich_text": {}}, "Created": {"created_time": {}}})

# 3. Projects
create_database(api_key, "Projects", "Client projects and internal builds",
    {"Name": {"title": {}}, "Description": {"rich_text": {}},
     "Status": {"select": {"options": [{"name": n} for n in ["planning","active","review","completed","paused","cancelled"]]}},
     "Tier": {"select": {"options": [{"name": n} for n in ["starter","growth","scale","custom"]]}},
     "Start Date": {"date": {}}, "Due Date": {"date": {}}, "Completed": {"date": {}},
     "Notes": {"rich_text": {}}, "Created": {"created_time": {}}})

# 4. Content Calendar
create_database(api_key, "Content Calendar", "Content pipeline",
    {"Title": {"title": {}},
     "Platform": {"select": {"options": [{"name": n} for n in ["linkedin","twitter","newsletter","youtube","blog","reddit"]]}},
     "Status": {"select": {"options": [{"name": n} for n in ["idea","draft","scheduled","published","repurposed"]]}},
     "Pillar": {"select": {"options": [{"name": n} for n in ["case_study","behind_scenes","tips_tutorial","social_proof","industry_insight","personal_story"]]}},
     "Scheduled Date": {"date": {}}, "Published Date": {"date": {}},
     "Engagement Score": {"number": {"format": "number"}},
     "Notes": {"rich_text": {}}, "Created": {"created_time": {}}})

# 5. Automation Health
create_database(api_key, "Automation Health", "Monitor all automations",
    {"Name": {"title": {}},
     "Status": {"select": {"options": [{"name": n} for n in ["running","paused","error","degraded","stopped"]]}},
     "Uptime %": {"number": {"format": "percent"}},
     "Success Count": {"number": {"format": "number"}},
     "Failure Count": {"number": {"format": "number"}},
     "Last Run": {"date": {}}, "Last Error": {"rich_text": {}},
     "Notes": {"rich_text": {}}, "Updated": {"last_edited_time": {}}})

# 6. Revenue
create_database(api_key, "Revenue", "All revenue entries",
    {"Description": {"title": {}},
     "Amount": {"number": {"format": "dollar"}},
     "Type": {"select": {"options": [{"name": n} for n in ["one_time","monthly_retainer","setup_fee","custom","early_bird"]]}},
     "Status": {"select": {"options": [{"name": n} for n in ["projected","confirmed","pending","paid","overdue","cancelled"]]}},
     "Date": {"date": {}}, "Notes": {"rich_text": {}}, "Created": {"created_time": {}}})

# 7. Agent Activity
create_database(api_key, "Agent Activity", "Log of all subagent actions",
    {"Action": {"title": {}},
     "Agent": {"select": {"options": [{"name": n} for n in ["Lead Finder","Outreach","Content Writer","LinkedIn","Builder","Monitor","Reporter","Phani","Hermes"]]}},
     "Target": {"rich_text": {}},
     "Status": {"select": {"options": [{"name": n} for n in ["completed","in_progress","failed","pending_review"]]}},
     "Details": {"rich_text": {}}, "Timestamp": {"created_time": {}}})

print("\nDone!")
