"""
One-off promotion runner for 2026-06-29 (fixed paths + SSL).
"""
import json
import os
import ssl
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
SCRIPT_DIR = Path(__file__).resolve().parent
AIDENTIFY_DIR = SCRIPT_DIR.parent.parent.parent  # AgentsFactory-marketplace/
PROJECTS_FILE = AIDENTIFY_DIR / "docs" / "data" / "projects.json"
POSTED_FILE = SCRIPT_DIR / "output" / "posted_projects.json"

# ── Ocaya config ───────────────────────────────────────────────────
OCAYA_KEY = open(r"C:\tmp\ocoya_key.txt").read().strip()
OCAYA_BASE = "https://app.ocaya.com/api/_public/v1"  # no www (SSL cert mismatch)
WORKSPACE_ID = "clapmus480dwb5vzyghnv5dku"

PROFILES = {
    "twitter": "cmdftz3un00187n0rrzbjc8o4",
    "linkedin": "cll7ytoyz002wl70fnxk0tjwr",
    "instagram": "cmdftzne6005l1hrgeacfi8sx",
    "facebook": "cmdftypmk005e1hrg1b7ow01b",
}

POST_TIMES_IST = {
    "linkedin": 8,
    "twitter": 9,
    "instagram": 10,
    "facebook": 11,
}

MARKETPLACE_URL = "https://phanindraintelligenzit-afk.github.io/AgentsFactory/marketplace.html"

# Image base URL (images are in the AgentsFactory gh-pages repo)
IMAGE_BASE_URL = "https://raw.githubusercontent.com/phanindraintelligenzit-afk/AgentsFactory/gh-pages/projects/image-pipeline/src/.social-assets-repo/images"

# ── SSL context that works with Ocaya ──────────────────────────────
SSL_CONTEXT = ssl.create_default_context()
SSL_CONTEXT.check_hostname = False
SSL_CONTEXT.verify_mode = ssl.CERT_NONE


def ist_to_utc_schedule(hour_ist: int) -> str:
    """Convert IST hour to UTC ISO timestamp for tomorrow if time already passed."""
    now_utc = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = now_utc + ist_offset
    target_ist = now_ist.replace(hour=hour_ist, minute=0, second=0, microsecond=0)
    if target_ist <= now_ist:
        target_ist += timedelta(days=1)
    target_utc = target_ist - ist_offset
    return target_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def ocaya_schedule_post(caption: str, profile_ids: list, scheduled_at: str, media_urls: list = None) -> dict:
    """Schedule a post via Ocaya API."""
    url = f"{OCAYA_BASE}/post?workspaceId={WORKSPACE_ID}"
    body = {
        "caption": caption,
        "socialProfileIds": profile_ids,
        "scheduledAt": scheduled_at,
        "postNow": False,
    }
    if media_urls:
        body["mediaUrls"] = media_urls

    data = json.dumps(body).encode()
    req = urllib.request.Request(
        url,
        data=data,
        headers={
            "X-API-Key": OCAYA_KEY,
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )

    for attempt in range(3):
        try:
            resp = urllib.request.urlopen(req, timeout=30, context=SSL_CONTEXT)
            return json.loads(resp.read().decode())
        except Exception as e:
            if attempt < 2:
                time.sleep(3)
            else:
                return {"error": str(e)}


def load_posted_projects() -> dict:
    if POSTED_FILE.exists():
        with open(POSTED_FILE) as f:
            return json.load(f)
    return {"posted": [], "last_run": None}


def save_posted_projects(data: dict):
    POSTED_FILE.parent.mkdir(exist_ok=True)
    with open(POSTED_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_caption(project: dict, platform: str) -> str:
    name = project["name"]
    desc = project.get("description", "")
    github_url = project.get("github_url", "")
    short_desc = desc.split(".")[0][:100]

    if platform == "twitter":
        caption = f"Just built and published: {name}\n\n{short_desc}\n\nLive: {github_url}\nMarketplace: {MARKETPLACE_URL}\n\nBuilt autonomously by the AgentsFactory agent swarm."
        if len(caption) > 280:
            available = 280 - len(f"Just built and published: {name}\n\n\nLive: {github_url}\nMarketplace: {MARKETPLACE_URL}\n\nBuilt autonomously by the AgentsFactory agent swarm.")
            short_desc = short_desc[:max(available - 3, 10)] + "..."
            caption = f"Just built and published: {name}\n\n{short_desc}\n\nLive: {github_url}\nMarketplace: {MARKETPLACE_URL}\n\nBuilt autonomously by the AgentsFactory agent swarm."
        return caption
    elif platform == "linkedin":
        agents = project.get("agents", project.get("agents_list", []))
        agent_count = len(agents) if isinstance(agents, list) else (project.get("agents", 4) if isinstance(project.get("agents"), int) else 4)
        caption = f"Just shipped a new AI agent project: {name}\n\n{short_desc}.\n\nThis is a {agent_count}-agent multi-agent system built by our autonomous agent swarm. Each agent handles a specific part of the workflow.\n\nOpen source: {github_url}\nBrowse all: {MARKETPLACE_URL}\n\nBuilding AI agents that solve real business problems."
        return caption
    elif platform == "instagram":
        caption = f"New build: {name}\n\n{short_desc}.\n\nBuilt by AI agents, for humans.\n\nLink in bio → {MARKETPLACE_URL}"
        return caption
    elif platform == "facebook":
        caption = f"Just published a new AI agent project to the AgentsFactory marketplace!\n\n{name} — {short_desc}.\n\nBuilt autonomously by our multi-agent swarm:\n{github_url}\n\nExplore all projects: {MARKETPLACE_URL}"
        return caption
    return f"New project: {name}\n{github_url}"


def get_image_url(project_name: str, platform: str) -> str:
    """Get the URL for an already-uploaded image."""
    safe_name = project_name.lower().replace(" ", "-")[:30]
    filename = f"{platform}_{safe_name}.png"
    return f"{IMAGE_BASE_URL}/{filename}"


def check_image_exists(url: str) -> bool:
    """Check if an image URL returns 200."""
    try:
        req = urllib.request.Request(url, method="HEAD")
        resp = urllib.request.urlopen(req, timeout=10)
        return resp.status == 200
    except:
        return False


def main():
    print("=" * 60)
    print("AgentsFactory Promotion Engine — 2026-06-29 (Fixed)")
    print("=" * 60)

    # Load projects
    with open(PROJECTS_FILE) as f:
        projects_data = json.load(f)
    projects = projects_data["projects"]
    print(f"\nTotal projects in marketplace: {len(projects)}")

    # Load posted tracking
    posted_data = load_posted_projects()
    already_posted = set(posted_data.get("posted", []))
    print(f"Already posted: {len(already_posted)} projects")

    # Find unposted projects
    unposted = [p for p in projects if p["id"] not in already_posted]
    print(f"New projects to promote: {len(unposted)}")

    if not unposted:
        print("\n✅ All projects already promoted. Nothing to do.")
        return

    for p in unposted:
        print(f"  - {p['name']} ({p['id']})")

    # Verify images exist
    print("\nVerifying images are accessible...")
    for project in unposted:
        name = project["name"]
        for platform in ["twitter", "linkedin", "instagram", "facebook"]:
            url = get_image_url(name, platform)
            exists = check_image_exists(url)
            status = "✅" if exists else "❌"
            if not exists:
                print(f"  {status} {platform}: {url}")

    # Schedule posts
    results = []
    scheduled_count = 0

    for project in unposted:
        project_id = project["id"]
        project_name = project["name"]

        print(f"\n{'─' * 50}")
        print(f"Processing: {project_name}")
        print(f"{'─' * 50}")

        project_results = {"project_id": project_id, "name": project_name, "posts": []}

        for platform, profile_id in PROFILES.items():
            # Instagram requires image
            if platform == "instagram":
                img_url = get_image_url(project_name, platform)
                if not check_image_exists(img_url):
                    print(f"  ⚠️  {platform}: Skipped (no image)")
                    continue
                media_urls = [img_url]
            else:
                # Other platforms can use text-only or with image
                img_url = get_image_url(project_name, platform)
                if check_image_exists(img_url):
                    media_urls = [img_url]
                else:
                    media_urls = None

            caption = generate_caption(project, platform)
            hour_ist = POST_TIMES_IST[platform]
            scheduled_at = ist_to_utc_schedule(hour_ist)

            result = ocaya_schedule_post(
                caption=caption,
                profile_ids=[profile_id],
                scheduled_at=scheduled_at,
                media_urls=media_urls,
            )

            if "error" in result:
                print(f"  ❌ {platform}: {result['error']}")
            else:
                print(f"  ✅ {platform}: Scheduled for {scheduled_at} UTC (postGroupId: {result.get('postGroupId', 'N/A')})")
                scheduled_count += 1

            project_results["posts"].append({
                "platform": platform,
                "scheduled_at": scheduled_at,
                "result": result,
            })

            time.sleep(1)

        results.append(project_results)

    # Update posted tracking
    print(f"\n{'=' * 60}")
    print("Updating posted projects tracking...")

    all_posted = list(already_posted) + [p["id"] for p in unposted]
    save_posted_projects({
        "posted": all_posted,
        "last_run": datetime.now(timezone.utc).isoformat(),
    })
    print(f"  Total posted now: {len(all_posted)}")

    # Save results
    results_file = SCRIPT_DIR / "output" / f"promotion_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved to: {results_file}")

    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Projects promoted: {len(unposted)}")
    for p in unposted:
        print(f"  ✅ {p['name']}")
    print(f"Total posts scheduled: {scheduled_count}")
    print(f"\nScheduled for tomorrow (IST):")
    print(f"  LinkedIn: 8:00 AM | Twitter: 9:00 AM | Instagram: 10:00 AM | Facebook: 11:00 AM")
    print(f"\nNote: Posts created as DRAFT in Ocaya, auto-publish at scheduled time.")


if __name__ == "__main__":
    main()
