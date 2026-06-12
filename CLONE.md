# AgentsFactory — Self-Cloning Backup & Restore

This repo is designed to be **fully cloneable**. If you lose your machine, you can recreate the entire AgentsFactory system on a new VPS or PC in under 10 minutes.

## Quick Start (New Machine)

```bash
# 1. Clone this repo
git clone https://github.com/phanindraintelligenzit-afk/AgentsFactory.git
cd AgentsFactory

# 2. Run the bootstrap script
bash setup/bootstrap.sh

# 3. Configure your API keys
cp .env.example .env
nano .env  # Add your keys

# 4. Initialize the database
python src/agents/lead_loader.py --download

# 5. Start the dashboard
uv run streamlit run src/agentkit/observability/command_center.py
```

## What Gets Recreated

| Component | Automation |
|-----------|-----------|
| Python virtual environment | `uv venv` + `uv sync` |
| All Python dependencies | `pyproject.toml` / `requirements.txt` |
| Database schema | Auto-created on first run |
| Cron jobs (4x) | `setup/install-crons.sh` |
| All agents (8x) | Source code in `src/agents/` |
| Command Center dashboard | `src/agentkit/observability/command_center.py` |
| Landing page | `docs/landing/index.html` |
| Notion databases | Created via API (see `setup/notion-setup.md`) |
| Skills | Symlinked to `~/.hermes/skills/` |

## Required API Keys

Add these to `.env`:

| Key | Where to get it |
|-----|----------------|
| `NOTION_API_KEY` | notion.so/my-integrations |
| `OCoYA_API_KEY` | app.ocoya.com → Settings → API |
| `GITHUB_TOKEN` | github.com/settings/tokens (for backups) |

## Backup Strategy

- **Code**: Auto-pushed to GitHub on every commit
- **Database**: Backed up to `backups/` directory (cron)
- **Configs**: All in repo (`src/agents/ocoya_client.py`, `.env.example`)
- **Cron jobs**: Reinstallable via `setup/install-crons.sh`

## Supported Platforms

- ✅ LinkedIn (via Ocoya)
- ✅ X/Twitter (via Ocoya)
- ✅ Facebook (via Ocoya)
- 📸 Instagram (via Ocoya, requires media attachment)

## Architecture

```
AgentsFactory/
├── src/agents/           # All AI agents
│   ├── ocoya_client.py   # Ocoya API wrapper
│   ├── linkedin_poster.py
│   ├── content_scheduler.py
│   ├── engagement_agent.py
│   ├── outreach_agent.py
│   ├── multi_platform_agent.py
│   ├── lead_loader.py
│   └── form_sync.py
├── src/agentkit/observability/
│   └── command_center.py # Streamlit dashboard
├── docs/
│   ├── landing/          # GitHub Pages landing page
│   └── services.md       # Pricing tiers
├── setup/
│   ├── bootstrap.sh      # One-command setup
│   └── install-crons.sh  # Reinstall cron jobs
├── .env.example          # Template for API keys
└── agentsfactory_metrics.db  # SQLite database
```

## Support

Open an issue at https://github.com/phanindraintelligenzit-afk/AgentsFactory/issues
