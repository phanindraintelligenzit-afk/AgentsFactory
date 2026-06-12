# AgentsFactory — AI Automation Agency

> **Self-cloning AI agency infrastructure.** Lose your machine? Clone this repo on any VPS/PC and be back online in 10 minutes.

## 🚀 Quick Start

```bash
git clone https://github.com/phanindraintelligenzit-afk/AgentsFactory.git
cd AgentsFactory
bash setup/bootstrap.sh
```

See [CLONE.md](CLONE.md) for full restore instructions.

## 📱 Social Media Automation

Automated posting to **LinkedIn, X/Twitter, Facebook** (and Instagram with media) via Ocoya.

| Platform | Status | Notes |
|----------|--------|-------|
| LinkedIn | ✅ Live | Daily posts at 9 AM IST |
| X/Twitter | ✅ Live | Platform-optimized content |
| Facebook | ✅ Live | Page posting |
| Instagram | 📸 Partial | Requires media attachment |

### Content Pipeline
- **6 content pillars**: AI/Automation, E-commerce, SaaS, Building in Public, Productivity, Industry Insights
- **4 post types**: Infotainment, Storytelling, Value bombs, Engagement
- **Auto-scheduled**: Weekdays 9 AM + 12 PM, weekly queue every Sunday

## 📊 Command Center Dashboard

```bash
uv run streamlit run src/agentkit/observability/command_center.py
```

8 pages: Overview, Projects, Revenue, Leads, Content, LinkedIn, Automations, Agents, Kanban, AI Advice

## 🤖 AI Agents

| Agent | File | Purpose |
|-------|------|---------|
| LinkedIn Poster | `src/agents/linkedin_poster.py` | Post/schedule to LinkedIn |
| Content Scheduler | `src/agents/content_scheduler.py` | Generate + queue weekly content |
| Engagement Agent | `src/agents/engagement_agent.py` | Engagement posts + comment-to-DM |
| Outreach Agent | `src/agents/outreach_agent.py` | Cold DMs + outreach posts |
| Multi-Platform | `src/agents/multi_platform_agent.py` | Post to all 4 platforms at once |
| Lead Loader | `src/agents/lead_loader.py` | Import leads from Google Sheets |
| Form Sync | `src/agents/form_sync.py` | Sync form responses to DB + Notion |

## ⏰ Automated Cron Jobs

| Job | Schedule | Description |
|-----|----------|-------------|
| Daily Briefing | 8 AM (Mon-Fri) | Stats + action items via Telegram |
| LinkedIn Post | 9 AM (Mon-Fri) | Generate + post to all platforms |
| Engagement | 12 PM (Mon-Fri) | Engagement-optimized post |
| Weekly Queue | Sunday 8 AM | Schedule 7 days of content |

## 📋 Lead Database

- **3,312 leads** imported from Google Sheets
- Fields: Company, Email, Phone, Website, Category, Social URLs, Lead Score
- Synced to Notion database
- Dashboard: Leads page in Command Center

## 🏗️ Architecture

```
AgentsFactory/
├── src/agents/              # AI agents (Python)
├── src/agentkit/observability/  # Streamlit dashboard
├── docs/
│   ├── landing/             # GitHub Pages landing page
│   └── services.md          # Pricing tiers
├── setup/
│   ├── bootstrap.sh         # One-command setup
│   ├── install-crons.sh     # Reinstall cron jobs
│   └── backup.sh            # Daily backup to GitHub
├── .env.example             # API key template
├── CLONE.md                 # Full restore guide
└── agentsfactory_metrics.db # SQLite database
```

## 🔑 Required API Keys

1. **Notion** — notion.so/my-integrations
2. **Ocoya** — app.ocoya.com → Settings → API
3. **GitHub** — github.com/settings/tokens (for backups)

## 📄 License

MIT — Use this to build your own AI agency.
