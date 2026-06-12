"""
Lead Outreach Automation System
Multi-channel outreach: Email, LinkedIn DM, Twitter DM, Facebook Message.
Targets HOT leads first, then Great, then Good.

Usage:
    python outreach_automation.py --dry-run          # Preview what would be sent
    python outreach_automation.py --send --limit 10  # Send to 10 leads
    python outreach_automation.py --stats            # Show outreach stats
"""
import sys
import os
import json
import random
import sqlite3
import argparse
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocoya_client import post_to_linkedin, post_to_twitter, post_to_facebook

DB_PATH = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "agentsfactory_metrics.db"))


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_leads_by_priority(limit: int = 50) -> list[dict]:
    """Get leads ordered by priority: HOT > Great > Good, then by social followers."""
    conn = get_db()
    leads = conn.execute("""
        SELECT id, company, email, phone, website, category, social_lead_score,
               facebook_followers, twitter_followers, facebook_url, twitter_url,
               gmb_url, keyword
        FROM leads
        WHERE email != '' OR facebook_url != '' OR twitter_url != ''
        ORDER BY
            CASE social_lead_score
                WHEN 'HOT' THEN 1
                WHEN 'Great' THEN 2
                WHEN 'Good' THEN 3
                ELSE 4
            END,
            COALESCE(facebook_followers, 0) + COALESCE(twitter_followers, 0) DESC
        LIMIT ?
    """, (limit,)).fetchall()
    conn.close()
    return [dict(l) for l in leads]


# ============================================================
# Outreach message templates — personalized per platform
# ============================================================

def generate_linkedin_dm(lead: dict) -> str:
    """Generate a personalized LinkedIn DM."""
    company = lead["company"]
    category = lead.get("category", "business")
    keyword = lead.get("keyword", "")

    templates = [
        f"Hi! I noticed {company} is doing great work in the {category} space. I'm building AI automation for businesses like yours — helping them save 20+ hours/week on manual tasks. Would love to connect and share what we're building at AgentsFactory. Quick chat?",
        f"Hey! Came across {company} and was impressed by your work. We help {category} companies automate their operations with AI agents. Our clients typically see 50%+ time savings within 30 days. Worth a quick 15-min call?",
        f"Hi there! I've been researching top {category} companies and {company} stood out. I'm building AgentsFactory — an AI automation agency. We help businesses like yours scale without adding headcount. Open to a quick intro call?",
    ]
    return random.choice(templates)


def generate_twitter_dm(lead: dict) -> str:
    """Generate a personalized Twitter DM."""
    company = lead["company"]
    category = lead.get("category", "business")

    templates = [
        f"Hi! Love what {company} is doing in the {category} space 🚀 I'm building AI automation for businesses like yours — saving 20+ hours/week on manual work. Worth a quick chat?",
        f"Hey! Noticed {company} is making waves in {category}. We help companies like yours automate operations with AI agents. 50%+ time savings typical. Interested in learning more?",
    ]
    return random.choice(templates)


def generate_facebook_message(lead: dict) -> str:
    """Generate a personalized Facebook message."""
    company = lead["company"]
    category = lead.get("category", "business")

    templates = [
        f"Hi! I came across {company} and was really impressed by your work in the {category} space. I'm building AgentsFactory — we help businesses like yours automate manual tasks with AI agents. Would love to connect!",
        f"Hello! {company} is doing amazing work. We help {category} companies save 20+ hours/week through AI automation. Would you be open to a quick 15-min call to see if we can help?",
    ]
    return random.choice(templates)


def generate_email(lead: dict) -> dict:
    """Generate a personalized email."""
    company = lead["company"]
    category = lead.get("category", "business")
    email = lead["email"]

    subject_options = [
        f"Quick question about {company}'s operations",
        f"AI automation for {company}",
        f"Save 20+ hours/week at {company}?",
        f"Re: {company} + AI automation",
    ]

    body = f"""Hi there,

I came across {company} and was impressed by your work in the {category} space.

I'm building AgentsFactory — an AI automation agency that helps businesses like yours:

→ Automate manual tasks (data entry, lead research, follow-ups)
→ Save 20+ hours/week per team member
→ Scale operations without adding headcount

Our starter plan begins at $500/month, and most clients see ROI within 30 days.

Would you be open to a quick 15-min call this week to see if we can help {company}?

Best,
Phani
Founder, AgentsFactory
https://agentsfactory.dev

P.S. If this isn't the right time, no worries — just reply "not now" and I'll follow up in a quarter.
"""

    return {
        "to": email,
        "subject": random.choice(subject_options),
        "body": body,
    }


# ============================================================
# Outreach execution
# ============================================================

def send_linkedin_outreach(lead: dict, dry_run: bool = True) -> dict:
    """Send LinkedIn outreach via Ocoya."""
    message = generate_linkedin_dm(lead)
    result = {
        "lead": lead["company"],
        "platform": "linkedin",
        "message": message[:100] + "...",
        "dry_run": dry_run,
    }

    if not dry_run:
        try:
            # Post as a LinkedIn message via Ocoya
            # Note: Ocoya supports posting; for DMs we'd need LinkedIn API
            # For now, we create a public post targeting the lead
            ocoya_result = post_to_linkedin(
                f"Connecting with amazing {lead.get('category', 'business')} companies like {lead['company']}! 🚀\n\nIf you're looking to automate your operations with AI, let's talk.\n\n#AIAgents #Automation"
            )
            result["ocoya_result"] = ocoya_result
        except Exception as e:
            result["error"] = str(e)

    return result


def send_twitter_outreach(lead: dict, dry_run: bool = True) -> dict:
    """Send Twitter outreach via Ocoya."""
    message = generate_twitter_dm(lead)
    result = {
        "lead": lead["company"],
        "platform": "twitter",
        "message": message[:100] + "...",
        "dry_run": dry_run,
    }

    if not dry_run:
        try:
            ocoya_result = post_to_twitter(
                f"Love what @{lead['company'].replace(' ', '')} is doing! 🚀\n\nIf you're in the {lead.get('category', 'marketing')} space and want to automate manual work, let's connect.\n\n#AIAgents #Automation"
            )
            result["ocoya_result"] = ocoya_result
        except Exception as e:
            result["error"] = str(e)

    return result


def send_facebook_outreach(lead: dict, dry_run: bool = True) -> dict:
    """Send Facebook outreach via Ocoya."""
    message = generate_facebook_message(lead)
    result = {
        "lead": lead["company"],
        "platform": "facebook",
        "message": message[:100] + "...",
        "dry_run": dry_run,
    }

    if not dry_run:
        try:
            ocoya_result = post_to_facebook(
                f"Connecting with amazing {lead.get('category', 'business')} companies! 🚀\n\nWe help businesses automate 80% of manual work with AI agents.\n\nInterested? Drop a comment or DM me.\n\n#AIAgents #Automation"
            )
            result["ocoya_result"] = ocoya_result
        except Exception as e:
            result["error"] = str(e)

    return result


def run_outreach_campaign(limit: int = 10, dry_run: bool = True) -> dict:
    """
    Run a full outreach campaign across all channels.
    """
    leads = get_leads_by_priority(limit)
    results = {
        "timestamp": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "dry_run": dry_run,
        "total_leads": len(leads),
        "actions": [],
    }

    print(f"🎯 Outreach Campaign {'(DRY RUN)' if dry_run else '(LIVE)'}")
    print(f"   Targeting {len(leads)} leads")
    print("=" * 60)

    for i, lead in enumerate(leads, 1):
        score = lead.get("social_lead_score", "?")
        company = lead["company"]
        print(f"\n{i}/{len(leads)} [{score}] {company}")

        # LinkedIn outreach (if they have a LinkedIn presence)
        if lead.get("facebook_followers", 0) > 1000 or lead.get("twitter_followers", 0) > 500:
            result = send_linkedin_outreach(lead, dry_run)
            results["actions"].append(result)
            print(f"  💼 LinkedIn: {result['message'][:60]}...")

        # Twitter outreach
        if lead.get("twitter_url") and lead.get("twitter_followers", 0) > 100:
            result = send_twitter_outreach(lead, dry_run)
            results["actions"].append(result)
            print(f"  🐦 Twitter: {result['message'][:60]}...")

        # Facebook outreach
        if lead.get("facebook_url") and lead.get("facebook_followers", 0) > 1000:
            result = send_facebook_outreach(lead, dry_run)
            results["actions"].append(result)
            print(f"  📘 Facebook: {result['message'][:60]}...")

        # Email outreach (generate but don't send without SMTP)
        if lead.get("email"):
            email = generate_email(lead)
            results["actions"].append({
                "lead": company,
                "platform": "email",
                "to": email["to"],
                "subject": email["subject"],
                "dry_run": True,  # Email always dry-run until SMTP configured
            })
            print(f"  📧 Email: {email['subject']}")

    # Summary
    platforms = {}
    for action in results["actions"]:
        p = action["platform"]
        platforms[p] = platforms.get(p, 0) + 1

    results["summary"] = platforms
    print(f"\n{'=' * 60}")
    print(f"📊 Campaign Summary:")
    for platform, count in platforms.items():
        print(f"   {platform}: {count} messages")

    return results


def get_outreach_stats() -> dict:
    """Get outreach statistics."""
    conn = get_db()
    stats = {
        "total_leads": conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0],
        "hot_leads": conn.execute("SELECT COUNT(*) FROM leads WHERE social_lead_score='HOT'").fetchone()[0],
        "great_leads": conn.execute("SELECT COUNT(*) FROM leads WHERE social_lead_score='Great'").fetchone()[0],
        "with_email": conn.execute("SELECT COUNT(*) FROM leads WHERE email != ''").fetchone()[0],
        "with_facebook": conn.execute("SELECT COUNT(*) FROM leads WHERE facebook_url != ''").fetchone()[0],
        "with_twitter": conn.execute("SELECT COUNT(*) FROM leads WHERE twitter_url != ''").fetchone()[0],
        "with_gmb": conn.execute("SELECT COUNT(*) FROM leads WHERE gmb_url != ''").fetchone()[0],
    }

    # Top leads by platform
    stats["top_linkedin_targets"] = [dict(r) for r in conn.execute(
        "SELECT company, facebook_followers, email FROM leads WHERE facebook_followers > 5000 ORDER BY facebook_followers DESC LIMIT 5"
    ).fetchall()]
    stats["top_twitter_targets"] = [dict(r) for r in conn.execute(
        "SELECT company, twitter_followers, email FROM leads WHERE twitter_followers > 1000 ORDER BY twitter_followers DESC LIMIT 5"
    ).fetchall()]

    conn.close()
    return stats


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Lead Outreach Automation")
    parser.add_argument("--dry-run", action="store_true", default=True, help="Preview without sending")
    parser.add_argument("--send", action="store_true", help="Actually send messages")
    parser.add_argument("--limit", type=int, default=10, help="Number of leads to target")
    parser.add_argument("--stats", action="store_true", help="Show outreach stats")
    args = parser.parse_args()

    if args.stats:
        stats = get_outreach_stats()
        print(json.dumps(stats, indent=2))
    else:
        dry_run = not args.send
        results = run_outreach_campaign(limit=args.limit, dry_run=dry_run)
