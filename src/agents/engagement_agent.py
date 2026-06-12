"""
Engagement Agent - Automated LinkedIn engagement via Ocoya.
Handles comment-to-DM, post engagement, and lead nurturing.
"""
import sys
import os
import json
import time
import random
from datetime import datetime, timezone, timedelta

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ocoya_client import (
    post_to_linkedin,
    create_post,
    list_posts,
    LINKEDIN_PROFILE_ID,
)

# ============================================================
# Engagement templates
# ============================================================

COMMENT_TEMPLATES = [
    "Great point about {topic}! We're seeing the same trend with our clients.",
    "This is spot on. {follow_up_question}",
    "Interesting perspective. Have you tried {suggestion}?",
    "Thanks for sharing this. {value_add}",
    "Love this. We built something similar for {use_case}.",
]

ENGAGEMENT_DM_TEMPLATES = [
    "Hey {name}! Saw your comment on my post about {topic}. Would love to connect and share what we're building at AgentsFactory. Quick chat?",
    "Hi {name}, your insight on {topic} was great. I'm building AI automation for businesses — would you be open to a quick call?",
    "Hey {name}! Thanks for engaging with my content. I noticed you're in {industry}. We help companies like yours automate {pain_point}. Worth a conversation?",
]

FOLLOW_UP_TEMPLATES = [
    "Hey {name}, just following up on my previous message. Would love to hear your thoughts on {topic}.",
    "Hi {name}, I know things get busy. Just wanted to bump this up — quick 15-min chat about {topic}?",
]


def engage_with_post(post_url: str, comment: str) -> dict:
    """
    Comment on a LinkedIn post.
    Note: Ocoya API supports posting. For engagement (liking/commenting on others' posts),
    we use the comment-to-DM feature or direct API calls.
    """
    # This uses Ocoya's comment feature
    result = create_post(
        caption=comment,
        social_profile_ids=[LINKEDIN_PROFILE_ID],
    )
    return result


def send_engagement_dm(name: str, topic: str, industry: str = "tech", pain_point: str = "manual work") -> str:
    """Generate a personalized engagement DM."""
    template = random.choice(ENGAGEMENT_DM_TEMPLATES)
    return template.format(
        name=name,
        topic=topic,
        industry=industry,
        pain_point=pain_point,
    )


def generate_comment(topic: str) -> str:
    """Generate a thoughtful comment on a topic."""
    template = random.choice(COMMENT_TEMPLATES)
    follow_up_questions = [
        "What tools are you using for this?",
        "How are you measuring the impact?",
        "What's been your biggest challenge?",
        "How long did it take to see results?",
    ]
    suggestions = [
        "automating the follow-up process",
        "using AI for the initial research",
        "building a simple workflow first",
        "tracking the metrics more closely",
    ]
    value_adds = [
        "We've been working on something similar.",
        "This aligns with what we're seeing in the market.",
        "I've seen this pattern across multiple industries.",
        "This is exactly what our clients need.",
    ]
    use_cases = [
        "e-commerce brands",
        "SaaS companies",
        "local businesses",
        "marketing agencies",
    ]

    return template.format(
        topic=topic,
        follow_up_question=random.choice(follow_up_questions),
        suggestion=random.choice(suggestions),
        value_add=random.choice(value_adds),
        use_case=random.choice(use_cases),
    )


def create_engagement_post() -> dict:
    """
    Create an engagement-optimized post (question, poll, hot take).
    These get more comments and reach.
    """
    engagement_posts = [
        "🤔 What's the #1 repetitive task in your business that you wish was automated?\n\nDrop it in the comments — I'll share how I'd automate it.\n\n#Automation #AIAgents #Productivity",
        "🔥 Hot take: By 2026, every business will have at least one AI agent.\n\nNot a chatbot. Not a tool. An actual agent that takes actions.\n\nAgree or disagree? 👇\n\n#AIAgents #FutureOfWork #Automation",
        "Quick poll: What's your biggest bottleneck right now?\n\nA) Lead generation\nB) Customer follow-up\nC) Content creation\nD) Operations & logistics\n\nComment with your answer 👇\n\n#BusinessGrowth #Automation",
        "I'm going to say what everyone's thinking:\n\nMost 'AI solutions' are just fancy chatbots.\n\nReal AI automation is:\n→ Agents that take actions\n→ Workflows that run 24/7\n→ Systems that learn and improve\n\nThe difference matters.\n\nAgree? 👇\n\n#AIAgents #ArtificialIntelligence #Automation",
        "💡 Unpopular opinion:\n\nYou don't need more tools. You need fewer tools that talk to each other.\n\nThe best automation isn't adding another SaaS.\n\nIt's connecting what you already have.\n\nThoughts? 👇\n\n#Automation #SaaS #Integration",
    ]

    post_text = random.choice(engagement_posts)
    return post_to_linkedin(post_text)


def run_engagement_cycle() -> dict:
    """
    Run a full engagement cycle:
    1. Post an engagement-optimized post
    2. Generate comments for target posts
    3. Track engagement metrics
    """
    results = {
        "timestamp": datetime.now(timezone(timedelta(hours=5, minutes=30))).isoformat(),
        "actions": [],
    }

    # Step 1: Create an engagement post (every other day)
    if datetime.now().day % 2 == 0:
        post_result = create_engagement_post()
        results["actions"].append({
            "type": "engagement_post",
            "result": post_result,
        })
        print(f"✅ Engagement post created: {post_result.get('postGroupId', 'N/A')}")

    # Step 2: Get recent post stats
    try:
        posts = list_posts(limit=20)
        results["actions"].append({
            "type": "post_stats",
            "total_posts": len(posts),
        })
    except Exception as e:
        results["actions"].append({
            "type": "post_stats",
            "error": str(e),
        })

    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Engagement Agent")
    parser.add_argument("--engage", action="store_true", help="Run engagement cycle")
    parser.add_argument("--comment", type=str, help="Generate a comment on a topic")
    parser.add_argument("--dm", type=str, help="Generate a DM for a person (name)")
    parser.add_argument("--engagement-post", action="store_true", help="Create an engagement post")
    args = parser.parse_args()

    if args.engage:
        results = run_engagement_cycle()
        print(json.dumps(results, indent=2))
    elif args.comment:
        comment = generate_comment(args.comment)
        print(comment)
    elif args.dm:
        dm = send_engagement_dm(args.dm, "AI automation")
        print(dm)
    elif args.engagement_post:
        result = create_engagement_post()
        print(json.dumps(result, indent=2))
    else:
        print("Engagement Agent ready. Use --help for options.")
