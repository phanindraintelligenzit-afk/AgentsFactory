#!/usr/bin/env python3
"""Deep opportunity scanner — reverse-engineers paid tools for AI agent opportunities."""
import json
from datetime import datetime, timezone, timedelta
from pathlib import Path

IST = timezone(timedelta(hours=5, minutes=30))

TOOL_LANDSCAPE = [
    {"name": "Vanta",        "price": 40000, "cat": "compliance", "desc": "SOC2/ISO compliance automation"},
    {"name": "Drata",        "price": 25000, "cat": "compliance", "desc": "Automated security compliance"},
    {"name": "Drift",        "price": 2500,  "cat": "sales",      "desc": "Conversational marketing/sales AI chat"},
    {"name": "Ironclad",     "price": 5000,  "cat": "legal",      "desc": "Contract lifecycle management"},
    {"name": "Gong",         "price": 10000, "cat": "sales",      "desc": "Conversation intelligence AI for sales"},
    {"name": "Fivetran",     "price": 6000,  "cat": "data",       "desc": "Automated data pipeline / ELT"},
    {"name": "Snyk",         "price": 3000,  "cat": "devtools",   "desc": "Vulnerability scanning in code"},
    {"name": "Zendesk AI",   "price": 5000,  "cat": "support",    "desc": "Customer support AI agents"},
    {"name": "Ada",          "price": 4000,  "cat": "support",    "desc": "AI customer service agent"},
    {"name": "LeanData",     "price": 3000,  "cat": "operations", "desc": "B2B lead-to-account matching"},
    {"name": "Common Room",  "price": 5000,  "cat": "marketing",  "desc": "Community-driven growth platform"},
    {"name": "Apollo",       "price": 3000,  "cat": "sales",      "desc": "Sales intelligence & prospecting"},
    {"name": "Pendo",        "price": 12000, "cat": "analytics",  "desc": "Product analytics & in-app guidance"},
    {"name": "Mixpanel",     "price": 2000,  "cat": "analytics",  "desc": "Product & user analytics"},
    {"name": "Chorus",       "price": 8000,  "cat": "sales",      "desc": "Conversation intelligence"},
    {"name": "Resolve",      "price": 3000,  "cat": "support",    "desc": "Customer service automation"},
    {"name": "Chameleon",    "price": 300,   "cat": "marketing",  "desc": "Onboarding product tours"},
    {"name": "Clearbit",     "price": 3000,  "cat": "sales",      "desc": "Intelligence API for lead scoring"},
]

# Already-built projects (skip these)
PROJECTS_FILE = Path(__file__).resolve().parent.parent / "docs" / "data" / "projects.json"

def load_built_projects():
    if PROJECTS_FILE.exists():
        with open(PROJECTS_FILE) as f:
            return {p["id"] for p in json.load(f).get("projects", [])}
    return set()

def is_already_built(tool_name, built_ids):
    """Check if we already have a project for this tool. Precise keyword matching only."""
    tool_lower = tool_name.lower()
    # Map each tool to EXACT project keywords that would indicate it's already built
    exact_matches = {
        "vanta":       ["soc2", "compliance"],
        "drata":       ["soc2", "compliance"],
        "drift":       ["drift", "conversational"],
        "ironclad":    ["contract", "legal"],
        "gong":        ["gong", "conversation-intelligence", "competitive-intelligence"],
        "chorus":      ["chorus", "conversation-intelligence"],
        "fivetran":    ["fivetran", "data-pipeline", "elt"],
        "snyk":        ["sast", "security", "code-shield"],
        "zendesk ai":  ["zendesk", "support-agent", "customer-support"],
        "ada":         ["ada", "customer-service-agent"],
        "leandata":    ["leandata", "lead-to-account"],
        "common room": ["common-room", "community-growth"],
        "apollo":      ["apollo", "prospecting", "sales-intelligence"],
        "pendo":       ["pendo", "product-analytics"],
        "mixpanel":    ["mixpanel", "user-analytics"],
        "resolve":     ["resolve", "customer-service"],
        "chameleon":   ["chameleon", "product-tour"],
        "clearbit":    ["clearbit", "lead-scoring"],
    }
    keywords = exact_matches.get(tool_lower, [tool_lower.split()[0]])
    for bid in built_ids:
        bid_lower = bid.lower()
        for kw in keywords:
            if kw in bid_lower:
                return True
    return False

def score_opportunity(tool):
    price = tool["price"]
    if price >= 5000:    score = min(88, 55 + int(price / 800))
    elif price >= 1000:  score = min(68, 38 + int(price / 250))
    else:                score = min(50, 25 + int(price / 120))
    ai_ready = ["support", "compliance", "sales", "devtools", "legal", "operations"]
    if tool["cat"] in ai_ready:
        score = min(92, score + 12)
    return score

def generate_solution(tool):
    cat = tool["cat"]
    n = tool["name"]
    solutions = {
        "compliance": f"Open-source {n} alternative — multi-agent SOC2/ISO automation: Scanner finds gaps, Writer drafts evidence, Monitor tracks drift, Auditor generates reports.",
        "sales":      f"AI {n} substitute — Research → Prospect → Outreach → Follow-up agent chain. Personalization at scale without per-seat pricing.",
        "legal":      f"AI contract agent — Parse, redline, risk-score, summarize. Multi-agent: Parser→Reviewer→RiskScorer→Summarizer. Beats {n}'s black-box.",
        "support":    f"AI triage agent — Auto-classify, draft replies, escalate only hard ones. Multi-classifier reduces handle time 60%.",
        "data":       f"Auto pipeline agent — Schema monitoring, transform migration, break detection. Self-healing data infrastructure.",
        "devtools":   f"AI security agent — Continuous dep scanning, auto-patch generation, PR filing. Shifts left without Snyk's per-developer tax.",
        "analytics":  f"Analytics agent — Ingest events, auto-cohorts, insight surfacing. Product intelligence without proprietary SDKs.",
        "marketing":  f"Community agent — Signal monitoring, auto-onboarding, churn prediction. Growth ops without per-contact pricing.",
        "operations": f"Revenue ops agent — Lead-to-account matching, routing, conversion tracking. Replaces manual RevOps busywork."
    }
    return solutions.get(cat, f"AI multi-agent system replicating {n}'s core workflow")

def main():
    built = load_built_projects()
    opportunities = []
    skipped = []

    for tool in TOOL_LANDSCAPE:
        if is_already_built(tool["name"], built):
            skipped.append(tool["name"])
            continue
        price = tool["price"]
        score = score_opportunity(tool)
        opportunities.append({
            "score": score, "tool": tool["name"], "cat": tool["cat"],
            "who": f"SMBs & mid-market doing {tool['cat']}",
            "pay": f"${price:,}/yr" if price >= 1000 else f"${price}/mo",
            "solution": generate_solution(tool),
            "wtp": f"${int(price*0.2)}-${int(price*0.5)}/mo saved" if price < 1000 else f"${int(price*0.2/12)}-${int(price*0.5/12)}/mo saved",
            "effort": "4-6 agents" if tool["cat"] in ["sales","support","compliance","operations"] else "6-8 agents",
            "beat": tool["name"],
            "why": f"{tool['name']} charges ${price:,}/yr for workflow AI agents replicate at near-zero marginal cost. Gap = margin."
        })

    opportunities.sort(key=lambda x: x["score"], reverse=True)

    print("=" * 60)
    print("� AIdentify — Deep Opportunity Scanner")
    print(f"📅 {datetime.now(IST).strftime('%A, %B %d %Y — %I:%M %p IST')}")
    print(f"Scanned {len(TOOL_LANDSCAPE)} paid tools → {len(opportunities)} buildable opportunities")
    if skipped:
        print(f"�️  Skipped (already built): {', '.join(skipped)}")
    print("=" * 60)

    for i, o in enumerate(opportunities[:10], 1):
        icon = "�" if o["score"] >= 70 else "🟡" if o["score"] >= 50 else "🟠"
        print(f"\n{i}. {icon} [{o['score']}/100] REPLACE {o['beat']}")
        print(f"   Pay today: {o['pay']}")
        print(f"   Who: {o['who']}")
        print(f"   AI solution: {o['solution']}")
        print(f"   WTP saved: {o['wtp']}")
        print(f"   Build: {o['effort']}")
        print(f"   Why now: {o['why']}")

    print("\n" + "-" * 60)
    print("Say `build [number]` to start the pipeline.")

if __name__ == "__main__":
    main()
