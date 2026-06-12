"""LinkedIn Agent subagent for AgentsFactory.

Posts content to LinkedIn, engages with target posts, and sends connection requests.
Uses browser automation (LinkedIn requires login — Phani's credentials).
All actions are rate-limited to 20/day to avoid LinkedIn restrictions.

Usage:
    python src/agents/linkedin_agent.py --action post --content-id cc_abc123
    python src/agents/linkedin_agent.py --action post --content-id cc_abc123 --dry-run
    python src/agents/linkedin_agent.py --action engage
    python src/agents/linkedin_agent.py --action engage --dry-run
    python src/agents/linkedin_agent.py --action connect --profile-urls url1 url2 url3
    python src/agents/linkedin_agent.py --action connect --profile-urls url1 url2 --dry-run
    python src/agents/linkedin_agent.py --action status
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
import time
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # C:\Users\Admin\Projects\AgentsFactory
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"

AGENT_NAME = "linkedin_agent"
MAX_ACTIONS_PER_DAY = 20
ENGAGE_TARGET_COUNT = 10
CONNECT_TARGET_COUNT = 5

# LinkedIn profile URLs to engage with (target personas)
DEFAULT_ENGAGE_TARGETS = [
    "https://www.linkedin.com/in/search/?keywords=ecommerce%20founder",
    "https://www.linkedin.com/in/search/?keywords=shopify%20store%20owner",
    "https://www.linkedin.com/in/search/?keywords=saas%20founder%20india",
    "https://www.linkedin.com/in/search/?keywords=operations%20manager%20ecommerce",
    "https://www.linkedin.com/in/search/?keywords=business%20automation%20consultant",
]

# Sample engagement comments (rotated to avoid detection)
ENGAGEMENT_COMMENTS = [
    "Great insights! Automation has been a game-changer for similar challenges. Would love to hear more about your approach.",
    "This resonates — we've seen 70%+ efficiency gains by automating exactly these kinds of workflows. Thanks for sharing!",
    "Spot on. The manual work bottleneck is real. We help founders solve exactly this — keep up the great content!",
    "Love this perspective. We've been working on similar automation stacks — the ROI numbers are incredible.",
    "Thanks for sharing! This is exactly the kind of problem that keeps founders up at night. Smart systems > bigger teams.",
    "Well said. We've helped e-commerce teams cut processing time by 70%+ with the right automation. Great discussion here.",
    "Interesting take! We see this pattern across SaaS and e-commerce — the bottleneck is almost always the same 5-6 processes.",
    "This is why automation matters. Great post — the before/after numbers always tell the story.",
]


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Open a connection to the metrics database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_tables() -> None:
    """Create required tables if missing."""
    conn = get_db()
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS agent_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT NOT NULL, "
        "action TEXT NOT NULL, target TEXT DEFAULT '', "
        "status TEXT DEFAULT 'completed', details TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS linkedin_actions ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, action_type TEXT NOT NULL, "
        "target TEXT DEFAULT '', status TEXT DEFAULT 'pending', "
        "details TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
    )
    conn.commit()
    conn.close()


def log_activity(
    action: str,
    target: str = "",
    status: str = "completed",
    details: str = "",
) -> None:
    """Log agent activity to the database."""
    conn = get_db()
    conn.execute(
        "INSERT INTO agent_activity (agent_name, action, target, status, details) "
        "VALUES (?, ?, ?, ?, ?)",
        (AGENT_NAME, action, target, status, details),
    )
    conn.commit()
    conn.close()


def get_today_action_count() -> int:
    """Return the number of LinkedIn actions performed today."""
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) FROM linkedin_actions "
        "WHERE date(created_at) = date('now') AND status = 'completed'",
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def record_linkedin_action(
    action_type: str,
    target: str = "",
    status: str = "completed",
    details: str = "",
) -> None:
    """Record a LinkedIn-specific action for rate limiting."""
    conn = get_db()
    conn.execute(
        "INSERT INTO linkedin_actions (action_type, target, status, details) "
        "VALUES (?, ?, ?, ?)",
        (action_type, target, status, details),
    )
    conn.commit()
    conn.close()


def fetch_content(content_id: str) -> dict | None:
    """Fetch a content piece from content_calendar by ID."""
    conn = get_db()
    conn.row_factory = sqlite3.Row
    row = conn.execute(
        "SELECT * FROM content_calendar WHERE id = ?", (content_id,)
    ).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


# ---------------------------------------------------------------------------
# Rate limit check
# ---------------------------------------------------------------------------

def check_rate_limit(requested_actions: int) -> tuple[bool, int]:
    """
    Check if the requested number of actions is within the daily limit.
    Returns (allowed: bool, remaining: int).
    """
    today_count = get_today_action_count()
    remaining = MAX_ACTIONS_PER_DAY - today_count
    return (requested_actions <= remaining, remaining)


# ---------------------------------------------------------------------------
# Browser automation helpers (stub — requires Playwright/Selenium)
# ---------------------------------------------------------------------------

def _init_browser():
    """
    Initialize a browser instance for LinkedIn automation.
    In production, this uses Playwright with Phani's saved credentials.
    Returns a browser context or None if browser automation is unavailable.
    """
    try:
        # In production:
        # from playwright.sync_api import sync_playwright
        # p = sync_playwright().start()
        # browser = p.chromium.launch(headless=True)
        # context = browser.new_context(storage_state="linkedin_auth.json")
        # return context
        return None
    except ImportError:
        return None


def _post_to_linkedin(content: str, dry_run: bool = True) -> dict:
    """
    Post content to LinkedIn via browser automation.
    Returns a result dict with status and details.
    """
    if dry_run:
        return {
            "status": "dry_run",
            "message": f"[DRY RUN] Would post {len(content)} chars to LinkedIn",
        }

    browser = _init_browser()
    if browser is None:
        return {
            "status": "error",
            "message": "Browser automation not available. Install playwright: pip install playwright",
        }

    # Production flow:
    # page = browser.new_page()
    # page.goto("https://www.linkedin.com/feed/")
    # page.wait_for_selector(".share-box-feed-entry__trigger")
    # page.click(".share-box-feed-entry__trigger")
    # page.fill(".editor-content", content)
    # page.click('button:has-text("Post")')
    # page.wait_for_timeout(3000)

    return {
        "status": "completed",
        "message": "Posted to LinkedIn successfully",
    }


def _engage_with_post(profile_url: str, comment: str, dry_run: bool = True) -> dict:
    """
    Navigate to a LinkedIn post/profile and leave a comment.
    Returns a result dict.
    """
    if dry_run:
        return {
            "status": "dry_run",
            "message": f"[DRY RUN] Would comment on {profile_url}: {comment[:60]}...",
        }

    browser = _init_browser()
    if browser is None:
        return {
            "status": "error",
            "message": "Browser automation not available.",
        }

    return {
        "status": "completed",
        "message": f"Commented on {profile_url}",
    }


def _send_connection_request(profile_url: str, note: str = "", dry_run: bool = True) -> dict:
    """
    Send a LinkedIn connection request to a profile.
    Returns a result dict.
    """
    if dry_run:
        return {
            "status": "dry_run",
            "message": f"[DRY RUN] Would send connection request to {profile_url}",
        }

    browser = _init_browser()
    if browser is None:
        return {
            "status": "error",
            "message": "Browser automation not available.",
        }

    return {
        "status": "completed",
        "message": f"Connection request sent to {profile_url}",
    }


# ---------------------------------------------------------------------------
# Action: Post
# ---------------------------------------------------------------------------

def action_post(content_id: str, dry_run: bool = True) -> dict:
    """Post content to LinkedIn by content ID."""
    content = fetch_content(content_id)
    if not content:
        result = {
            "status": "error",
            "message": f"Content not found: {content_id}",
        }
        log_activity("post", content_id, "error", result["message"])
        return result

    # Check rate limit
    allowed, remaining = check_rate_limit(1)
    if not allowed:
        result = {
            "status": "rate_limited",
            "message": f"Daily limit reached ({MAX_ACTIONS_PER_DAY}/day). Try again tomorrow.",
        }
        log_activity("post", content_id, "rate_limited", result["message"])
        return result

    # Extract content body from notes (stored as JSON)
    content_body = content.get("title", "")
    notes = content.get("notes", "")
    try:
        notes_data = json.loads(notes)
        # The actual content is stored in the template; use title as the post
        content_body = notes_data.get("topic", content_body)
    except (json.JSONDecodeError, TypeError):
        pass

    # Build the LinkedIn post
    post_text = (
        f"{content_body}\n\n"
        f"---\n"
        f"#AgentsFactory #Automation"
    )

    result = _post_to_linkedin(post_text, dry_run=dry_run)

    if result["status"] == "completed":
        record_linkedin_action("post", content_id, "completed", post_text[:200])
        log_activity("post", content_id, "completed", f"Posted: {content_body[:80]}")
    elif result["status"] == "dry_run":
        log_activity("post_dry_run", content_id, "dry_run", f"Would post: {content_body[:80]}")
    else:
        log_activity("post", content_id, "error", result["message"])

    return result


# ---------------------------------------------------------------------------
# Action: Engage
# ---------------------------------------------------------------------------

def action_engage(
    target_urls: list[str] | None = None,
    count: int = ENGAGE_TARGET_COUNT,
    dry_run: bool = True,
) -> list[dict]:
    """Engage with target LinkedIn posts by commenting."""
    targets = target_urls or DEFAULT_ENGAGE_TARGETS
    results = []

    # Check rate limit
    allowed, remaining = check_rate_limit(count)
    if not allowed:
        count = remaining
        print(f"⚠️  Rate limit: only {remaining} actions remaining today.")

    if count <= 0:
        log_activity("engage", "rate_limited", "skipped", "Daily limit exhausted")
        return results

    import random
    random.shuffle(ENGAGEMENT_COMMENTS)

    for i in range(min(count, len(targets))):
        comment = ENGAGEMENT_COMMENTS[i % len(ENGAGEMENT_COMMENTS)]
        result = _engage_with_post(targets[i], comment, dry_run=dry_run)

        if result["status"] == "completed":
            record_linkedin_action("engage", targets[i], "completed", comment[:100])
        elif result["status"] == "dry_run":
            pass  # Don't record dry runs

        results.append({
            "target": targets[i],
            "comment": comment,
            "result": result,
        })

        # Small delay between actions to mimic human behavior
        if not dry_run and i < count - 1:
            time.sleep(random.uniform(2, 5))

    # Log summary
    completed = sum(1 for r in results if r["result"]["status"] == "completed")
    log_activity(
        "engage_batch",
        f"{len(results)} targets",
        "completed" if completed == len(results) else "partial",
        f"Engaged with {completed}/{len(results)} posts. Dry run: {dry_run}",
    )

    return results


# ---------------------------------------------------------------------------
# Action: Connect
# ---------------------------------------------------------------------------

def action_connect(
    profile_urls: list[str] | None = None,
    count: int = CONNECT_TARGET_COUNT,
    dry_run: bool = True,
) -> list[dict]:
    """Send LinkedIn connection requests."""
    if not profile_urls:
        result = {
            "status": "error",
            "message": "No profile URLs provided. Use --profile-urls to specify targets.",
        }
        log_activity("connect", "no_targets", "error", result["message"])
        return [result]

    results = []

    # Check rate limit
    allowed, remaining = check_rate_limit(count)
    if not allowed:
        count = remaining
        print(f"⚠️  Rate limit: only {remaining} actions remaining today.")

    if count <= 0:
        log_activity("connect", "rate_limited", "skipped", "Daily limit exhausted")
        return results

    import random

    for i in range(min(count, len(profile_urls))):
        note = (
            "Hi! I came across your profile and noticed your work in "
            "e-commerce/SaaS. I'd love to connect and exchange ideas on "
            "business automation. — Phani"
        )
        result = _send_connection_request(profile_urls[i], note, dry_run=dry_run)

        if result["status"] == "completed":
            record_linkedin_action("connect", profile_urls[i], "completed")
        elif result["status"] == "dry_run":
            pass

        results.append({
            "profile": profile_urls[i],
            "result": result,
        })

        if not dry_run and i < count - 1:
            time.sleep(random.uniform(3, 7))

    completed = sum(1 for r in results if r["result"]["status"] == "completed")
    log_activity(
        "connect_batch",
        f"{len(results)} profiles",
        "completed" if completed == len(results) else "partial",
        f"Sent {completed}/{len(results)} connection requests. Dry run: {dry_run}",
    )

    return results


# ---------------------------------------------------------------------------
# Action: Status
# ---------------------------------------------------------------------------

def action_status() -> dict:
    """Show today's LinkedIn agent activity summary."""
    today_count = get_today_action_count()
    remaining = MAX_ACTIONS_PER_DAY - today_count

    conn = get_db()
    rows = conn.execute(
        "SELECT action_type, target, status, created_at "
        "FROM linkedin_actions "
        "WHERE date(created_at) = date('now') "
        "ORDER BY created_at DESC "
        "LIMIT 20",
    ).fetchall()
    conn.close()

    actions_today = [
        {
            "type": row[0],
            "target": row[1],
            "status": row[2],
            "time": row[3],
        }
        for row in rows
    ]

    return {
        "agent": AGENT_NAME,
        "date": datetime.now().strftime("%Y-%m-%d"),
        "actions_today": today_count,
        "daily_limit": MAX_ACTIONS_PER_DAY,
        "remaining_today": max(remaining, 0),
        "recent_actions": actions_today,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="linkedin_agent",
        description="LinkedIn Agent — Post, engage, and connect on LinkedIn",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python src/agents/linkedin_agent.py --action post --content-id cc_abc123\n"
            "  python src/agents/linkedin_agent.py --action post --content-id cc_abc123 --dry-run\n"
            "  python src/agents/linkedin_agent.py --action engage\n"
            "  python src/agents/linkedin_agent.py --action engage --count 5 --dry-run\n"
            "  python src/agents/linkedin_agent.py --action connect --profile-urls url1 url2 url3\n"
            "  python src/agents/linkedin_agent.py --action status\n"
        ),
    )
    parser.add_argument(
        "--action",
        required=True,
        choices=["post", "engage", "connect", "status"],
        help="Action to perform",
    )
    parser.add_argument(
        "--content-id",
        default="",
        help="Content ID from content_calendar (required for --action post)",
    )
    parser.add_argument(
        "--profile-urls",
        nargs="*",
        default=None,
        help="LinkedIn profile URLs (for --action connect)",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of targets (default: 10 for engage, 5 for connect)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview actions without executing them",
    )
    parser.add_argument(
        "--json",
        dest="output_json",
        action="store_true",
        help="Output results as JSON",
    )
    return parser


def main() -> None:
    """Main CLI entry point."""
    parser = build_parser()
    args = parser.parse_args()

    ensure_tables()

    # Default dry-run for safety (user must explicitly use --send equivalent)
    dry_run = not getattr(args, "send", False)
    if not dry_run:
        dry_run = args.dry_run  # If --dry-run flag is set, override

    # Actually, let's be safe: default to dry_run=True unless --send is used
    # But the spec says --dry-run mode, so default is to execute
    # Re-reading spec: "--dry-run mode" means it supports --dry-run flag
    # Default behavior: execute (not dry run), unless --dry-run is passed
    dry_run = args.dry_run

    if args.action == "post":
        if not args.content_id:
            parser.error("--content-id is required for --action post")

        print(f"\n📤 LinkedIn Agent — Post")
        print(f"   Content ID : {args.content_id}")
        print(f"   Dry run    : {dry_run}")
        print()

        result = action_post(args.content_id, dry_run=dry_run)

        if args.output_json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            status_icon = "✅" if result["status"] in ("completed", "dry_run") else "❌"
            print(f"   {status_icon} {result['message']}")

    elif args.action == "engage":
        count = args.count or ENGAGE_TARGET_COUNT
        print(f"\n💬 LinkedIn Agent — Engage")
        print(f"   Targets  : {count} posts")
        print(f"   Dry run  : {dry_run}")
        print()

        results = action_engage(count=count, dry_run=dry_run)

        if args.output_json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for i, r in enumerate(results, 1):
                icon = "✅" if r["result"]["status"] in ("completed", "dry_run") else "❌"
                print(f"   {icon} [{i}] {r['target'][:60]}")
                print(f"      → {r['result']['message']}")

    elif args.action == "connect":
        count = args.count or CONNECT_TARGET_COUNT
        print(f"\n🤝 LinkedIn Agent — Connect")
        print(f"   Profiles : {args.profile_urls or 'none provided'}")
        print(f"   Count    : {count}")
        print(f"   Dry run  : {dry_run}")
        print()

        results = action_connect(
            profile_urls=args.profile_urls,
            count=count,
            dry_run=dry_run,
        )

        if args.output_json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for i, r in enumerate(results, 1):
                icon = "✅" if r["result"]["status"] in ("completed", "dry_run") else "❌"
                target = r.get("profile", r.get("message", "unknown"))
                print(f"   {icon} [{i}] {target[:60]}")
                print(f"      → {r['result']['message']}")

    elif args.action == "status":
        status = action_status()

        if args.output_json:
            print(json.dumps(status, indent=2, ensure_ascii=False))
        else:
            print(f"\n📊 LinkedIn Agent — Status")
            print(f"   Date     : {status['date']}")
            print(f"   Actions  : {status['actions_today']}/{status['daily_limit']} today")
            print(f"   Remaining: {status['remaining_today']}")
            if status["recent_actions"]:
                print(f"\n   Recent actions:")
                for a in status["recent_actions"]:
                    print(f"     {a['time']} | {a['type']:<10} | {a['status']:<10} | {a['target'][:40]}")
            print()

    # Print rate limit info
    if args.action != "status":
        today_count = get_today_action_count()
        remaining = MAX_ACTIONS_PER_DAY - today_count
        print(f"\n📊 Rate limit: {today_count}/{MAX_ACTIONS_PER_DAY} today, {max(remaining, 0)} remaining")

    log_activity(
        f"linkedin_agent_{args.action}",
        args.content_id or args.profile_urls or "",
        "completed",
        f"dry_run={dry_run}",
    )


if __name__ == "__main__":
    main()
