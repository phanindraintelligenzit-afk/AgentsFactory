#!/usr/bin/env bash
# Install AgentsFactory cron jobs on a new machine
# Usage: bash setup/install-crons.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "⏰ Installing AgentsFactory cron jobs..."

# Check if hermes cron is available
if ! command -v hermes &>/dev/null; then
    echo "⚠️  Hermes CLI not found. Install from https://hermes-agent.nousresearch.com"
    echo "   Cron jobs must be installed manually. See CLONE.md for details."
    exit 0
fi

# Remove existing AgentsFactory crons (if any)
echo "  Cleaning up old cron jobs..."
hermes cron list 2>/dev/null | grep -i "agentsfactory" | awk '{print $1}' | while read -r job_id; do
    [ -n "$job_id" ] && hermes cron remove "$job_id" 2>/dev/null
done

echo "  Installing new cron jobs..."

# Daily Briefing — 8 AM (Mon-Fri)
hermes cron create \
    --name "AgentsFactory - Daily Briefing" \
    --schedule "0 8 * * 1-5" \
    --prompt "Generate the daily business briefing for AgentsFactory. Check Ocoya for LinkedIn stats, review scheduled posts, and summarize key metrics. Send the briefing as a Telegram message." \
    --deliver origin

# LinkedIn Daily Post — 9 AM (Mon-Fi)
hermes cron create \
    --name "AgentsFactory - LinkedIn Daily Post" \
    --schedule "0 9 * * 1-5" \
    --prompt "Generate and post to LinkedIn for AgentsFactory. Use content_scheduler.py to generate a post from today's content pillar, then post via Ocoya API with scheduledAt set to now. Also post to X and Facebook. Report results." \
    --deliver origin

# LinkedIn Engagement — 12 PM (Mon-Fri)
hermes cron create \
    --name "AgentsFactory - LinkedIn Engagement" \
    --schedule "0 12 * * 1-5" \
    --prompt "Run the LinkedIn engagement cycle for AgentsFactory. Create an engagement-optimized post (question, poll, or hot take) via Ocoya. Report results." \
    --deliver origin

# Weekly Content Queue — Sunday 8 AM
hermes cron create \
    --name "AgentsFactory - Weekly Content Queue" \
    --schedule "0 8 * * 0" \
    --prompt "Schedule a full week of LinkedIn posts for AgentsFactory. Use content_scheduler.py to generate and schedule 7 posts (one per day) via Ocoya. Report how many posts were scheduled." \
    --deliver origin

echo ""
echo "✅ Cron jobs installed:"
echo "  • Daily Briefing     — 8 AM (Mon-Fri)"
echo "  • LinkedIn Daily Post — 9 AM (Mon-Fri)"
echo "  • LinkedIn Engagement — 12 PM (Mon-Fri)"
echo "  • Weekly Content Queue — Sunday 8 AM"
echo ""
