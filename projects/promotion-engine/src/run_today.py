"""
Promotion engine runner for 2026-06-29.
Generates images, uploads to GitHub, schedules via Ocaya API.
"""
import json
import os
import sys
import time
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

# Setup paths
SCRIPT_DIR = Path(__file__).resolve().parent
PROMOTION_DIR = SCRIPT_DIR.parent          # promotion-engine/
PROJECTS_DIR = PROMOTION_DIR.parent        # projects/
AIDENTIFY_DIR = PROJECTS_DIR.parent        # AgentsFactory-marketplace/

PROJECTS_FILE = AIDENTIFY_DIR / "docs" / "data" / "projects.json"
POSTED_FILE = SCRIPT_DIR / "output" / "posted_projects.json"
IMAGE_PIPELINE_SRC = PROJECTS_DIR / "image-pipeline" / "src"

sys.path.insert(0, str(IMAGE_PIPELINE_SRC))

from image_gen import generate_social_image
from github_uploader import upload_image

# Ocaya config
OCAYA_KEY = open(r"C:\tmp\ocoya_key.txt").read().strip()
OCAYA_BASE = "https://www.app.ocaya.com/api/_public/v1"
WORKSPACE_ID = "clapmus480dwb5vzyghnv5dku"

PROFILES = {
    "twitter": "cmdftz3un00187n0rrzbjc8o4",
    "linkedin": "cll7ytoyz002wl70fnxk0tjwr",
    "instagram": "cmdftzne6005l1hrgeacfi8sx",
    "facebook": "cmdftypmk005e1hrg1b7ow01b",
}

# IST posting times (converted to UTC)
# IST = UTC+5:30
# 8:00 AM IST = 02:30 UTC
# 9:00 AM IST = 03:30 UTC
# 10:00 AM IST = 04:30 UTC
# 11:00 AM IST = 05:30 UTC
POST_TIMES_IST = {
    "linkedin": 8,
    "twitter": 9,
    "instagram": 10,
    "facebook": 11,
}

MARKETPLACE_URL = "https://phanindraintelligenzit-afk.github.io/AgentsFactory/marketplace.html"


def ist_to_utc_schedule(hour_ist: int) -> str:
    """Convert IST hour to UTC ISO timestamp for tomorrow if time already passed."""
    now_utc = datetime.now(timezone.utc)
    ist_offset = timedelta(hours=5, minutes=30)
    now_ist = now_utc + ist_offset
    
    # Schedule for today if time hasn't passed, else tomorrow
    target_ist = now_ist.replace(hour=hour_ist, minute=0, second=0, microsecond=0)
    if target_ist <= now_ist:
        target_ist += timedelta(days=1)
    
    target_utc = target_ist - ist_offset
    return target_utc.strftime("%Y-%m-%dT%H:%M:%SZ")


def ocaya_schedule_post(caption: str, profile_ids: list, scheduled_at: str, media_urls: list = None) -> dict:
    """Schedule a post via Ocaya API."""
    params = {"workspaceId": WORKSPACE_ID}
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
    
    try:
        resp = urllib.request.urlopen(req, timeout=30)
        result = json.loads(resp.read().decode())
        return result
    except Exception as e:
        return {"error": str(e)}


def load_posted_projects() -> dict:
    """Load posted projects tracking."""
    if POSTED_FILE.exists():
        with open(POSTED_FILE) as f:
            return json.load(f)
    return {"posted": [], "last_run": None}


def save_posted_projects(data: dict):
    """Save posted projects tracking."""
    POSTED_FILE.parent.mkdir(exist_ok=True)
    with open(POSTED_FILE, "w") as f:
        json.dump(data, f, indent=2)


def generate_caption(project: dict, platform: str) -> str:
    """Generate a story-driven caption for a project."""
    name = project["name"]
    desc = project.get("description", "")
    github_url = project.get("github_url", "")
    
    # Short description (first sentence, max 100 chars)
    short_desc = desc.split(".")[0][:100]
    
    if platform == "twitter":
        # Max 280 chars
        caption = f"Just built and published: {name}\n\n{short_desc}\n\nLive: {github_url}\nMarketplace: {MARKETPLACE_URL}\n\nBuilt autonomously by the AgentsFactory agent swarm."
        if len(caption) > 280:
            # Truncate description
            available = 280 - len(f"Just built and published: {name}\n\n\nLive: {github_url}\nMarketplace: {MARKETPLACE_URL}\n\nBuilt autonomously by the AgentsFactory agent swarm.")
            short_desc = short_desc[:available-3] + "..."
            caption = f"Just built and published: {name}\n\n{short_desc}\n\nLive: {github_url}\nMarketplace: {MARKETPLACE_URL}\n\nBuilt autonomously by the AgentsFactory agent swarm."
        return caption
    
    elif platform == "linkedin":
        # Professional, story-driven
        agents = project.get("agents", project.get("agents_list", []))
        agent_count = len(agents) if isinstance(agents, list) else agents
        
        caption = f"Just shipped a new AI agent project: {name}\n\n{short_desc}.\n\nThis is a {agent_count}-agent multi-agent system built by our autonomous agent swarm. Each agent handles a specific part of the workflow — from intake to output.\n\nOpen source on GitHub: {github_url}\nBrowse all projects: {MARKETPLACE_URL}\n\nBuilding AI agents that solve real business problems."
        return caption
    
    elif platform == "instagram":
        caption = f"New build: {name}\n\n{short_desc}.\n\nBuilt by AI agents, for humans.\n\nLink in bio → {MARKETPLACE_URL}"
        return caption
    
    elif platform == "facebook":
        caption = f"Just published a new AI agent project to the AgentsFactory marketplace!\n\n{name} — {short_desc}.\n\nBuilt autonomously by our multi-agent swarm. Check it out:\n{github_url}\n\nExplore all projects: {MARKETPLACE_URL}"
        return caption
    
    return f"New project: {name}\n{github_url}"


def main():
    print("=" * 60)
    print("AgentsFactory Promotion Engine — 2026-06-29")
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
    
    # Process each unposted project
    results = []
    newly_posted = []
    
    for project in unposted:
        project_id = project["id"]
        project_name = project["name"]
        short_desc = project.get("description", "").split(".")[0][:80]
        
        print(f"\n{'─' * 50}")
        print(f"Processing: {project_name}")
        print(f"{'─' * 50}")
        
        # Step 1: Generate images for all platforms
        print("  Generating images...")
        image_paths = {}
        for platform in ["twitter", "linkedin", "instagram", "facebook"]:
            try:
                path = generate_social_image(
                    project_name=project_name,
                    description=short_desc,
                    platform=platform,
                )
                image_paths[platform] = path
                print(f"    ✅ {platform}: {os.path.basename(path)}")
            except Exception as e:
                print(f"    ❌ {platform}: {e}")
        
        # Step 2: Upload images to GitHub
        print("  Uploading images to GitHub...")
        image_urls = {}
        for platform, path in image_paths.items():
            try:
                url = upload_image(path)
                image_urls[platform] = url
                print(f"    ✅ {platform}: {url}")
            except Exception as e:
                print(f"    ❌ {platform}: {e}")
        
        # Step 3: Schedule posts per platform
        print("  Scheduling posts via Ocaya...")
        project_results = {"project_id": project_id, "name": project_name, "posts": []}
        
        for platform, profile_id in PROFILES.items():
            # Instagram requires image
            if platform == "instagram" and platform not in image_urls:
                print(f"    ⚠️  {platform}: Skipped (no image)")
                continue
            
            # Generate caption
            caption = generate_caption(project, platform)
            
            # Get schedule time
            hour_ist = POST_TIMES_IST[platform]
            scheduled_at = ist_to_utc_schedule(hour_ist)
            
            # Get media URL if available
            media_urls = [image_urls[platform]] if platform in image_urls else None
            
            # Schedule
            result = ocaya_schedule_post(
                caption=caption,
                profile_ids=[profile_id],
                scheduled_at=scheduled_at,
                media_urls=media_urls,
            )
            
            if "error" in result:
                print(f"    ❌ {platform}: {result['error']}")
            else:
                print(f"    ✅ {platform}: Scheduled for {scheduled_at} (postGroupId: {result.get('postGroupId', 'N/A')})")
            
            project_results["posts"].append({
                "platform": platform,
                "scheduled_at": scheduled_at,
                "result": result,
            })
            
            # Small delay between API calls
            time.sleep(1)
        
        results.append(project_results)
        newly_posted.append(project_id)
    
    # Step 4: Update posted tracking
    print(f"\n{'=' * 60}")
    print("Updating posted projects tracking...")
    
    all_posted = list(already_posted) + newly_posted
    save_posted_projects({
        "posted": all_posted,
        "last_run": datetime.now(timezone.utc).isoformat(),
    })
    print(f"  Total posted now: {len(all_posted)}")
    
    # Save results
    results_file = Path(__file__).resolve().parent / "output" / f"promotion_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2)
    print(f"  Results saved to: {results_file}")
    
    # Summary
    print(f"\n{'=' * 60}")
    print("SUMMARY")
    print(f"{'=' * 60}")
    print(f"Projects promoted: {len(newly_posted)}")
    for pid in newly_posted:
        name = next((p["name"] for p in unposted if p["id"] == pid), pid)
        print(f"  ✅ {name}")
    print(f"\nAll posts scheduled for tomorrow (IST):")
    print(f"  LinkedIn: 8:00 AM | Twitter: 9:00 AM | Instagram: 10:00 AM | Facebook: 11:00 AM")
    print(f"\nNote: Posts are created as DRAFT in Ocaya and will auto-publish at scheduled time.")


if __name__ == "__main__":
    main()
