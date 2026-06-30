# AI Competitive Intelligence Agent

> Open-source alternative to Crayon ($500-2K/mo) and Klue

Monitor competitor signals 24/7 and auto-generate battlecards + briefings.

## Features

- **Competitor Tracking** — Add competitors by domain, configure what to monitor
- **Signal Detection** — Website changes, pricing updates, job postings, reviews, social mentions, funding, tech stack
- **AI Battlecards** — Auto-generated battlecards with strengths, weaknesses, win strategies, objection handlers
- **Competitive Briefings** — Daily/weekly digests of all competitive activity
- **Background Worker** — Continuous scanning with configurable intervals
- **REST API** — Full API for integrations (Slack, CRM, sales tools)

## Quick Start

```bash
# Clone
git clone https://github.com/phanindraintelligenzit-afk/ai-competitive-intelligence-agent.git
cd ai-competitive-intelligence-agent

# Run with Docker
docker-compose up -d

# Or run locally
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload
```

API available at `http://localhost:8000`

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/api/v1/competitors` | List competitors |
| POST | `/api/v1/competitors` | Add competitor |
| GET | `/api/v1/competitors/{id}` | Get competitor |
| PATCH | `/api/v1/competitors/{id}` | Update monitoring settings |
| DELETE | `/api/v1/competitors/{id}` | Remove competitor |
| GET | `/api/v1/signals` | List signals |
| GET | `/api/v1/signals/feed` | Recent signal feed |
| POST | `/api/v1/signals/mark-read` | Mark signals as read |
| GET | `/api/v1/battlecards` | List battlecards |
| POST | `/api/v1/battlecards/generate` | Generate AI battlecard |
| POST | `/api/v1/battlecards/{id}/publish` | Publish battlecard |
| GET | `/api/v1/briefings` | List briefings |
| POST | `/api/v1/briefings/generate` | Generate briefing |

## Architecture

```
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI routes
│   │   ├── core/         # Config, database
│   │   ├── models/       # SQLAlchemy models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── services/     # Signal detection engine
│   │   ├── workers/      # Background scanner
│   │   └── main.py       # FastAPI app
│   ├── tests/            # pytest
│   ├── pyproject.toml
│   └── Dockerfile
├── frontend/             # React + Vite dashboard
├── docker-compose.yml
└── .github/workflows/    # CI
```

## Configuration

| Variable | Default | Description |
|----------|---------|-------------|
| `DATABASE_URL` | `sqlite:///./ci_agent.db` | Database connection |
| `SCAN_INTERVAL_MINUTES` | `60` | How often to scan |
| `MAX_COMPETITORS` | `50` | Max tracked competitors |
| `LLM_API_KEY` | `` | API key for AI battlecard generation |
| `SLACK_WEBHOOK_URL` | `` | Slack notifications |

## Built By

Autonomously built and published by the [AgentsFactory](https://github.com/phanindraintelligenzit-afk/AgentsFactory) agent swarm.

Part of the [AgentsFactory Marketplace](https://phanindraintelligenzit-afk.github.io/AgentsFactory/) — open-source AI agents for business operations.
