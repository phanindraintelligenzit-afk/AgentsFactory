# Setup Guide — Finance Automation Ai Powered Multi Agent System F

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/finance-automation-ai-powered-multi-agent-system-f.git
cd finance-automation-ai-powered-multi-agent-system-f
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

## Run Tests

```bash
pytest tests/ -v
```

## Run Locally

```bash
uvicorn src.pipeline:app --reload
```

## Deploy with Docker

```bash
docker build -t finance-automation-ai-powered-multi-agent-system-f .
docker run -p 8000:8000 finance-automation-ai-powered-multi-agent-system-f
```
