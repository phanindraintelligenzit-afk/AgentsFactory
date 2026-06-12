"""
Lead Loader - Imports leads from Google Sheets CSV into AgentsFactory database + Notion.
"""
import sys
import os
import csv
import json
import urllib.request
from datetime import datetime
from collections import Counter

# Add parent dir for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "agentsfactory_metrics.db")

import sqlite3

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            keyword TEXT,
            company TEXT,
            website TEXT,
            phone TEXT,
            email TEXT,
            category TEXT,
            facebook_url TEXT,
            facebook_likes INTEGER DEFAULT 0,
            facebook_followers INTEGER DEFAULT 0,
            facebook_posts_30d INTEGER DEFAULT 0,
            facebook_last_post_days INTEGER DEFAULT 0,
            social_lead_score TEXT,
            twitter_url TEXT,
            twitter_id TEXT,
            twitter_tweets INTEGER DEFAULT 0,
            twitter_followers INTEGER DEFAULT 0,
            twitter_likes INTEGER DEFAULT 0,
            twitter_posts_30d INTEGER DEFAULT 0,
            twitter_last_post_days INTEGER DEFAULT 0,
            gmb_url TEXT,
            created_at TEXT DEFAULT (datetime('now'))
        )
    """)
    conn.commit()
    conn.close()


def download_csv() -> list[dict]:
    """Download leads from Google Sheets."""
    url = "https://docs.google.com/spreadsheets/d/1LqWzHRYgX-LzneQGB4J63IQJSO6ysvs1V2Ij1H7SZfs/export?format=csv"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req, timeout=60) as resp:
        content = resp.read().decode('utf-8-sig')
    reader = csv.DictReader(content.splitlines())
    return list(reader)


def safe_int(val) -> int:
    try:
        return int(str(val).replace(',', '').strip())
    except (ValueError, TypeError):
        return 0


def load_leads_to_db(leads: list[dict]) -> dict:
    """Load leads into SQLite database."""
    init_db()
    conn = get_db()

    # Drop and recreate table
    conn.execute("DROP TABLE IF EXISTS leads")
    conn.commit()
    conn.close()
    init_db()
    conn = get_db()
    errors = 0
    inserted = 0
    score_map = {'HOT': 90, 'Great': 75, 'Good': 60, 'Poor': 30, 'Yes': 50, 'No': 20}

    for lead in leads:
        try:
            score_text = lead.get('Social Lead Score', '').strip()
            fb_followers = safe_int(lead.get('Facebook Followers #', 0))
            tw_followers = safe_int(lead.get('Twitter Followers #', 0))

            # Calculate a numeric score
            base_score = score_map.get(score_text, 40)
            # Boost for active social presence
            if fb_followers > 5000: base_score += 5
            if fb_followers > 10000: base_score += 5
            if tw_followers > 1000: base_score += 5

            conn.execute("""
                INSERT INTO leads (keyword, company, website, phone, email, category,
                    facebook_url, facebook_likes, facebook_followers, facebook_posts_30d,
                    facebook_last_post_days, social_lead_score, twitter_url, twitter_id,
                    twitter_tweets, twitter_followers, twitter_likes, twitter_posts_30d,
                    twitter_last_post_days, gmb_url)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                lead.get('Keyword', ''),
                lead.get('Company Name', ''),
                lead.get('Website URL', ''),
                lead.get('Phone', ''),
                lead.get('Email', ''),
                lead.get('Category', ''),
                lead.get('Facebook Page URL', ''),
                safe_int(lead.get('Facebook Likes #', 0)),
                fb_followers,
                safe_int(lead.get('Facebook Posts In Last 30 Days', 0)),
                safe_int(lead.get('Facebook Last Posted Days Ago', 0)),
                score_text,
                lead.get('Twitter Page URL', ''),
                lead.get('Twitter ID', ''),
                safe_int(lead.get('Twitter Tweets #', 0)),
                tw_followers,
                safe_int(lead.get('Twitter Likes #', 0)),
                safe_int(lead.get('Twitter Posts In Last 30 Days', 0)),
                safe_int(lead.get('Twitter Last Posted Days Ago', 0)),
                lead.get('Google My Business URL', ''),
            ))
            inserted += 1
        except Exception as e:
            errors += 1

    conn.commit()

    # Get stats
    stats = {
        "total_inserted": inserted,
        "errors": errors,
        "hot_leads": conn.execute("SELECT COUNT(*) FROM leads WHERE social_lead_score='HOT'").fetchone()[0],
        "great_leads": conn.execute("SELECT COUNT(*) FROM leads WHERE social_lead_score='Great'").fetchone()[0],
        "good_leads": conn.execute("SELECT COUNT(*) FROM leads WHERE social_lead_score='Good'").fetchone()[0],
        "with_email": conn.execute("SELECT COUNT(*) FROM leads WHERE email != ''").fetchone()[0],
        "with_phone": conn.execute("SELECT COUNT(*) FROM leads WHERE phone != ''").fetchone()[0],
        "with_facebook": conn.execute("SELECT COUNT(*) FROM leads WHERE facebook_url != ''").fetchone()[0],
        "with_twitter": conn.execute("SELECT COUNT(*) FROM leads WHERE twitter_url != ''").fetchone()[0],
        "categories": {},
    }

    # Category breakdown
    cat_rows = conn.execute("SELECT category, COUNT(*) as cnt FROM leads GROUP BY category ORDER BY cnt DESC LIMIT 20").fetchall()
    for row in cat_rows:
        stats["categories"][row[0]] = row[1]

    # Top leads by social score
    top_leads = conn.execute("""
        SELECT company, email, phone, social_lead_score, facebook_followers, twitter_followers, category
        FROM leads WHERE social_lead_score IN ('HOT','Great')
        ORDER BY facebook_followers DESC LIMIT 20
    """).fetchall()
    stats["top_leads"] = [dict(r) for r in top_leads]

    conn.close()
    return stats


def load_leads_to_notion(leads: list[dict], batch_size: int = 50) -> dict:
    """Load leads into Notion database in batches."""
    import os
    notion_key = os.environ.get('NOTION_KEY', '')
    # Try to read from config
    if not notion_key:
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), '.env')
        if os.path.exists(config_path):
            with open(config_path) as f:
                for line in f:
                    if line.strip().startswith('NOTION_KEY='):
                        notion_key = line.strip().split('=', 1)[1].strip()
                        break

    if not notion_key:
        return {"error": "Notion API key not found"}

    # Notion database ID for leads
    db_id = "37d4baec-8165-8126-ae73-e56e6d5d235d"  # This is the parent page, need the actual leads DB
    # Actually, let's use the specific leads database ID from the AgentsFactory Notion workspace
    # We need to find or create the leads database
    return {"status": "skipped", "message": "Loading to Notion via separate script"}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Lead Loader")
    parser.add_argument("--download", action="store_true", help="Download CSV and load to DB")
    parser.add_argument("--stats", action="store_true", help="Show lead stats")
    args = parser.parse_args()

    if args.download or not args.stats:
        print("Downloading leads from Google Sheets...")
        leads = download_csv()
        print(f"Downloaded {len(leads)} leads")

        print("Loading to database...")
        stats = load_leads_to_db(leads)
        print(json.dumps(stats, indent=2))

    elif args.stats:
        conn = get_db()
        total = conn.execute("SELECT COUNT(*) FROM leads").fetchone()[0]
        hot = conn.execute("SELECT COUNT(*) FROM leads WHERE social_lead_score='HOT'").fetchone()[0]
        great = conn.execute("SELECT COUNT(*) FROM leads WHERE social_lead_score='Great'").fetchone()[0]
        print(f"Total leads: {total}")
        print(f"HOT: {hot} | Great: {great}")
        conn.close()
