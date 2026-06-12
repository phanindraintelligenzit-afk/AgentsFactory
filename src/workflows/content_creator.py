"""
Workflow 1: Turn One Idea Into a Week's Worth of Content
Based on Rick Mulready's Hermes Agent prompt.

Usage:
    python workflows/content_creator.py --idea "Your YouTube video idea here"
    python workflows/content_creator.py --interactive
"""
import sys
import os
import json
import argparse
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src", "agents"))
from content_scheduler import generate_post
from ocoya_client import post_to_linkedin, schedule_linkedin_post


def content_creator_workflow(idea: str) -> dict:
    """
    Turn one idea into a full week of content.
    Returns a dict with all content pieces.
    """
    results = {
        "idea": idea,
        "timestamp": datetime.now().isoformat(),
        "youtube_outline": "",
        "newsletter_draft": "",
        "linkedin_posts": [],
        "short_form_ideas": [],
        "review_notes": "",
    }

    print(f"🎬 Content Creator Workflow")
    print(f"Idea: {idea}")
    print("=" * 60)

    # Step 1: YouTube Outline
    print("\n📹 Step 1: Creating YouTube outline...")
    results["youtube_outline"] = f"""
# YouTube Video Outline: {idea}

## Hook (0:00-0:30)
- Open with a surprising statement or question related to: {idea}
- Promise the viewer what they'll learn

## Introduction (0:30-2:00)
- Brief context on why this matters now
- Your credibility/experience with this topic
- What they'll walk away with

## Main Content (2:00-15:00)
### Point 1: The Problem
- Why most people struggle with this
- Common mistakes to avoid

### Point 2: The Framework
- Your unique approach to solving this
- Step-by-step breakdown

### Point 3: Real Examples
- Case study or personal story
- Before/after comparison

### Point 4: Implementation
- How to apply this today
- Quick wins vs long-term strategy

## Conclusion (15:00-16:00)
- Recap key points
- Call to action (subscribe, comment, check link)
- Tease next video

## Description Template
In this video, I cover {idea.lower()}. You'll learn:
- Why this matters for your business
- The exact framework I use
- How to implement it starting today

🔗 Links mentioned:
- [Your landing page]
- [Related resources]

#YouTube #Tutorial #{idea.replace(' ', '')}
"""
    print("  ✅ YouTube outline created")

    # Step 2: Newsletter Draft
    print("\n📧 Step 2: Creating newsletter draft...")
    results["newsletter_draft"] = f"""
Subject: The one thing I learned about {idea.lower()} that changed everything

Hey [Name],

Last week I recorded a video about {idea.lower()}, and something unexpected happened.

[Personal story or insight about the topic]

Here's what I learned:

1. **The obvious thing isn't always right**
   Most people approach this wrong because they focus on [common mistake].

2. **The real leverage is in [key insight]**
   When you shift your focus here, everything gets easier.

3. **Start small, but start today**
   You don't need to overhaul everything. Pick one thing from this email and try it this week.

I go deeper in my latest video — link below.

[Watch the video →]

Talk soon,
[Your name]

P.S. If you found this useful, forward it to someone who needs to hear it.
"""
    print("  ✅ Newsletter draft created")

    # Step 3: LinkedIn Posts
    print("\n💼 Step 3: Creating LinkedIn posts...")
    post_templates = [
        f"I spent this week thinking about {idea.lower()}.\n\nHere's the one thing most people get wrong:\n\nThey focus on [surface-level solution] instead of [root cause].\n\nThe fix is simpler than you think:\n\n1. [Action step 1]\n2. [Action step 2]\n3. [Action step 3]\n\nI recorded a full video breaking this down. Link in comments.\n\nWhat's your experience with this? 👇\n\n#{idea.replace(' ', '')} #BusinessGrowth",

        f"Hot take: {idea.lower()} is the most underrated skill in business right now.\n\nI see companies waste thousands of hours on [problem] when the solution is actually straightforward.\n\nThe framework I use:\n\n→ Step 1: [Brief description]\n→ Step 2: [Brief description]\n→ Step 3: [Brief description]\n\nResult: [Specific outcome]\n\nFull breakdown in my latest video. Link in comments 👇\n\n#AIAgents #Automation #{idea.replace(' ', '')}",

        f"3 things I learned about {idea.lower()} this week:\n\n1️⃣ Most people overcomplicate it. The best solution is usually the simplest.\n\n2️⃣ Consistency beats intensity. Small daily actions > occasional big pushes.\n\n3️⃣ You need a system, not just motivation. Systems survive when motivation fades.\n\nI'm building AI agents to handle exactly this kind of work for businesses.\n\nIf you're drowning in manual work, let's talk. DM me.\n\n#BuildingInPublic #AIAgents #Automation"
    ]
    results["linkedin_posts"] = post_templates
    print(f"  ✅ {len(post_templates)} LinkedIn posts created")

    # Step 4: Short-form Video Ideas
    print("\n📱 Step 4: Creating short-form video ideas...")
    results["short_form_ideas"] = [
        {
            "platform": "Reels/Shorts",
            "hook": f"The #1 mistake people make with {idea.lower()}",
            "format": "Talking text overlay, 30-60 seconds",
            "cta": "Follow for more tips"
        },
        {
            "platform": "Reels/Shorts",
            "hook": f"I saved 10 hours/week by automating {idea.lower()}",
            "format": "Before/after comparison, screen recording",
            "cta": "Link in bio for the full tutorial"
        },
        {
            "platform": "Reels/Shorts",
            "hook": f"POV: You just discovered the {idea.lower()} framework",
            "format": "Reaction style, text + face cam",
            "cta": "Save this for later"
        },
        {
            "platform": "Reels/Shorts",
            "hook": f"Stop doing {idea.lower()} manually",
            "format": "Quick tip format, 15-30 seconds",
            "cta": "Comment 'GUIDE' for the full breakdown"
        },
        {
            "platform": "Reels/Shorts",
            "hook": f"What {idea.lower()} looks like in 2025 vs 2020",
            "format": "Split screen comparison",
            "cta": "Which side are you on?"
        },
    ]
    print(f"  ✅ {len(results['short_form_ideas'])} short-form ideas created")

    # Step 5: Review Notes
    print("\n📝 Step 5: Review notes...")
    results["review_notes"] = f"""
Content Review Checklist for: {idea}

Voice & Tone:
☐ Does this sound like me? (Not too formal, not too casual)
☐ Is it practical? (Actionable steps, not just theory)
☐ Is it useful? (Would I share this with a friend?)

Clarity:
☐ Is the main point clear in the first 3 seconds?
☐ Are the steps easy to follow?
☐ Is there a clear call to action?

Usefulness:
☐ Does this solve a real problem?
☐ Is there a specific example or case study?
☐ Can someone implement this today?

Before Publishing:
☐ Check for jargon — replace with plain language
☐ Add a personal story or example
☐ Make sure the hook is strong
☐ Verify all links work
☐ Add relevant hashtags (3-5 max for LinkedIn)
"""
    print("  ✅ Review notes created")

    return results


def save_results(results: dict, output_dir: str = "output/content"):
    """Save all content pieces to files."""
    os.makedirs(output_dir, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    idea_slug = results["idea"][:30].replace(" ", "_").lower()

    # Save YouTube outline
    with open(f"{output_dir}/{idea_slug}_youtube_outline.md", "w") as f:
        f.write(results["youtube_outline"])

    # Save newsletter
    with open(f"{output_dir}/{idea_slug}_newsletter.md", "w") as f:
        f.write(results["newsletter_draft"])

    # Save LinkedIn posts
    for i, post in enumerate(results["linkedin_posts"], 1):
        with open(f"{output_dir}/{idea_slug}_linkedin_{i}.txt", "w") as f:
            f.write(post)

    # Save short-form ideas
    with open(f"{output_dir}/{idea_slug}_short_form.json", "w") as f:
        json.dump(results["short_form_ideas"], f, indent=2)

    # Save review notes
    with open(f"{output_dir}/{idea_slug}_review.md", "w") as f:
        f.write(results["review_notes"])

    # Save full results
    with open(f"{output_dir}/{idea_slug}_full.json", "w") as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 All content saved to {output_dir}/")
    return output_dir


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Content Creator Workflow")
    parser.add_argument("--idea", type=str, help="Your YouTube video idea")
    parser.add_argument("--interactive", action="store_true", help="Interactive mode")
    parser.add_argument("--save", action="store_true", help="Save to files")
    args = parser.parse_args()

    if args.interactive:
        idea = input("Enter your YouTube video idea: ").strip()
    elif args.idea:
        idea = args.idea
    else:
        idea = "How AI agents can automate 80% of manual business tasks"
        print(f"Using default idea: {idea}")

    results = content_creator_workflow(idea)

    if args.save:
        save_results(results)

    print("\n" + "=" * 60)
    print("✅ Content creation complete!")
    print(f"  📹 YouTube outline: {len(results['youtube_outline'])} chars")
    print(f"  📧 Newsletter: {len(results['newsletter_draft'])} chars")
    print(f"  💼 LinkedIn posts: {len(results['linkedin_posts'])}")
    print(f"  📱 Short-form ideas: {len(results['short_form_ideas'])}")
