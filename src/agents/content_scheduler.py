"""
Content Scheduler Agent - Automated LinkedIn content pipeline.
Generates, queues, and schedules posts using Ocoya API + AI copy generation.
"""
import sys
import os
import json
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocoya_client import (
    post_to_linkedin,
    schedule_linkedin_post,
    list_posts,
    generate_ai_copy,
)

# ============================================================
# Content pillars for AgentsFactory
# ============================================================

CONTENT_PILLARS = [
    "AI & Automation",
    "E-commerce Growth",
    "SaaS & Tech",
    "Building in Public",
    "Productivity Hacks",
    "Industry Insights",
]

# Post ideas bank - used to generate varied content
POST_IDEAS = {
    "AI & Automation": [
        {"hook": "AI isn't replacing jobs. It's replacing tasks.", "angle": "debunk the fear narrative with data"},
        {"hook": "I replaced 40 hours/week of manual work with 3 AI agents.", "angle": "personal case study"},
        {"hook": "The best automation isn't the most complex. It's the most consistent.", "angle": "simplicity wins"},
        {"hook": "Your competitors are already automating. The question is: how fast can you catch up?", "angle": "urgency"},
        {"hook": "I built an AI agent that finds and qualifies leads while I sleep.", "angle": "lead gen automation"},
    ],
    "E-commerce Growth": [
        {"hook": "E-commerce brands waste 60% of their ad budget on poor targeting.", "angle": "data-driven insight"},
        {"hook": "The #1 reason e-commerce stores don't scale: manual operations.", "angle": "bottleneck identification"},
        {"hook": "Automated follow-ups can recover 15-25% of abandoned carts.", "angle": "cart recovery"},
        {"hook": "Your store runs 24/7. Shouldn't your marketing?", "angle": "always-on automation"},
        {"hook": "From 100 to 10,000 orders/month: what changes?", "angle": "scaling operations"},
    ],
    "SaaS & Tech": [
        {"hook": "SaaS churn is an automation problem, not a product problem.", "angle": "churn reduction"},
        {"hook": "The best SaaS companies automate their customer success.", "angle": "CS automation"},
        {"hook": "Your onboarding takes 14 days. It should take 14 minutes.", "angle": "onboarding automation"},
        {"hook": "API integrations are the glue of modern SaaS.", "angle": "integration value"},
        {"hook": "Stop building features. Start automating workflows.", "angle": "feature vs automation"},
    ],
    "Building in Public": [
        {"hook": "Day {n} of building AgentsFactory. Here's the honest update.", "angle": "progress report"},
        {"hook": "What I thought building an AI agency would be like vs reality.", "angle": "expectations vs reality"},
        {"hook": "The hardest part of building in public? Consistency.", "angle": "consistency challenge"},
        {"hook": "Revenue update: Month 1 of AgentsFactory.", "angle": "transparent metrics"},
        {"hook": "I almost quit building AgentsFactory. Here's why I didn't.", "angle": "resilience story"},
    ],
    "Productivity Hacks": [
        {"hook": "The 2-minute rule doesn't work. Here's what does.", "angle": "productivity system"},
        {"hook": "I track every hour. Here's where the time actually goes.", "angle": "time audit"},
        {"hook": "Stop using to-do lists. Use automation queues instead.", "angle": "automation over lists"},
        {"hook": "The most productive people don't work more. They eliminate more.", "angle": "elimination mindset"},
        {"hook": "Your calendar is lying to you about your productivity.", "angle": "calendar audit"},
    ],
    "Industry Insights": [
        {"hook": "The AI agency model is broken. Here's how to fix it.", "angle": "industry critique"},
        {"hook": "Why 90% of automation projects fail (and how to be the 10%).", "angle": "failure analysis"},
        {"hook": "The future of work isn't remote. It's automated.", "angle": "future of work"},
        {"hook": "India's IT services industry is about to be disrupted.", "angle": "market disruption"},
        {"hook": "Every company will be an AI company by 2027. Most aren't ready.", "angle": "prediction"},
    ],
}

# Hashtag sets per pillar
HASHTAGS = {
    "AI & Automation": ["AIAgents", "Automation", "ArtificialIntelligence", "MachineLearning"],
    "E-commerce Growth": ["Ecommerce", "EcommerceGrowth", "D2C", "Shopify"],
    "SaaS & Tech": ["SaaS", "TechStartup", "B2B", "ProductLed"],
    "Building in Public": ["BuildingInPublic", "StartupLife", "IndieHacker", "Bootstrapped"],
    "Productivity Hacks": ["Productivity", "TimeManagement", "WorkSmarter", "Efficiency"],
    "Industry Insights": ["TechTrends", "FutureOfWork", "Innovation", "DigitalTransformation"],
}


def generate_post(pillar: str = None, day_count: int = 1) -> str:
    """Generate a LinkedIn post for a given content pillar."""
    if not pillar:
        pillar = random.choice(CONTENT_PILLARS)

    ideas = POST_IDEAS.get(pillar, POST_IDEAS["AI & Automation"])
    idea = random.choice(ideas)
    tags = HASHTAGS.get(pillar, ["AIAgents", "Automation"])
    tag1, tag2 = random.sample(tags, min(2, len(tags)))

    hook = idea["hook"].replace("{n}", str(day_count))
    angle = idea["angle"]

    # Build the post based on angle
    post = f"{hook}\n\n"

    # Add body based on pillar
    bodies = {
        "AI & Automation": [
            "I've been building AI agents for the past few weeks, and the results are staggering.\n\nOne agent scans 100+ prospects in minutes.\nAnother drafts content while I focus on strategy.\nA third handles engagement 24/7.\n\nThe key isn't building one perfect agent.\nIt's orchestrating many simple ones.\n\nWhat's the most repetitive task in your business?",
            "Here's what most people get wrong about AI automation:\n\nThey try to automate everything at once.\n\nStart with the ONE task that eats the most time.\nAutomate that. Measure the impact.\nThen move to the next.\n\nCompound automation > big bang automation.",
        ],
        "E-commerce Growth": [
            "I audited an e-commerce store last month.\n\nThey were spending:\n→ 15 hrs/week on order tracking\n→ 10 hrs/week on customer follow-ups\n→ 8 hrs/week on inventory updates\n\nWe automated 80% of it.\n\nResult: 26 hours/week saved. ₹80K/month recovered.\n\nWhat would you do with 26 extra hours?",
        "The e-commerce brands winning in 2025 all have one thing in common:\n\nThey've automated the boring stuff.\n\n→ Order processing\n→ Customer segmentation\n→ Abandoned cart recovery\n→ Review requests\n→ Inventory alerts\n\nThe founders? They focus on growth.\n\nAutomation isn't optional anymore.",
        ],
    }

    body_options = bodies.get(pillar, [
        f"Here's the thing about {pillar.lower()}:\n\nMost people overcomplicate it.\n\nThe best approach is usually the simplest:\n1. Identify the bottleneck\n2. Automate the repeatable parts\n3. Keep the human touch where it matters\n\nI've seen this pattern across 50+ businesses.\n\nThe ones that scale are the ones that automate early.\n\nWhat's your biggest operational bottleneck right now?",
        f"Let me save you 6 months of trial and error with {pillar.lower()}:\n\n→ Start small. One process. One agent.\n→ Measure everything. If you can't measure it, you can't improve it.\n→ Iterate fast. Kill what doesn't work.\n→ Scale what does. Compound the wins.\n\nThis is the framework I use for every automation project.\n\nIt works. Every time.",
    ])

    post += random.choice(body_options)
    post += f"\n\n#{tag1} #{tag2} #AgentsFactory"

    return post


def schedule_weekly_posts(posts_per_day: int = 1, days_ahead: int = 7) -> list[dict]:
    """
    Schedule a full week of LinkedIn posts.
    Spreads posts across the week at optimal times.
    """
    # Optimal LinkedIn posting times (IST): 9 AM, 12 PM, 5 PM
    optimal_hours = [9, 12, 17]  # IST

    results = []
    today = datetime.now(timezone(timedelta(hours=5, minutes=30)))  # IST

    for day_offset in range(days_ahead):
        day_time = today + timedelta(days=day_offset)
        day_name = day_time.strftime("%A")

        for post_num in range(posts_per_day):
            # Pick a pillar (rotate through them)
            pillar_index = (day_offset * posts_per_day + post_num) % len(CONTENT_PILLARS)
            pillar = CONTENT_PILLARS[pillar_index]

            # Generate post
            post_text = generate_post(pillar=pillar, day_count=day_offset + 1)

            # Schedule time
            hour = optimal_hours[post_num % len(optimal_hours)]
            scheduled_time = day_time.replace(hour=hour, minute=0, second=0, microsecond=0)

            # Don't schedule in the past
            if scheduled_time < today:
                scheduled_time += timedelta(hours=1)

            # Schedule via Ocoya
            result = schedule_linkedin_post(
                post_text,
                hours_from_now=(scheduled_time - today).total_seconds() / 3600
            )

            results.append({
                "day": day_name,
                "pillar": pillar,
                "scheduled": scheduled_time.strftime("%Y-%m-%d %H:%M IST"),
                "result": result,
                "preview": post_text[:80] + "...",
            })
            print(f"✅ Scheduled: {day_name} - {pillar} - {scheduled_time.strftime('%H:%M IST')}")

    return results


def get_content_calendar() -> dict:
    """Get the current content calendar with scheduled posts."""
    try:
        posts = list_posts(limit=100)
        calendar = {}
        for post in posts:
            # Parse scheduled time
            sched = post.get("scheduledAt", post.get("created_at", ""))
            if sched:
                try:
                    dt = datetime.fromisoformat(sched.replace("Z", "+00:00"))
                    dt_ist = dt.astimezone(timezone(timedelta(hours=5, minutes=30)))
                    day = dt_ist.strftime("%A")
                    calendar[day] = calendar.get(day, 0) + 1
                except:
                    pass
        return calendar
    except Exception as e:
        return {"error": str(e)}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Content Scheduler Agent")
    parser.add_argument("--generate", action="store_true", help="Generate a sample post")
    parser.add_argument("--pillar", type=str, help="Content pillar for generation")
    parser.add_argument("--schedule-week", action="store_true", help="Schedule a full week of posts")
    parser.add_argument("--posts-per-day", type=int, default=1, help="Posts per day")
    parser.add_argument("--calendar", action="store_true", help="Show content calendar")
    args = parser.parse_args()

    if args.generate:
        post = generate_post(pillar=args.pillar)
        print(post)
    elif args.schedule_week:
        results = schedule_weekly_posts(posts_per_day=args.posts_per_day)
        print(f"\n✅ Scheduled {len(results)} posts")
    elif args.calendar:
        cal = get_content_calendar()
        print(json.dumps(cal, indent=2))
    else:
        print("Content Scheduler Agent ready. Use --help for options.")
