"""
Workflow 3: Hand Off an Entire Project and Let It Run Itself
Based on Rick Mulready's Hermes Agent prompt.

Turns a fuzzy business goal into a clean project plan with tasks,
success metrics, and a self-running workflow.

Usage:
    python workflows/project_planner.py --goal "Your project goal" --budget 5000 --timeline "30 days"
"""
import argparse
import json
from datetime import datetime


def project_planner_workflow(goal: str, budget: float = 0, timeline: str = "30 days") -> dict:
    """
    Turn a fuzzy goal into a structured project plan.
    """
    results = {
        "goal": goal,
        "budget": budget,
        "timeline": timeline,
        "timestamp": datetime.now().isoformat(),
        "project_plan": "",
        "tasks": [],
        "success_metrics": "",
        "risks": "",
    }

    print("📋 Project Planner Workflow")
    print("=" * 60)
    print(f"\nGoal: {goal}")
    print(f"Budget: ${budget:,.0f}" if budget else "Budget: Not specified")
    print(f"Timeline: {timeline}")

    # Project Plan
    results["project_plan"] = f"""
# Project Plan: {goal}

## Overview
- **Goal**: {goal}
- **Timeline**: {timeline}
- **Budget**: ${budget:,.0f}
- **Status**: Planning Phase

## Phase 1: Research & Planning (Days 1-5)
- [ ] Define success criteria
- [ ] Research competitive landscape
- [ ] Identify target audience
- [ ] Create project timeline
- [ ] Allocate budget

## Phase 2: Build (Days 6-20)
- [ ] Core development/creation
- [ ] Content creation
- [ ] System setup
- [ ] Integration testing

## Phase 3: Launch (Days 21-25)
- [ ] Beta testing with small group
- [ ] Collect feedback
- [ ] Fix issues
- [ ] Prepare launch materials

## Phase 4: Measure & Optimize (Days 26-30)
- [ ] Track success metrics
- [ ] Gather user feedback
- [ ] Iterate based on data
- [ ] Document learnings
"""
    print("  ✅ Project plan created")

    # Tasks
    results["tasks"] = [
        {"phase": "Research", "task": "Define success criteria", "owner": "You", "due": "Day 1"},
        {"phase": "Research", "task": "Competitive research", "owner": "AI Agent", "due": "Day 2"},
        {"phase": "Research", "task": "Target audience analysis", "owner": "AI Agent", "due": "Day 3"},
        {"phase": "Build", "task": "Core development", "owner": "You/Team", "due": "Day 10"},
        {"phase": "Build", "task": "Content creation", "owner": "AI Agent", "due": "Day 12"},
        {"phase": "Build", "task": "System setup", "owner": "AI Agent", "due": "Day 15"},
        {"phase": "Launch", "task": "Beta testing", "owner": "You", "due": "Day 21"},
        {"phase": "Launch", "task": "Launch materials", "owner": "AI Agent", "due": "Day 23"},
        {"phase": "Measure", "task": "Track metrics", "owner": "AI Agent", "due": "Day 26"},
        {"phase": "Measure", "task": "Iterate", "owner": "You", "due": "Day 30"},
    ]
    print(f"  ✅ {len(results['tasks'])} tasks created")

    # Success Metrics
    results["success_metrics"] = f"""
# Success Metrics for: {goal}

## Primary Metrics (KPIs)
- **Metric 1**: [Specific number] by [date]
- **Metric 2**: [Specific number] by [date]
- **Metric 3**: [Specific number] by [date]

## Secondary Metrics
- **Engagement**: [Target]
- **Conversion**: [Target]
- **Retention**: [Target]

## How to Measure
- Daily: [What to check daily]
- Weekly: [What to review weekly]
- End of project: [Final assessment]

## Red Flags (When to Pivot)
- If [metric] is below [threshold] by [date]
- If [metric] is below [threshold] by [date]
"""
    print("  ✅ Success metrics defined")

    # Risks
    results["risks"] = """
# Risk Assessment

## High Risk
- **Risk**: Scope creep
  - **Mitigation**: Define clear boundaries upfront
- **Risk**: Timeline slip
  - **Mitigation**: Build in buffer days

## Medium Risk
- **Risk**: Budget overrun
  - **Mitigation**: Track spending weekly
- **Risk**: Quality issues
  - **Mitigation**: Beta test before full launch

## Low Risk
- **Risk**: Low initial traction
  - **Mitigation**: Have a backup marketing plan
"""
    print("  ✅ Risk assessment created")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Project Planner Workflow")
    parser.add_argument("--goal", type=str, required=True, help="Your project goal")
    parser.add_argument("--budget", type=float, default=0, help="Budget in USD")
    parser.add_argument("--timeline", type=str, default="30 days", help="Project timeline")
    args = parser.parse_args()

    results = project_planner_workflow(args.goal, args.budget, args.timeline)
    print("\n✅ Project plan complete!")
