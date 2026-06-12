"""Content Writer subagent for AgentsFactory.

Generates infotainment-style content across 6 pillars and 4 platforms.
Saves drafts to content_calendar table and logs activity to agent_activity table.

Usage:
    python src/agents/content_writer.py --platform linkedin --pillar tips_tutorial --topic "Shopify automation" --count 3
    python src/agents/content_writer.py --platform twitter --pillar case_study --topic "e-commerce workflows" --count 5 --dry-run
    python src/agents/content_writer.py --platform newsletter --pillar industry_insight --topic "AI automation" --count 1 --json
    python src/agents/content_writer.py --platform blog --pillar behind_scenes --topic "lead generation" --count 2
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
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
TEMPLATES_DIR = PROJECT_ROOT / "templates" / "content"

PLATFORMS = ("linkedin", "twitter", "newsletter", "blog")
PILLARS = (
    "case_study",
    "behind_scenes",
    "tips_tutorial",
    "social_proof",
    "industry_insight",
    "personal_story",
)

# Platform-specific constraints
PLATFORM_LIMITS = {
    "twitter": {"chars": 280, "threads允": True},
    "linkedin": {"chars": 3000, "hashtags": 5},
    "newsletter": {"words": (800, 2000)},
    "blog": {"words": (1200, 3000)},
}

# Sample data for template filling
SAMPLE_DATA = {
    "client_names": [
        "Sarah Chen", "Marcus Rivera", "Priya Patel",
        "James O'Brien", "Fatima Al-Hassan", "David Kim",
    ],
    "roles": [
        "Founder", "CEO", "Head of Operations",
        "Director", "Managing Partner", "COO",
    ],
    "companies": [
        "GrowthPath", "NovaTech Solutions", "BrightEdge",
        "Catalyst Works", "Summit Digital", "FlowState Inc",
    ],
    "industries": [
        "E-commerce", "SaaS", "Healthcare", "F&B",
        "Professional Services", "Logistics", "Education",
    ],
    "years": ["2", "3", "5", "7", "8", "10", "12"],
    "months": [
        "January", "February", "March", "April", "May", "June",
        "July", "August", "September", "October", "November", "December",
    ],
    "survey_sizes": ["150", "250", "500", "750", "1000", "1500"],
    "client_counts": ["25", "50", "75", "100", "150"],
}


# ---------------------------------------------------------------------------
# Database helpers
# ---------------------------------------------------------------------------

def get_db() -> sqlite3.Connection:
    """Open a connection to the metrics database."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def ensure_tables() -> None:
    """Create content_calendar and agent_activity tables if missing."""
    conn = get_db()
    conn.executescript(
        "CREATE TABLE IF NOT EXISTS content_calendar ("
        "id TEXT PRIMARY KEY, title TEXT NOT NULL, platform TEXT DEFAULT 'linkedin', "
        "status TEXT DEFAULT 'draft', scheduled_at TEXT, published_at TEXT, "
        "engagement_score REAL DEFAULT 0, notes TEXT DEFAULT '', "
        "created_at TEXT DEFAULT (datetime('now')));"
        ""
        "CREATE TABLE IF NOT EXISTS agent_activity ("
        "id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT NOT NULL, "
        "action TEXT NOT NULL, target TEXT DEFAULT '', "
        "status TEXT DEFAULT 'completed', details TEXT DEFAULT '', "
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
        ("content_writer", action, target, status, details),
    )
    conn.commit()
    conn.close()


def save_content(
    content_id: str,
    title: str,
    platform: str,
    notes: str,
    dry_run: bool = False,
) -> bool:
    """Save a content piece to content_calendar. Returns True if saved."""
    if dry_run:
        return False
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO content_calendar (id, title, platform, status, notes) "
        "VALUES (?, ?, ?, 'draft', ?)",
        (content_id, title, platform, notes),
    )
    conn.commit()
    conn.close()
    return True


# ---------------------------------------------------------------------------
# Template engine
# ---------------------------------------------------------------------------

def load_template(pillar: str, platform: str) -> str:
    """Load a template file for the given pillar+platform combination."""
    template_name = f"{pillar}_{platform}.md"
    template_path = TEMPLATES_DIR / template_name
    if not template_path.exists():
        raise FileNotFoundError(
            f"Template not found: {template_path}\n"
            f"Expected template for pillar={pillar}, platform={platform}"
        )
    return template_path.read_text(encoding="utf-8")


def topic_slug(topic: str) -> str:
    """Convert topic to a hashtag-friendly slug."""
    return re.sub(r"[^a-zA-Z0-9]", "", topic).title()


def fill_sample_data(template: str, topic: str) -> str:
    """Fill {{placeholders}} in the template with sample data."""
    data = {
        "topic": topic,
        "topic_slug": topic_slug(topic),
        "count": str(random.randint(4, 7)),
        "client_name": random.choice(SAMPLE_DATA["client_names"]),
        "client_name2": random.choice(SAMPLE_DATA["client_names"]),
        "client_name3": random.choice(SAMPLE_DATA["client_names"]),
        "role": random.choice(SAMPLE_DATA["roles"]),
        "role2": random.choice(SAMPLE_DATA["roles"]),
        "role3": random.choice(SAMPLE_DATA["roles"]),
        "company": random.choice(SAMPLE_DATA["companies"]),
        "company2": random.choice(SAMPLE_DATA["companies"]),
        "company3": random.choice(SAMPLE_DATA["companies"]),
        "industry": random.choice(SAMPLE_DATA["industries"]),
        "industry2": random.choice(SAMPLE_DATA["industries"]),
        "industry3": random.choice(SAMPLE_DATA["industries"]),
        "years": random.choice(SAMPLE_DATA["years"]),
        "month": random.choice(SAMPLE_DATA["months"]),
        "date": datetime.now().strftime("%B %d, %Y"),
        "edition": str(random.randint(1, 48)),
        "survey_size": random.choice(SAMPLE_DATA["survey_sizes"]),
        "client_count": random.choice(SAMPLE_DATA["client_counts"]),
    }

    result = template
    for key, value in data.items():
        result = result.replace(f"{{{{{key}}}}}", value)

    return result


def derive_title(pillar: str, platform: str, topic: str, index: int) -> str:
    """Generate a title for the content piece."""
    pillar_labels = {
        "case_study": "Case Study",
        "behind_scenes": "Behind the Scenes",
        "tips_tutorial": "Tips & Tutorial",
        "social_proof": "Social Proof",
        "industry_insight": "Industry Insight",
        "personal_story": "Personal Story",
    }
    pillar_label = pillar_labels.get(pillar, pillar)
    platform_label = platform.capitalize()

    # Platform-specific title formats
    title_templates = {
        "twitter": f"🧵 Thread: {topic} ({pillar_label}) #{index + 1}",
        "linkedin": f"LinkedIn Post: {topic} — {pillar_label} #{index + 1}",
        "newsletter": f"Newsletter: {topic} ({pillar_label})",
        "blog": f"Blog: {topic} — {pillar_label}",
    }
    return title_templates.get(platform, f"{pillar_label}: {topic}")


def generate_variation(base_content: str, index: int) -> str:
    """Create a slight variation of the base content to avoid duplicates."""
    variations = [
        "",  # original
        "\n\n*Updated with latest insights.*",
        "\n\n🔥 *Brought to you by AgentsFactory*",
        "\n\n*This post was crafted by AI, refined by humans.*",
    ]
    suffix = variations[index % len(variations)]
    return base_content + suffix


# ---------------------------------------------------------------------------
# Content generation
# ---------------------------------------------------------------------------

def generate_content(
    pillar: str,
    platform: str,
    topic: str,
    count: int,
    dry_run: bool = False,
) -> list[dict]:
    """Generate `count` content pieces for the given pillar/platform/topic."""
    template = load_template(pillar, platform)
    filled_base = fill_sample_data(template, topic)

    results = []
    for i in range(count):
        content_id = f"cc_{uuid.uuid4().hex[:12]}"
        title = derive_title(pillar, platform, topic, i)
        content = generate_variation(filled_base, i)

        notes = json.dumps(
            {
                "pillar": pillar,
                "platform": platform,
                "topic": topic,
                "variant": i + 1,
                "generated_at": datetime.now().isoformat(),
                "word_count": len(content.split()),
            },
            ensure_ascii=False,
        )

        saved = False
        if not dry_run:
            saved = save_content(content_id, title, platform, notes)
            log_activity(
                action="generate_content",
                target=title,
                status="completed" if saved else "skipped_duplicate",
                details=f"pillar={pillar}, platform={platform}, topic={topic}, variant={i + 1}",
            )

        results.append(
            {
                "id": content_id,
                "title": title,
                "platform": platform,
                "pillar": pillar,
                "topic": topic,
                "status": "draft" if saved else ("preview" if dry_run else "skipped"),
                "content": content,
                "notes": notes,
            }
        )

    # Log batch summary
    log_activity(
        action="content_batch_complete",
        target=f"{count}x {pillar}/{platform}",
        status="completed",
        details=f"topic={topic}, dry_run={dry_run}",
    )

    return results


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="content_writer",
        description="Content Writer subagent — generates infotainment content for AgentsFactory",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=(
            "Examples:\n"
            '  python src/agents/content_writer.py --platform linkedin --pillar tips_tutorial --topic "Shopify automation" --count 3\n'
            '  python src/agents/content_writer.py --platform twitter --pillar case_study --topic "e-commerce workflows" --dry-run\n'
            '  python src/agents/content_writer.py --platform blog --pillar personal_story --topic "AI automation" --count 2 --json\n'
        ),
    )
    parser.add_argument(
        "--platform",
        required=True,
        choices=PLATFORMS,
        help="Target content platform",
    )
    parser.add_argument(
        "--pillar",
        required=True,
        choices=PILLARS,
        help="Content pillar (topic category)",
    )
    parser.add_argument(
        "--topic",
        required=True,
        help="Content topic (e.g. 'Shopify automation')",
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of content pieces to generate (default: 1)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Preview content without saving to database",
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

    # Validate
    if args.count < 1:
        parser.error("--count must be >= 1")
    if args.count > 20:
        parser.error("--count must be <= 20 (use reasonable batch sizes)")

    # Ensure DB tables exist
    ensure_tables()

    if not args.dry_run:
        print(f"📝 Generating {args.count} content piece(s)...")
        print(f"   Platform : {args.platform}")
        print(f"   Pillar   : {args.pillar}")
        print(f"   Topic    : {args.topic}")
        print()
    else:
        print(f"🔍 DRY RUN — Preview only (not saving)")
        print(f"   Platform : {args.platform}")
        print(f"   Pillar   : {args.pillar}")
        print(f"   Topic    : {args.topic}")
        print()

    try:
        results = generate_content(
            pillar=args.pillar,
            platform=args.platform,
            topic=args.topic,
            count=args.count,
            dry_run=args.dry_run,
        )
    except FileNotFoundError as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        sys.exit(1)

    # Output
    if args.output_json:
        print(json.dumps(results, indent=2, ensure_ascii=False))
    else:
        for i, piece in enumerate(results):
            print(f"{'=' * 60}")
            print(f"  #{i + 1} | {piece['title']}")
            print(f"  ID     : {piece['id']}")
            print(f"  Status : {piece['status']}")
            print(f"  Pillar : {piece['pillar']}")
            print(f"{'=' * 60}")
            print()
            print(piece["content"])
            print()

    # Summary
    saved_count = sum(1 for r in results if r["status"] == "draft")
    print(f"\n✅ Generated {len(results)} piece(s): {saved_count} saved, {len(results) - saved_count} preview-only")
    log_activity(
        action="content_writer_invocation",
        target=f"{args.platform}/{args.pillar}",
        details=f"topic={args.topic}, count={args.count}, dry_run={args.dry_run}",
    )


if __name__ == "__main__":
    main()
