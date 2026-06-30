#!/usr/bin/env python3
"""
AIdentify Continuous Social Poster.

Reads the next content item from the content queue and schedules it via Ocoya API.
Designed to be called by cron every 2-3 hours during active posting window.

Usage:
    python3 scripts/social_poster_v2.py              # Post next queued item
    python3 scripts/social_poster_v2.py --dry-run    # Show what would post
    python3 scripts/social_poster_v2.py --generate   # Regenerate today's queue
    python3 scripts/social_poster_v2.py --status     # Show queue status
"""

import argparse
import json
import ssl
import sys
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
QUEUE_FILE = SCRIPT_DIR / "content_queue.json"

IST = timezone(timedelta(hours=5, minutes=30))

# Ocoya config
OCOYA_BASE = "https://www.app.ocoya.com/api/_public/v1"
OCOYA_KEY = "dc835ba5-a773-4aa1-b2f5-7e1ed318c5b9"
OCOYA_WORKSPACE = "clapmus480dwb5vzyghnv5dku"

PROFILE_IDS = {
    "twitter": "cmdftz3un001870rrzbjc8o4",
    "linkedin": "cll7ytoyz002wl70fnxk0tjwr",
    "instagram": "cmdftzne6005l1hrgeacfi8sx",
    "facebook": "cmdftypmk005e1hrg1b7ow01b",
}

SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE


def ocaya_schedule_post(caption: str, platform: str, hours_from_now: int = 1) -> dict:
    """Schedule a post via Ocoya API. Returns result dict."""
    profile_id = PROFILE_IDS[platform]
    now_ist = datetime.now(IST)
    post_time = now_ist + timedelta(hours=hours_from_now)
    post_utc = post_time - timedelta(hours=5, minutes=30)
    post_time_str = post_utc.strftime("%Y-%m-%dT%H:%M:%SZ")

    payload = {
        "caption": caption,
        "profileIds": [profile_id],
        "scheduledAt": post_time_str,
    }

    data = json.dumps(payload).encode()
    url = f"{OCOYA_BASE}/post?workspaceId={OCOYA_WORKSPACE}"
    req = urllib.request.Request(url, data=data, headers={
        "X-API-Key": OCOYA_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json",
    }, method="POST")

    try:
        resp = urllib.request.urlopen(req, timeout=15, context=SSL_CTX)
        result = json.loads(resp.read().decode())
        return {"success": True, "postGroupId": result.get("postGroupId"),
                "scheduledAt": post_time_str, "platform": platform}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:200]
        return {"success": False, "http_code": e.code, "error": error_body, "platform": platform}
    except Exception as e:
        return {"success": False, "error": str(e), "platform": platform}


def post_item(item: dict, dry_run: bool = False) -> dict:
    """Post a content item to all platforms via Ocaya."""
    platforms = ["twitter", "linkedin", "instagram", "facebook"]
    results = {"type": item.get("type"), "name": item.get("name")}

    for platform in platforms:
        content = item.get(platform, "")
        if not content:
            continue

        if dry_run:
            print(f"  [DRY RUN] {platform}: {content[:80]}...")
            results[platform] = {"dry_run": True}
            continue

        result = ocaya_schedule_post(content, platform, hours_from_now=1)
        results[platform] = result

        if result.get("success"):
            print(f"  ✓ {platform}: Scheduled (ID: {result.get('postGroupId')})")
        else:
            print(f"  � {platform}: {result.get('error', result.get('http_code', 'unknown'))}")

    return results


def get_queue_status():
    """Show current queue status."""
    if not QUEUE_FILE.exists():
        print("No queue file found. Run --generate first.")
        return

    queue = json.loads(QUEUE_FILE.read_text())
    now_ist = datetime.now(IST)
    print(f"\n📅 Content Queue — {now_ist.strftime('%A, %B %d %Y')}")
    print(f"   Current time: {now_ist.strftime('%I:%M %p IST')}")
    print(f"   {'─' * 50}")

    done_count = sum(1 for q in queue if q.get("done"))
    print(f"   Progress: {done_count}/{len(queue)} posted\n")

    for q in queue:
        status = "✅" if q.get("done") else "�"
        hour = q.get("scheduled_hour", "?")
        ptype = q.get("type", "unknown")
        name = q.get("name", q.get("project_id", ""))
        print(f"   {status} {hour:02d}:00 IST | {ptype:25} | {name}")


def generate_queue():
    """Generate today's content queue."""
    sys.path.insert(0, str(SCRIPT_DIR))
    from content_calendar import generate_daily_queue, save_queue
    projects_file = PROJECT_ROOT / "docs" / "data" / "projects.json"
    with open(projects_file) as f:
        projects = json.load(f).get("projects", [])
    queue = generate_daily_queue(projects)
    save_queue(queue)
    print(f"✅ Generated {len(queue)} posts for today's queue")
    for q in queue:
        print(f"  {q['scheduled_hour']:02d}:00 IST | {q['type']:20} | {q['name']}")
    return queue


def post_next(dry_run: bool = False):
    """Get and post the next queued item."""
    sys.path.insert(0, str(SCRIPT_DIR))
    from content_calendar import get_next_post, mark_done, load_queue, save_queue

    # Check if queue exists and has undone items
    queue = load_queue()
    now_ist = datetime.now(IST)

    # If queue is empty or all done, generate new one
    if not queue or all(q.get("done") for q in queue):
        print("🔄 Queue empty or complete — generating new content...")
        generate_queue()

    item = get_next_post()
    if not item:
        print("❌ No posts available.")
        return

    print(f"\n📱 Posting: {item.get('type')} — {item.get('name')}")
    print(f"   Scheduled slot: {item.get('scheduled_hour', '?')}:00 IST")
    print(f"   Platform entries: twitter={bool(item.get('twitter'))}, linkedin={bool(item.get('linkedin'))}, instagram={bool(item.get('instagram'))}, facebook={bool(item.get('facebook'))}")
    print()

    results = post_item(item, dry_run=dry_run)

    if not dry_run:
        mark_done(item)
        print(f"\n✅ Marked as done. Next post ready for next cron cycle.")
    
    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="AIdentify Continuous Social Poster")
    parser.add_argument("--dry-run", action="store_true", help="Show what would be posted")
    parser.add_argument("--generate", action="store_true", help="Regenerate daily queue")
    parser.add_argument("--status", action="store_true", help="Show queue status")
    args = parser.parse_args()

    if args.generate:
        generate_queue()
    elif args.status:
        get_queue_status()
    else:
        post_next(dry_run=args.dry_run)
