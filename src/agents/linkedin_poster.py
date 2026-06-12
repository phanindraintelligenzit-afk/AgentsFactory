"""
LinkedIn Poster Agent - Uses Ocoya API for fully automated LinkedIn posting.
Creates, schedules, and publishes LinkedIn posts with zero manual work.
"""
import sys
import os
import random
import json
from datetime import datetime, timezone, timedelta

# Add parent dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocoya_client import (
    post_to_linkedin,
    schedule_linkedin_post,
    list_posts,
    generate_ai_copy,
    LINKEDIN_PROFILE_ID,
)

# ============================================================
# LinkedIn post templates for AgentsFactory
# ============================================================

POST_TEMPLATES = {
    "infotainment": [
        "💡 {insight}\n\n{hook}\n\n{call_to_action}\n\n#AIAgents #Automation #{tag1} #{tag2}",
        "Most {audience} don't realize this:\n\n{insight}\n\n{hook}\n\n{call_to_action}\n\n#BuildingInPublic #{tag1} #Automation",
        "🤖 {hook}\n\n{insight}\n\n{call_to_action}\n\n#AIAgents #{tag1} #Tech",
    ],
    "storytelling": [
        "Day {day_count} of building AgentsFactory.\n\n{story}\n\n{lesson}\n\n{question}\n\n#BuildingInPublic #StartupLife #{tag1}",
        "I built {thing} in {timeframe}.\n\nHere's what happened:\n\n{story}\n\n{lesson}\n\n#AIAgents #Automation #StartupJourney",
    ],
    "value_bomb": [
        "5 things I learned building an AI agency from scratch:\n\n{points}\n\nWhich one resonates? 👇\n\n#AIAgents #Entrepreneurship #{tag1}",
        "Stop doing {bad_thing}.\n\nDo this instead:\n\n{better_approach}\n\n{why_it_works}\n\n#Automation #{tag1} #Productivity",
    ],
    "engagement": [
        "🔥 Hot take: {controversial_opinion}\n\nAgree or disagree? 👇\n\n#AIAgants #{tag1} #Tech",
        "Unpopular opinion:\n\n{opinion}\n\n{reasoning}\n\nThoughts? 👇\n\n#{tag1} #BuildingInPublic",
    ],
}

CONTENT_CALENDAR = {
    "Monday":    {"type": "value_bomb", "topic": "productivity"},
    "Tuesday":   {"type": "infotainment", "topic": "AI/automation"},
    "Wednesday": {"type": "storytelling", "topic": "journey"},
    "Thursday":  {"type": "infotainment", "topic": "ecommerce/SaaS"},
    "Friday":    {"type": "engagement", "topic": "industry hot take"},
    "Saturday":  {"type": "value_bomb", "topic": "tips/lessons"},
    "Sunday":    {"type": "storytelling", "topic": "reflection"},
}

# Pre-written posts for the launch week
LAUNCH_POSTS = [
    {
        "caption": "I'm building an AI automation agency from scratch.\n\nNot with a team of 50. Not with VC funding.\n\nJust me and my AI agents.\n\nHere's what AgentsFactory looks like at Day 1:\n→ 8 AI subagents running operations\n→ Lead finder scanning for prospects\n→ Content writer drafting posts\n→ LinkedIn agent engaging targets\n→ Outreach agent sending 100 DMs/day\n→ Daily briefings at 8 AM\n→ Command Center dashboard tracking everything\n\nThe vision: An AI agency that runs itself.\nThe reality: Still a lot of manual work. 😅\n\nIf you run a business drowning in manual work — I want to talk.\n\nDrop a comment or DM me.\n\n#BuildingInPublic #AIAgents #Automation #SaaS",
        "scheduled_hours": 0,
    },
    {
        "caption": "Day 3 of building AgentsFactory:\n\nOpportunity cost is the most expensive thing in business.\n\nEvery hour your team spends on manual work:\n→ Data entry\n→ Lead research\n→ Social media posting\n→ Follow-ups\n→ Report generation\n\n…is an hour NOT spent on growth.\n\nI calculated this for an e-commerce client:\n→ 32 hours/week on repeatable tasks\n→ ₹1.2L/month in wasted productivity\n\nWe automated 80% of it in 2 weeks.\n\nWhat could your team do with 25+ extra hours per week?\n\n#Automation #AIAgents #Productivity #Ecommerce",
        "scheduled_hours": 4,
    },
    {
        "caption": "The biggest lie in tech right now:\n\n\"AI will replace your job.\"\n\nWrong.\n\nAI will replace the BORING parts of your job.\n\nHere's what I've seen after building 8 AI agents:\n\n✅ Research agents that scan 100+ prospects in minutes\n✅ Writing agents that draft posts, emails, reports\n✅ Engagement agents that nurture leads 24/7\n✅ Automation agents that connect your tools\n\nThe humans who thrive will be the ones who LEARN to direct these agents.\n\nStop fearing AI. Start orchestrating it.\n\nAgree? 👇\n\n#AIAgants #FutureOfWork #Automation",
        "scheduled_hours": 8,
    },
]


def create_launch_posts() -> list[dict]:
    """Create all launch week posts. Returns list of results."""
    results = []
    for post in LAUNCH_POSTS:
        if post["scheduled_hours"] == 0:
            result = post_to_linkedin(post["caption"])
        else:
            result = schedule_linkedin_post(post["caption"], hours_from_now=post["scheduled_hours"])
        results.append({"post": post["caption"][:60] + "...", "result": result})
        print(f"✅ Posted: {results[-1]['post']}")
    return results


def post_linkedin_update(text: str, schedule_hours: float = None) -> dict:
    """Post a LinkedIn update. If schedule_hours is set, schedules for later."""
    if schedule_hours:
        return schedule_linkedin_post(text, schedule_hours)
    return post_to_linkedin(text)


def get_post_stats() -> dict:
    """Get stats on recent posts."""
    try:
        posts = list_posts(limit=50)
        return {
            "total_posts": len(posts),
            "recent": posts[:5] if posts else [],
        }
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="LinkedIn Poster Agent")
    parser.add_argument("--launch", action="store_true", help="Post all launch posts")
    parser.add_argument("--post", type=str, help="Post a specific message")
    parser.add_argument("--schedule", type=str, help="Schedule a message")
    parser.add_argument("--hours", type=float, default=1, help="Hours from now to schedule")
    parser.add_argument("--stats", action="store_true", help="Show post stats")
    args = parser.parse_args()

    if args.launch:
        results = create_launch_posts()
        print(json.dumps(results, indent=2))
    elif args.post:
        result = post_to_linkedin(args.post)
        print(json.dumps(result, indent=2))
    elif args.schedule:
        result = schedule_linkedin_post(args.schedule, args.hours)
        print(json.dumps(result, indent=2))
    elif args.stats:
        stats = get_post_stats()
        print(json.dumps(stats, indent=2))
    else:
        print("LinkedIn Poster Agent ready. Use --help for options.")
