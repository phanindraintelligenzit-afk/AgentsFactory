"""
Workflow 2: Build and Price Your Next Offer
Based on Rick Mulready's Hermes Agent prompt.

Analyzes two comparison offers + your own program to recommend
a stand-alone offer you could create.

Usage:
    python workflows/offer_builder.py --program "Your program description" --url1 "https://competitor1.com" --url2 "https://competitor2.com"
"""
import argparse
import json
from datetime import datetime


def offer_builder_workflow(program_desc: str, url1: str, url2: str) -> dict:
    """
    Analyze two comparison offers and recommend a stand-alone offer.
    """
    results = {
        "your_program": program_desc,
        "competitor_1": url1,
        "competitor_2": url2,
        "timestamp": datetime.now().isoformat(),
        "analysis": "",
        "recommendation": "",
        "pricing_suggestion": "",
    }

    print("🏗️ Offer Builder Workflow")
    print("=" * 60)
    print(f"\nYour program: {program_desc}")
    print(f"Competitor 1: {url1}")
    print(f"Competitor 2: {url2}")

    # Analysis framework
    results["analysis"] = f"""
# Offer Analysis Framework

## Your Program
{program_desc}

## Competitive Analysis

### Competitor 1: {url1}
- **Price Point**: [Research this]
- **Target Audience**: [Who are they targeting?]
- **Key Features**: [What's included?]
- **Positioning**: [How do they market it?]
- **Strengths**: [What do they do well?]
- **Weaknesses**: [Where do they fall short?]

### Competitor 2: {url2}
- **Price Point**: [Research this]
- **Target Audience**: [Who are they targeting?]
- **Key Features**: [What's included?]
- **Positioning**: [How do they market it?]
- **Strengths**: [What do they do well?]
- **Weaknesses**: [Where do they fall short?]

## Gap Analysis
- What's missing from both competitors?
- What can you do better?
- What's your unique angle?
- Who's underserved by both?
"""
    print("  ✅ Competitive analysis framework created")

    # Recommendation
    results["recommendation"] = f"""
# Offer Recommendation

## Recommended Stand-Alone Offer

### The Gap
Based on the competitive landscape, there's an opportunity for:
- A program that combines [strength from competitor 1] with [strength from competitor 2]
- Targeted at [specific audience] who are underserved
- Priced between the two competitors to capture the middle market

### Offer Structure
**Name**: [Working Title]
**Price**: $[X] (between competitor 1 and 2)
**Duration**: [X weeks/months]
**Format**: [Course/Cohort/Membership/Service]

### Key Differentiators
1. [Unique feature 1]
2. [Unique feature 2]
3. [Unique feature 3]

### What's Included
- [Core deliverable 1]
- [Core deliverable 2]
- [Bonus/upsell opportunity]

### Who This Is For
- [Ideal customer profile]
- [Pain point they're trying to solve]
- [Budget range]

### Who This Is NOT For
- [People who need more hand-holding]
- [People who want the cheapest option]
- [People who need enterprise-level support]
"""
    print("  ✅ Offer recommendation created")

    # Pricing suggestion
    results["pricing_suggestion"] = """
# Pricing Strategy

## Pricing Options

### Option 1: Single Payment
- Full price: $X
- Early bird: $X (25% off for first 10 buyers)

### Option 2: Payment Plan
- 3 payments of $X
- Total: $X (slightly higher than single payment)

### Option 3: Tiered
- Basic: $X (core only)
- Pro: $X (core + bonuses)
- VIP: $X (core + bonuses + 1:1)

## Pricing Psychology Tips
- Anchor to the higher-priced competitor
- Offer a "founding member" discount for early buyers
- Include a guarantee to reduce risk
- Make the payment plan total slightly higher (incentive for full payment)

## Revenue Projections
- 10 buyers × $X = $X
- 25 buyers × $X = $X
- 50 buyers × $X = $X
"""
    print("  ✅ Pricing strategy created")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Offer Builder Workflow")
    parser.add_argument("--program", type=str, required=True, help="Description of your existing program")
    parser.add_argument("--url1", type=str, required=True, help="URL of competitor program 1")
    parser.add_argument("--url2", type=str, required=True, help="URL of competitor program 2")
    args = parser.parse_args()

    results = offer_builder_workflow(args.program, args.url1, args.url2)
    print("\n✅ Offer analysis complete!")
