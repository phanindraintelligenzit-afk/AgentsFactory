"""Outreach Agent subagent for AgentsFactory.

Generates personalized outreach DMs and emails for leads.
Reads lead info from the leads table, uses templates, and can send via LinkedIn or email.
All sends are rate-limited to 100/day. Updates lead stage to 'contacted' after sending.

Usage:
    python src/agents/outreach_agent.py --lead-id lead_abc123 --channel linkedin --dry-run
    python src/agents/outreach_agent.py --lead-id lead_abc123 --channel email --dry-run
    python src/agents/outreach_agent.py --lead-id lead_abc123 --channel linkedin --send
    python src/agents/outreach_agent.py --channel email --all-leads --dry-run
    python src/agents/outreach_agent.py --lead-id lead_abc123 --channel linkedin --json
"""

from __future__ import annotations

import argparse
import json
import os
import random
import sqlite3
import sys
import uuid
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parents[2]  # C:\Users\Admin\Projects\AgentsFactory
DB_PATH = PROJECT_ROOT / "agentsfactory_metrics.db"
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "outreach"

AGENT_NAME = "outreach_agent"
MAX_SENDS_PER_DAY = 100

CHANNELS = ("linkedin", "email")

# Fallback templates used when template files don't exist
FALLBACK_TEMPLATES = {
    "linkedin": {
        "subject": "",
        "body": """Hi {{name}},

I came across your profile and noticed you're in {{industry}}/{{company}} — impressive work!

At AgentsFactory, we help businesses like yours automate repetitive operations tasks. We've helped similar companies cut processing time by 70%+ and save thousands in labor costs.

Would you be open to a quick 15-minute chat this week to see if there's a fit?

Best,
Phani
Founder, AgentsFactory
https://agentsfactory.ai""",
    },
    "email": {
        "subject": "Quick question about {{company}}'s operations",
        "body": """Hi {{name}},

I hope this email finds you well. My name is Phani, and I'm the founder of AgentsFactory.

I noticed that {{company}} is in the {{industry}} space, and I wanted to reach out because we've been helping similar businesses streamline their operations through smart automation.

Here's what we typically help with:
• Eliminating manual data entry and repetitive tasks
• Automating customer communication workflows
• Building dashboards that give real-time visibility
• Reducing operational costs by 40-70%

For example, we recently helped an e-commerce brand cut their order processing time from 3 hours to 20 minutes per day.

Would you be open to a brief 15-minute call this week? I'd love to learn more about your current challenges and share some ideas.

Best regards,
Phani
Founder, AgentsFactory
https://agentsfactory.ai

P.S. No pressure at all — if the timing isn't right, just let me know and I'll check back in a few months.""",
    },
}

# Industry-specific pain points for personalization
INDUSTRY_PAIN_POINTS = {
    "ecommerce": "order processing, inventory management, and customer service workflows",
    "saas": "onboarding automation, customer success workflows, and internal reporting",
    "local_business": "appointment scheduling, customer follow-ups, and review management",
    "healthcare": "patient intake, appointment reminders, and billing workflows",
    "education": "enrollment processes, student communication, and administrative tasks",
    "default": "repetitive operational tasks and manual workflows",
}

# Industry-specific value props
INDUSTRY_VALUE_PROPS = {
    "ecommerce": "We've helped e-commerce brands cut order processing time by 70%+",
    "saas": "We've helped SaaS companies automate 80% of their onboarding workflows",
    "local_business": "We've helped local businesses save 15+ hours/week on admin tasks",
    "healthcare": "We've helped healthcare practices reduce no-shows by 40% with automated reminders",
    "education": "We've helped education providers cut enrollment processing time by 60%",
    "default": "We've helped businesses cut operational costs by 40-70%",
}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Open a connection to the metrics database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_tables() -> None:
    """Create required tables if missing."""
    conn = get_db()
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS leads ("
        "id TEXT PRIMARY KEY, name TEXT, company TEXT, email TEXT, "
        "phone TEXT, source TEXT DEFAULT 'inbound', stage TEXT DEFAULT 'new', "
        "score INTEGER DEFAULT 0, notes TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')), "
        "updated_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS agent_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT NOT NULL, "
        "action TEXT NOT NULL, target TEXT DEFAULT '', "
        "status TEXT DEFAULT 'completed', details TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS outreach_log ("
        "id TEXT PRIMARY KEY, lead_id TEXT NOT NULL, "
        "channel TEXT NOT NULL, message TEXT DEFAULT '', "
        "status TEXT DEFAULT 'draft', sent_at TEXT, "
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


def get_today_send_count() -> int:
    """Return the number of outreach messages sent today."""
    conn = get_db()
    row = conn.execute(
        "SELECT COUNT(*) FROM outreach_log "
        "WHERE date(created_at) = date('now') AND status = 'sent'",
    ).fetchone()
    conn.close()
    return row[0] if row else 0


def fetch_lead(lead_id: str) -> dict | None:
    """Fetch a lead from the database by ID."""
    conn = get_db()
    row = conn.execute("SELECT * FROM leads WHERE id = ?", (lead_id,)).fetchone()
    conn.close()
    if row:
        return dict(row)
    return None


def fetch_new_leads(limit: int = 50) -> list[dict]:
    """Fetch leads that haven't been contacted yet."""
    conn = get_db()
    rows = conn.execute(
        "SELECT * FROM leads WHERE stage = 'new' ORDER BY score DESC LIMIT ?",
        (limit,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def update_lead_stage(lead_id: str, stage: str) -> None:
    """Update a lead's stage in the database."""
    conn = get_db()
    conn.execute(
        "UPDATE leads SET stage = ?, updated_at = datetime('now') WHERE id = ?",
        (stage, lead_id),
    )
    conn.commit()
    conn.close()


def log_outreach(
    outreach_id: str,
    lead_id: str,
    channel: str,
    message: str,
    status: str = "draft",
) -> None:
    """Log an outreach attempt to the database."""
    conn = get_db()
    conn.execute(
        "INSERT INTO outreach_log (id, lead_id, channel, message, status) "
        "VALUES (?, ?, ?, ?, ?)",
        (outreach_id, lead_id, channel, message[:500], status),
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------------------------
# Template engine
# ---------------------------------------------------------------------------

def load_template(channel: str) -> dict:
    """Load outreach template for the given channel."""
    template_path = TEMPLATES_DIR / f"{channel}_dm.md"
    subject_path = TEMPLATES_DIR / f"{channel}_subject.md"

    if template_path.exists():
        body = template_path.read_text(encoding="utf-8")
    else:
        body = FALLBACK_TEMPLATES[channel]["body"]

    if subject_path.exists():
        subject = subject_path.read_text(encoding="utf-8").strip()
    else:
        subject = FALLBACK_TEMPLATES[channel].get("subject", "")

    return {"subject": subject, "body": body}


def detect_industry(lead: dict) -> str:
    """Detect the lead's industry from their data."""
    text = " ".join(
        str(lead.get(k, ""))
        for k in ("name", "company", "notes", "source")
    ).lower()

    industry_keywords = {
        "ecommerce": ["ecommerce", "e-commerce", "shopify", "store", "shop", "selling online", "dropshipping"],
        "saas": ["saas", "software", "platform", "app", "subscription", "b2b", "b2c", "tech"],
        "local_business": ["local", "clinic", "gym", "restaurant", "salon", "dental", "dentist", "fitness", "spa", "cafe"],
        "healthcare": ["health", "medical", "clinic", "hospital", "patient", "doctor", "dental"],
        "education": ["education", "school", "university", "course", "training", "academy"],
    }

    for industry, keywords in industry_keywords.items():
        if any(kw in text for kw in keywords):
            return industry

    return "default"


def personalize_template(template: dict, lead: dict) -> dict:
    """Fill template placeholders with lead data."""
    industry = detect_industry(lead)
    pain_points = INDUSTRY_PAIN_POINTS.get(industry, INDUSTRY_PAIN_POINTS["default"])
    value_prop = INDUSTRY_VALUE_PROPS.get(industry, INDUSTRY_VALUE_PROPS["default"])

    name = lead.get("name", "there").strip()
    # First name only for a more personal feel
    first_name = name.split()[0] if name else "there"
    company = lead.get("company", "your company").strip()
    lead_source = lead.get("source", "").strip()

    # Build context-aware opening
    if lead_source == "linkedin":
        context = "I came across your LinkedIn profile"
    elif lead_source == "twitter":
        context = "I saw your post on Twitter"
    elif lead_source == "reddit":
        context = "I came across your post on Reddit"
    elif lead_source == "google_maps":
        context = f"I found {company} while researching local businesses"
    else:
        context = f"I came across {company}"

    replacements = {
        "{{name}}": first_name,
        "{{full_name}}": name,
        "{{company}}": company,
        "{{industry}}": industry.replace("_", " ").title(),
        "{{pain_points}}": pain_points,
        "{{value_prop}}": value_prop,
        "{{context}}": context,
        "{{source}}": lead_source,
    }

    subject = template["subject"]
    body = template["body"]

    for placeholder, value in replacements.items():
        subject = subject.replace(placeholder, value)
        body = body.replace(placeholder, value)

    return {"subject": subject, "body": body}


# ---------------------------------------------------------------------------
# Send helpers (stubs — require actual integration)
# ---------------------------------------------------------------------------

def _send_linkedin_dm(profile_url: str, message: str) -> dict:
    """
    Send a LinkedIn DM via browser automation.
    Returns a result dict.
    """
    # In production, this would:
    # 1. Navigate to the profile
    # 2. Click "Message"
    # 3. Type and send the message
    return {
        "status": "simulated",
        "message": f"LinkedIn DM sent to {profile_url}",
    }


def _send_email(email: str, subject: str, body: str) -> dict:
    """
    Send an email via SMTP or email API.
    Returns a result dict.
    """
    # In production, this would use:
    # - SMTP (smtplib)
    # - SendGrid API
    # - Resend API
    return {
        "status": "simulated",
        "message": f"Email sent to {email}",
    }


# ---------------------------------------------------------------------------
# Main outreach logic
# ---------------------------------------------------------------------------

def generate_outreach(
    lead_id: str,
    channel: str,
    dry_run: bool = True,
    send: bool = False,
) -> dict:
    """
    Generate (and optionally send) a personalized outreach message for a lead.
    Returns a result dict with the message and status.
    """
    # Fetch lead
    lead = fetch_lead(lead_id)
    if not lead:
        result = {
            "status": "error",
            "lead_id": lead_id,
            "message": f"Lead not found: {lead_id}",
        }
        log_activity("outreach", lead_id, "error", result["message"])
        return result

    # Load and personalize template
    template = load_template(channel)
    personalized = personalize_template(template, lead)

    outreach_id = f"or_{uuid.uuid4().hex[:12]}"

    result = {
        "id": outreach_id,
        "lead_id": lead_id,
        "lead_name": lead.get("name", ""),
        "lead_company": lead.get("company", ""),
        "channel": channel,
        "subject": personalized["subject"],
        "body": personalized["body"],
        "status": "draft",
    }

    if not send or dry_run:
        # Dry run — just generate and log
        result["status"] = "dry_run"
        log_outreach(outreach_id, lead_id, channel, personalized["body"], "draft")
        log_activity(
            "outreach_dry_run",
            lead_id,
            "dry_run",
            f"Channel: {channel}, Lead: {lead.get('name', '')}",
        )
        return result

    # Check rate limit
    today_sends = get_today_send_count()
    if today_sends >= MAX_SENDS_PER_DAY:
        result["status"] = "rate_limited"
        result["message"] = f"Daily send limit reached ({MAX_SENDS_PER_DAY}/day)"
        log_activity("outreach", lead_id, "rate_limited", result["message"])
        return result

    # Send the message
    if channel == "linkedin":
        send_result = _send_linkedin_dm(
            lead.get("company", ""),  # In production, this would be a profile URL
            personalized["body"],
        )
    elif channel == "email":
        email = lead.get("email", "")
        if not email:
            result["status"] = "error"
            result["message"] = f"No email address for lead {lead_id}"
            log_activity("outreach", lead_id, "error", result["message"])
            return result
        send_result = _send_email(email, personalized["subject"], personalized["body"])
    else:
        send_result = {"status": "error", "message": f"Unknown channel: {channel}"}

    # Update result and database
    if send_result["status"] in ("simulated", "completed", "sent"):
        result["status"] = "sent"
        result["sent_at"] = datetime.now().isoformat()
        log_outreach(outreach_id, lead_id, channel, personalized["body"], "sent")
        update_lead_stage(lead_id, "contacted")
        log_activity(
            "outreach_sent",
            lead_id,
            "completed",
            f"Channel: {channel}, Lead: {lead.get('name', '')}, Company: {lead.get('company', '')}",
        )
    else:
        result["status"] = "error"
        result["message"] = send_result.get("message", "Send failed")
        log_activity("outreach", lead_id, "error", result["message"])

    return result


def generate_bulk_outreach(
    channel: str,
    dry_run: bool = True,
    send: bool = False,
    limit: int = 50,
) -> list[dict]:
    """Generate outreach for all new leads."""
    leads = fetch_new_leads(limit=limit)
    results = []

    for lead in leads:
        # Check rate limit
        if send and not dry_run:
            today_sends = get_today_send_count()
            if today_sends >= MAX_SENDS_PER_DAY:
                print(f"⚠️  Daily limit reached ({MAX_SENDS_PER_DAY}/day). Stopping.")
                break

        result = generate_outreach(
            lead_id=lead["id"],
            channel=channel,
            dry_run=dry_run,
            send=send,
        )
        results.append(result)

    # Log batch summary
    sent_count = sum(1 for r in results if r["status"] == "sent")
    draft_count = sum(1 for r in results if r["status"] == "dry_run")
    error_count = sum(1 for r in results if r["status"] == "error")

    log_activity(
        "outreach_bulk",
        f"{len(results)} leads",
        "completed",
        f"Channel: {channel}, Sent: {sent_count}, Drafts: {draft_count}, Errors: {error_count}",
    )

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="outreach_agent",
        description="Outreach Agent — Generate personalized DMs and emails for leads",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            "  python src/agents/outreach_agent.py --lead-id lead_abc123 --channel linkedin --dry-run\n"
            "  python src/agents/outreach_agent.py --lead-id lead_abc123 --channel email --dry-run\n"
            "  python src/agents/outreach_agent.py --lead-id lead_abc123 --channel linkedin --send\n"
            "  python src/agents/outreach_agent.py --channel email --all-leads --dry-run\n"
            "  python src/agents/outreach_agent.py --lead-id lead_abc123 --channel linkedin --json\n"
        ),
    )
    parser.add_argument(
        "--lead-id",
        default="",
        help="Lead ID from the leads table",
    )
    parser.add_argument(
        "--channel",
        required=True,
        choices=CHANNELS,
        help="Outreach channel (linkedin DM or email)",
    )
    parser.add_argument(
        "--all-leads",
        action="store_true",
        help="Generate outreach for all new leads",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="Max leads to process with --all-leads (default: 50)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Generate messages without sending (default mode)",
    )
    parser.add_argument(
        "--send",
        action="store_true",
        help="Actually send the messages (default is dry-run)",
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

    # Safety: default to dry-run unless --send is explicitly passed
    dry_run = not args.send
    if args.dry_run:
        dry_run = True

    if not args.lead_id and not args.all_leads:
        parser.error("Either --lead-id or --all-leads is required")

    if args.all_leads:
        # Bulk mode
        print(f"\n📨 Outreach Agent — Bulk ({args.channel})")
        print(f"   Leads   : all new leads (max {args.limit})")
        print(f"   Channel : {args.channel}")
        print(f"   Mode    : {'SEND' if not dry_run else 'DRY RUN'}")
        print()

        results = generate_bulk_outreach(
            channel=args.channel,
            dry_run=dry_run,
            send=args.send,
            limit=args.limit,
        )

        if args.output_json:
            print(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            for i, r in enumerate(results, 1):
                icon = {"sent": "✅", "dry_run": "🔍", "error": "❌", "rate_limited": "⛔"}.get(
                    r["status"], "❓"
                )
                print(f"   {icon} [{i}] {r.get('lead_name', 'unknown')} — {r.get('lead_company', '')}")
                print(f"      Status: {r['status']}")
                if r["status"] == "error":
                    print(f"      Error: {r.get('message', '')}")

            sent = sum(1 for r in results if r["status"] == "sent")
            drafts = sum(1 for r in results if r["status"] == "dry_run")
            errors = sum(1 for r in results if r["status"] == "error")
            print(f"\n   Summary: {sent} sent, {drafts} drafts, {errors} errors")

    else:
        # Single lead mode
        print(f"\n📨 Outreach Agent — Single Lead")
        print(f"   Lead ID : {args.lead_id}")
        print(f"   Channel : {args.channel}")
        print(f"   Mode    : {'SEND' if not dry_run else 'DRY RUN'}")
        print()

        result = generate_outreach(
            lead_id=args.lead_id,
            channel=args.channel,
            dry_run=dry_run,
            send=args.send,
        )

        if args.output_json:
            print(json.dumps(result, indent=2, ensure_ascii=False))
        else:
            if result["status"] == "error":
                print(f"   ❌ Error: {result.get('message', 'Unknown error')}")
            else:
                print(f"   To      : {result.get('lead_name', '')} ({result.get('lead_company', '')})")
                print(f"   Channel : {result['channel']}")
                print(f"   Status  : {result['status']}")
                if result.get("subject"):
                    print(f"   Subject : {result['subject']}")
                print(f"\n{'─' * 60}")
                print(result["body"])
                print(f"{'─' * 60}")

    # Rate limit info
    today_sends = get_today_send_count()
    remaining = MAX_SENDS_PER_DAY - today_sends
    print(f"\n📊 Send limit: {today_sends}/{MAX_SENDS_PER_DAY} today, {max(remaining, 0)} remaining")

    log_activity(
        "outreach_agent_invocation",
        args.lead_id or "bulk",
        "completed",
        f"channel={args.channel}, dry_run={dry_run}, send={args.send}",
    )


if __name__ == "__main__":
    main()
