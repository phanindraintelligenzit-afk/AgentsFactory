"""
Workflow 4: Get CEO-Level Advice
Workflow 5: Build Your Command Center
Workflow 6: AI Researcher
Workflow 7: Delegate Real Work From Your Phone

Based on Rick Mulready's 7 Hermes Agent prompts.
"""
import argparse
import json
from datetime import datetime


def ceo_advice_workflow(business_context: str = "") -> dict:
    """
    Prompt 4: Get CEO-level advice from an agent that knows your business.
    """
    prompt = f"""
Based on everything you know about my business, what are the 3 highest-leverage things I should focus on this week?

{f"Additional context: {business_context}" if business_context else ""}

For each, tell me:
1. What it is
2. Why it matters right now
3. How to do it (specific steps)
4. How to measure if it's working
"""
    return {
        "workflow": "CEO Advice",
        "prompt": prompt,
        "usage": "Run this anytime you feel scattered. It points you at the few things that actually move the needle.",
        "timestamp": datetime.now().isoformat(),
    }


def command_center_workflow(business_type: str = "AI agency") -> dict:
    """
    Prompt 5: Build your own Command Center.
    The Command Center already exists in this repo (command_center.py).
    """
    return {
        "workflow": "Command Center",
        "status": "✅ Already built!",
        "location": "src/agentkit/observability/command_center.py",
        "run_command": "uv run streamlit run src/agentkit/observability/command_center.py",
        "pages": [
            "Overview — KPIs, revenue, leads, automations",
            "Projects — Client project tracking",
            "Revenue — Financial dashboard",
            "Leads — Pipeline management (3,312 leads loaded)",
            "Content — Content calendar",
            "LinkedIn — Ocoya social media management",
            "Automations — Cron job health",
            "Agents — Subagent activity tracking",
            "Kanban — Visual agent status board",
            "AI Advice — Strategic recommendations",
        ],
        "note": "This IS the Command Center. You're looking at it.",
        "timestamp": datetime.now().isoformat(),
    }


def ai_researcher_workflow(topic: str, save_path: str = "output/research") -> dict:
    """
    Prompt 6: AI Researcher that makes the rest of your AI smarter.
    """
    prompt = f"""
Research the following topic and save your findings: {topic}

Do the following:
1. Search for the latest information on this topic
2. Find 5-10 high-quality sources
3. Separate real evidence from claims and weak signals
4. Identify key trends and insights
5. Write a research summary
6. Save it to {save_path}/

Format the output as:
- Executive Summary (3-5 sentences)
- Key Findings (bulleted)
- Evidence vs Claims (table)
- Weak Signals (emerging trends)
- Recommended Actions
- Sources
"""
    return {
        "workflow": "AI Researcher",
        "topic": topic,
        "prompt": prompt,
        "save_path": save_path,
        "usage": "Run this to research any market, competitor, or topic. The output feeds into your other agents.",
        "timestamp": datetime.now().isoformat(),
    }


def delegate_workflow(task: str, deadline: str = "") -> dict:
    """
    Prompt 7: Delegate real work from your phone and come back to it finished.
    """
    prompt = f"""
I need you to complete this task: {task}

{f"Deadline: {deadline}" if deadline else ""}

Here's what I need:
1. Break this task into steps
2. Execute each step
3. Report back when done with:
   - What was completed
   - Any issues encountered
   - Next steps (if applicable)

Work autonomously. If you need clarification, ask. Otherwise, just get it done.
"""
    return {
        "workflow": "Delegate Work",
        "task": task,
        "prompt": prompt,
        "usage": "Text this to Hermes from your phone. Come back to it finished.",
        "timestamp": datetime.now().isoformat(),
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Rick Mulready Workflow Runner")
    parser.add_argument("--workflow", type=str, choices=["4", "5", "6", "7", "all"], default="all")
    parser.add_argument("--topic", type=str, default="AI automation market trends")
    parser.add_argument("--task", type=str, default="Research competitors and create a comparison table")
    parser.add_argument("--context", type=str, default="")
    args = parser.parse_args()

    if args.workflow in ("4", "all"):
        result = ceo_advice_workflow(args.context)
        print(json.dumps(result, indent=2))

    if args.workflow in ("5", "all"):
        result = command_center_workflow()
        print(json.dumps(result, indent=2))

    if args.workflow in ("6", "all"):
        result = ai_researcher_workflow(args.topic)
        print(json.dumps(result, indent=2))

    if args.workflow in ("7", "all"):
        result = delegate_workflow(args.task)
        print(json.dumps(result, indent=2))
