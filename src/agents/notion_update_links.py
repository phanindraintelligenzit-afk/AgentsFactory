"""Update Notion Quick Links page with all important links."""
import os, json, urllib.request, urllib.error

def get_notion_key():
    config_path = os.path.join(os.path.expanduser("~"), ".hermes", ".env")
    with open(config_path) as f:
        for line in f:
            if line.strip().startswith("NOTION_API_KEY="):
                return line.strip().split("=", 1)[1].strip()

key = get_notion_key()
QUICK_LINKS_PAGE_ID = "37d4baec-8165-81a7-a0e1-de4593503d35"
PARENT_PAGE_ID = "37d4baec-8165-8126-ae73-e56e6d5d235d"

def notion_req(method, path, data=None):
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

# Step 1: Find all databases in the workspace
print("=== Finding all Notion databases ===")
search = notion_req("POST", "/search", {
    "query": "",
    "filter": {"value": "database", "property": "object"}
})
databases = {}
for db in search.get("results", []):
    title = "Unknown"
    if db.get("title"):
        title = db["title"][0].get("plain_text", "Unknown")
    db_id = db["id"]
    databases[title] = db_id
    print(f"  {title}: {db_id}")

# Step 2: Get child pages under parent
print("\n=== Finding child pages ===")
children = notion_req("GET", f"/blocks/{PARENT_PAGE_ID}/children?page_size=100")
pages = {}
for block in children.get("results", []):
    if block.get("type") == "child_page":
        title = block.get("child_page", {}).get("title", "Unknown")
        pages[title] = block["id"]
        print(f"  {title}: {block['id']}")

# Step 3: Build links content dynamically
blocks = [
    {
        "object": "block",
        "type": "heading_1",
        "heading_1": {"rich_text": [{"text": {"content": "AgentsFactory - All Links"}}]}
    },
    {"object": "block", "type": "divider", "divider": {}},
]

# Websites section
blocks.append({
    "object": "block",
    "type": "heading_2",
    "heading_2": {"rich_text": [{"text": {"content": "Websites & Landing Pages"}}]}
})
blocks.append({"object": "block", "type": "bookmark", "bookmark": {"url": "https://phanindraintelligenzit-afk.github.io/AgentsFactory/landing/"}})
blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Landing page with lead capture form (Formspree)"}}]}})
blocks.append({"object": "block", "type": "divider", "divider": {}})

# Social Media
blocks.append({
    "object": "block",
    "type": "heading_2",
    "heading_2": {"rich_text": [{"text": {"content": "Social Media Profiles"}}]}
})
blocks.append({"object": "block", "type": "bookmark", "bookmark": {"url": "https://www.linkedin.com/in/phanindramalladi/"}})
blocks.append({"object": "block", "type": "bookmark", "bookmark": {"url": "https://twitter.com/xAidentify"}})
blocks.append({"object": "block", "type": "bookmark", "bookmark": {"url": "https://www.instagram.com/ai.aidentify/"}})
blocks.append({"object": "block", "type": "bookmark", "bookmark": {"url": "https://www.facebook.com/Aidentify"}})
blocks.append({"object": "block", "type": "divider", "divider": {}})

# Notion Databases
blocks.append({
    "object": "block",
    "type": "heading_2",
    "heading_2": {"rich_text": [{"text": {"content": "Notion Databases"}}]}
})
blocks.append({"object": "block", "type": "bookmark", "bookmark": {"url": f"https://notion.so/{PARENT_PAGE_ID.replace('-', '')}"}})
blocks.append({"object": "block", "type": "paragraph", "paragraph": {"rich_text": [{"text": {"content": "Workspace parent page"}}]}})

# Add link_to_page for each database found
for title, db_id in sorted(databases.items()):
    blocks.append({"object": "block", "type": "paragraph", "paragraph": {
        "rich_text": [{"text": {"content": f"📁 {title}: "}, "annotations": {"bold": True}},
                     {"text": {"content": f"https://notion.so/{db_id.replace('-', '')}"}}]
    }})

blocks.append({"object": "block", "type": "divider", "divider": {}})

# Dashboard & Tools
blocks.append({
    "object": "block",
    "type": "heading_2",
    "heading_2": {"rich_text": [{"text": {"content": "Dashboard & Tools"}}]}
})
blocks.append({"object": "block", "type": "paragraph", "paragraph": {
    "rich_text": [{"text": {"content": "Streamlit Command Center (local): "}},
                 {"text": {"content": "http://localhost:8501"}, "annotations": {"code": True}}]
}})
blocks.append({"object": "block", "type": "paragraph", "paragraph": {
    "rich_text": [{"text": {"content": "Pages: Overview, Projects, Revenue, Leads, Content, Automations, AI Advice, Kanban"}}]
}})
blocks.append({"object": "block", "type": "divider", "divider": {}})

# GitHub
blocks.append({
    "object": "block",
    "type": "heading_2",
    "heading_2": {"rich_text": [{"text": {"content": "GitHub Repository"}}]}
})
blocks.append({"object": "block", "type": "bookmark", "bookmark": {"url": "https://github.com/phanindraintelligenzit-afk/AgentsFactory"}})
blocks.append({"object": "block", "type": "paragraph", "paragraph": {
    "rich_text": [{"text": {"content": "Full source: agents, dashboard, docs, landing page. Cloneable with setup/bootstrap.sh"}}]
}})
blocks.append({"object": "block", "type": "divider", "divider": {}})

# External Tools
blocks.append({
    "object": "block",
    "type": "heading_2",
    "heading_2": {"rich_text": [{"text": {"content": "External Tools & Accounts"}}]}
})
blocks.append({"object": "block", "type": "bookmark", "bookmark": {"url": "https://app.ocoya.com"}})
blocks.append({"object": "block", "type": "paragraph", "paragraph": {
    "rich_text": [{"text": {"content": "Ocoya - Social media scheduling (LinkedIn, X, Instagram, Facebook)"}}]
}})
blocks.append({"object": "block", "type": "bookmark", "bookmark": {"url": "https://formspree.io/f/xlgkpzeo"}})
blocks.append({"object": "block", "type": "paragraph", "paragraph": {
    "rich_text": [{"text": {"content": "Formspree - Lead capture form endpoint"}}]
}})

# Step 4: Clear and update the Quick Links page
print(f"\n=== Updating Quick Links page ===")
page = notion_req("GET", f"/pages/{QUICK_LINKS_PAGE_ID}")
if "error" in page:
    print(f"Error: {page}")
    exit(1)

# Clear existing blocks
existing = notion_req("GET", f"/blocks/{QUICK_LINKS_PAGE_ID}/children?page_size=100")
deleted = 0
for block in existing.get("results", []):
    r = notion_req("DELETE", f"/blocks/{block['id']}")
    if "error" not in r:
        deleted += 1
print(f"Cleared {deleted} existing blocks")

# Add new blocks in batches of 100
for i in range(0, len(blocks), 100):
    batch = blocks[i:i+100]
    result = notion_req("PATCH", f"/blocks/{QUICK_LINKS_PAGE_ID}/children", {"children": batch})
    if "error" in result:
        print(f"Error adding batch {i}: {result}")
    else:
        print(f"Added blocks {i+1}-{min(i+100, len(blocks))}")

# Update title
notion_req("PATCH", f"/pages/{QUICK_LINKS_PAGE_ID}", {
    "properties": {"title": {"title": [{"text": {"content": "AgentsFactory - All Links"}}]}}
})

print(f"\n✅ Quick Links page updated!")
print(f"View at: https://notion.so/{QUICK_LINKS_PAGE_ID.replace('-', '')}")
print(f"\nDatabases linked: {', '.join(sorted(databases.keys()))}")
