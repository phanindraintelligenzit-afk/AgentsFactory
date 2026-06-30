#!/usr/bin/env python3
"""
AIdentify Content Calendar — manages a rotating queue of social content.

Post types (rotating, story-driven):
1. PROJECT_SPOTLIGHT — Deep-dive on one marketplace project (agents, problem, code)
2. BUILD_STORY — Behind-the-scenes: how the swarm built something
3. FOUNDER_THOUGHT — Phani's take on AI, agency, Indian tech, building in public
4. QUICK_TIP — Actionable AI/automation tip our audience can use today
5. PROOF_POINT — Metric, milestone, number go up
6. CONTRARIAN_HOT_TAKE — Opinion on AI industry news/trends
7. CROSS_POST — Same story adapted per platform

The calendar queues posts for every 2-3 hours during active hours.
Social poster reads the next item from the queue and schedules it via Ocaya.
"""

import json
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))
MARKETPLACE_URL = "https://phanindraintelligenzit-afk.github.io/AIdentify/docs/marketplace.html"

SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
QUEUE_FILE = SCRIPT_DIR / "content_queue.json"
PROJECTS_FILE = PROJECT_ROOT / "docs" / "data" / "projects.json"

# Active posting window (IST): 8am to 11pm = 15 hours
# Every 2-3 hours = ~5-7 posts/day
POST_HOURS_IST = [8, 11, 14, 17, 20]  # 8am, 11am, 2pm, 5pm, 8pm IST

# --- Content generators ---

def truncate_twitter(text: str, max_chars: int = 280) -> str:
    """Truncate text to Twitter's character limit at a word boundary."""
    if len(text) <= max_chars:
        return text
    truncated = text[:max_chars]
    last_space = truncated.rfind(' ')
    if last_space > max_chars // 2:
        return truncated[:last_space]
    return truncated


def gen_project_spotlight(project: dict) -> dict:
    """Deep-dive on a project."""
    name = project["name"]
    desc = project.get("description", "")
    gh_url = project.get("github_url", "")
    agents_list = project.get("agents_list", [])
    short_desc = desc.split(".")[0][:120]

    twitter = f"Just shipped: {name}\n\n{short_desc}.\n\nBuilt by {len(agents_list)} AI agents working in parallel. No humans touched the code.\n\nOpen source: {gh_url}\nBrowse all: {MARKETPLACE_URL}"

    linkedin = f"We just open-sourced {name}.\n\n{short_desc}.\n\nHere's how the AIdentify agent swarm built it:\n"
    for a in agents_list[:4]:
        linkedin += f"• {a}\n"
    linkedin += f"\nFull source: {gh_url}\nAll projects: {MARKETPLACE_URL}"

    instagram = f"New build: {name}\n\n{short_desc}.\n\nBuilt by {len(agents_list)} AI agents. Open source + free.\n\nLink in bio: {gh_url}"

    facebook = f"Open-sourcing {name} today.\n\n{desc}\n\nBuilt autonomously by our multi-agent AI agency.\n\n{gh_url}\n\nSee the full collection: {MARKETPLACE_URL}"

    return {"type": "PROJECT_SPOTLIGHT", "project_id": project["id"], "name": name,
            "twitter": truncate_twitter(twitter), "linkedin": linkedin,
            "instagram": truncate_twitter(instagram), "facebook": facebook}


def gen_build_story() -> dict:
    """Behind-the-scenes build narrative."""
    stories = [
        {
            "twitter": "Today we published 16 AI agent projects to open source.\n\nZero human-written code.\n\nThe entire pipeline — research, scaffold, build, test, publish — ran autonomously.\n\nHere's how it works:",
            "linkedin": "We just hit 16 open-source AI agent projects on the AIdentify marketplace.\n\nAnd here's the thing: none of them were written by humans.\n\nOur agent swarm operates as a full autonomous pipeline:\n1. Opportunity Scanner finds high-WTP problems\n2. Multi-agent swarm scaffolds and builds\n3. Automated testing validates\n4. Publisher pushes to GitHub + Gumroad\n5. Promotion engine schedules social posts\n\nNo PM meetings. No standups. No code reviews.\n\nThe bottleneck now is scoring opportunities, not building them.",
            "instagram": "16 AI agent projects. Zero human code. All open source.\n\nBuilding the autonomous AI agency.",
            "facebook": "Milestone: 16 AI projects open-sourced in a single week.\n\nAll built autonomously by the AIdentify agent swarm. No human engineers involved in the actual coding.\n\nThis is what the future of software development looks like."
        },
        {
            "twitter": "Hot take: Most 'AI wrappers' aren't slop.\n\nThey're the exact same pattern every successful SaaS used to start.\n\nStripe wrapped bank APIs. Plaid wrapped bank APIs better.\n\nThe winners aren't building new tech. They're wrapping existing tech so well people forget the underlying complexity.",
            "linkedin": "Everyone is rightfully sick of 'AI wrapper' discourse.\n\nBut consider: Stripe was a wrapper around banking infrastructure. Plaid was a wrapper around bank APIs. Shopify was a wrapper around payment + shipping + inventory.\n\nThe pattern hasn't changed. What changed is the wrapping material.\n\nInstead of 6 months of engineering to abstract a complex workflow, a multi-agent swarm does it in hours.\n\nThe wrapper model is the same. The cost of wrapping just dropped 100x.\n\nThis is the opportunity.",
            "instagram": "Stripe wrapped banking. Shopify wrapped logistics.\n\nAI agents wrap complex workflows.\n\nSame pattern. 100x cheaper to build.",
            "facebook": "The 'AI wrapper' critique misses something important.\n\nEvery great SaaS started as a wrapper. Stripe wrapped banking. Shopify wrapped e-commerce infrastructure. Plaid wrapped bank APIs.\n\nWhat AI agents do — that's new — is reduce the cost of wrapping from $500K engineering to a prompt.\n\nThat's not slop. That's leverage."
        },
        {
            "twitter": "Most Indian SaaS companies target US customers.\n\nWe target Indian SMBs who are still doing things manually.\n\nPriya runs a clinic with paper files.\nArjun manages 50 tenants on Excel.\Priya needs compliance help. Arjun needs lead follow-up.\n\nThey're not buying from Salesforce. They're not buying from Zapier.\n\nThey need something they can afford and actually understand.",
            "linkedin": "While everyone chases US enterprise deals, I've been thinking about the Indian SMB market.\n\nThe dentist in Hyderabad managing patient records on paper.\nThe real estate broker in Bangalore tracking leads on WhatsApp.\nThe e-commerce seller in Mumbai reconciling invoices manually.\n\nThese businesses have real willingness to pay. They solve painful daily problems.\n\nThey just don't have $500/month for Salesforce.\n\nThis is where AI agent products win.\n\nOur automation for prior auth workflows starts from �2,999/month.\n\nAffordable. Immediately useful. Built for them.",
            "instagram": "Indian SMBs spend hours daily on manual work.\n\nInvoice matching. Lead follow-up. Compliance.\n\nWe build AI agents for ₹2,999/month that do it automatically.",
            "facebook": "There's a massive unserved market right here in India.\n\nSmall businesses — dental clinics, real estate agencies, e-commerce sellers — doing critical work on paper and Excel.\n\nThey can't afford Salesforce. They don't need enterprise software.\n\nThey need an AI agent that does the boring work for ₹2,999/month.\n\nThat's exactly what we're building at AIdentify."
        },
        {
            "twitter": "Built a SOC2 compliance agent that replaces $20K/year tools.\n\nVanta: $40K/year.\nDrata: $25K/year.\nOur agent: open source.\n\nEvidence collection, control mapping, audit prep — fully automated.\n\nIf you're a startup that needs SOC2 to close enterprise deals, your compliance bill just dropped to $0.",
            "linkedin": "SOC2 compliance costs startups $25-40K/year.\n\nVanta. Drata. Secureframe. Each one charges enterprise prices for what is fundamentally checklist automation.\n\nWe built an open-source SOC2 compliance agent.\n\nIt handles:\n• Continuous evidence collection\n• Control mapping and documentation\n• Auditor-ready report generation\n• Policy templates customized to your stack\n\nTotal cost: $0. It's on GitHub.\n\nFor Indian startups selling to US enterprise — this is the difference between closing and losing deals.",
            "instagram": "SOC2 compliance costs Indian startups $25K/year.\n\nBuilt an open-source AI agent that does it for $0.",
            "facebook": "SOC2 compliance tools charge $25-40K per year.\n\nOur AI agent does the same work — evidence collection, control mapping, audit prep — and it's free on GitHub.\n\nBuilt this because too many good Indian startups lose deals over compliance costs."
        },
    ]
    story = random.choice(stories)
    story["twitter"] = truncate_twitter(story["twitter"])
    story["instagram"] = truncate_twitter(story["instagram"])
    return {"type": "BUILD_STORY", "name": "Behind the Scenes", **story}


def gen_quick_tip() -> dict:
    """Actionable tip the audience can use today."""
    tips = [
        {
            "twitter": "Tip: Use Claude or Cursor to audit your SaaS pricing page.\n\nPrompt: 'Review this pricing page. What's confusing? What would make you hesitate to buy? Give me specific fixes.'\n\nBetter than 90% of CRO audits I've paid for.",
            "linkedin": "Quick growth tip for SaaS founders:\n\nDrop your pricing page into Claude/Cursor and ask:\n\n'Analyze this pricing page. What questions does it leave unanswered? What would make a buyer hesitate? What specific changes would increase conversion?'\n\nThen ask: 'Rewrite this for a skeptical buyer who's comparing us to [competitor].'\n\nTwo minutes. Free. Beats most $2K/month CRO tools.",
            "instagram": "Free CRO audit: Paste your pricing page into Claude.\n\nSay: 'What's confusing? What makes buyers hesitate?'\n\nSame insights as a $2K/month tool.",
            "facebook": "Free alternative to expensive CRO tools.\n\nPaste your pricing page into Claude or Cursor and ask it to find the friction points. It'll spot the gaps in 30 seconds."
        },
        {
            "twitter": "Stop manually sending follow-up emails.\n\nBuild an agent that:\n1. Checks which leads haven't replied in 48h\n2. Reads the previous thread context\n3. Drafts a personalized nudge\n4. Sends it\n\nWe built this for real estate. Works for any outbound.",
            "linkedin": "Every sales team has the same problem: leads go cold because follow-up is manual.\n\nEasy fix — build a lead follow-up agent:\n• Scans unreplied leads every 48 hours\n• Reads conversation history\n• Drafts contextual follow-ups\n• Sends or puts in queue for review\n\nWe built one for real estate lead gen. It's open source.\n\nWorks for any B2B outbound workflow.",
            "instagram": "Stop losing leads to slow follow-up.\n\nAn AI agent can scan, contextualize, and draft nudges automatically.\n\nFree code on our marketplace.",
            "facebook": "Sales teams lose 80% of deals because follow-up takes too long.\n\nAn AI agent can automate the whole flow: check who hasn't replied, draft contextual nudges, send them.\n\nFree templates on our marketplace."
        },
    ]
    tip = random.choice(tips)
    tip["twitter"] = truncate_twitter(tip["twitter"])
    tip["instagram"] = truncate_twitter(tip["instagram"])
    return {"type": "QUICK_TIP", "name": "Tip", **tip}


def gen_contrarian_take() -> dict:
    """Hot take on AI industry."""
    takes = [
        {
            "twitter": "Anthropic is now 'the AI company that doesn't actually build AI products.'\n\nThey build models. OpenAI builds products.\n\nModels are commodities. Products are moats.\n\nThis is why Claude keeps winning benchmarks while ChatGPT keeps winning revenue.",
            "linkedin": "The AI industry has a positioning problem.\n\nAnthropic builds the best models but has no consumer product. OpenAI builds the best products but has a commoditized model.\n\nThe lesson for AI agency founders:\n\nDon't compete on model quality. Compete on workflow depth.\n\nA wrapper around a company's specific approval process is worth more than a general-purpose AI assistant.\n\nThis is why we build agents for specific verticals, not general AI tools.",
            "instagram": "Models get better every month.\n\nProducts with workflow depth stay valuable.\n\nThis is why domain-specific AI agents win.",
            "facebook": "The AI model you use won't matter in 12 months. They all converge.\n\nWhat matters: does your agent understand the specific workflow it's automating?\n\nThat's where we focus — deep domain expertise baked into every agent."
        },
    ]
    take = random.choice(takes)
    take["twitter"] = truncate_twitter(take["twitter"])
    take["instagram"] = truncate_twitter(take["instagram"])
    return {"type": "CONTRARIAN_HOT_TAKE", "name": "Hot Take", **take}


# --- Queue management ---

def load_queue() -> list:
    if QUEUE_FILE.exists():
        return json.loads(QUEUE_FILE.read_text())
    return []

def save_queue(queue: list):
    QUEUE_FILE.write_text(json.dumps(queue, indent=2, default=str))

def generate_daily_queue(projects: list) -> list:
    """Generate today's content queue — 5 posts spread across active hours."""
    queue = []
    
    # Slot 1 (8am): Project spotlight — pick a random project
    p = random.choice(projects)
    item = gen_project_spotlight(p)
    item["scheduled_hour"] = POST_HOURS_IST[0]
    queue.append(item)
    
    # Slot 2 (11am): Build story or hot take
    if random.random() > 0.5:
        item = gen_build_story()
    else:
        item = gen_contrarian_take()
    item["scheduled_hour"] = POST_HOURS_IST[1]
    queue.append(item)
    
    # Slot 3 (2pm): Project spotlight — different project
    remaining = [p for p in projects if p["id"] != queue[0].get("project_id")]
    if not remaining:
        remaining = projects
    p = random.choice(remaining)
    item = gen_project_spotlight(p)
    item["scheduled_hour"] = POST_HOURS_IST[2]
    queue.append(item)
    
    # Slot 4 (5pm): Quick tip
    item = gen_quick_tip()
    item["scheduled_hour"] = POST_HOURS_IST[3]
    queue.append(item)
    
    # Slot 5 (8pm): Build story or hot take
    if random.random() > 0.5:
        item = gen_build_story()
    else:
        item = gen_contrarian_take()
    item["scheduled_hour"] = POST_HOURS_IST[4]
    queue.append(item)
    
    return queue

def get_next_post() -> dict:
    """Get the next post to publish from the queue."""
    queue = load_queue()
    now_ist = datetime.now(IST)
    current_hour = now_ist.hour
    
    # Find the next scheduled post that hasn't been marked as done
    for item in queue:
        if not item.get("done"):
            return item
    
    # All done or empty — regenerate queue for rest of day
    with open(PROJECTS_FILE) as f:
        projects = json.load(f).get("projects", [])
    
    new_queue = generate_daily_queue(projects)
    save_queue(new_queue)
    return new_queue[0] if new_queue else None

def mark_done(item: dict):
    """Mark a queue item as done."""
    queue = load_queue()
    for q in queue:
        if q.get("name") == item.get("name") and q.get("project_id") == item.get("project_id") and q.get("type") == item.get("type"):
            q["done"] = True
            q["posted_at"] = datetime.now(IST).isoformat()
            break
    save_queue(queue)


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--generate":
        with open(PROJECTS_FILE) as f:
            projects = json.load(f).get("projects", [])
        queue = generate_daily_queue(projects)
        save_queue(queue)
        print(f"Generated {len(queue)} posts for today:")
        for q in queue:
            print(f"  {q['scheduled_hour']:02d}:00 IST | {q['type']:20} | {q['name']}")
    else:
        item = get_next_post()
        if item:
            print(json.dumps(item, indent=2, default=str))
        else:
            print("No posts in queue. Run with --generate first.")
