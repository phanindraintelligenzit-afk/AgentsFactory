# Setup Guide — Finance Automation What Surprised You About Estoni

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/finance-automation-what-surprised-you-about-estoni.git
cd finance-automation-what-surprised-you-about-estoni
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
docker build -t finance-automation-what-surprised-you-about-estoni .
docker run -p 8000:8000 finance-automation-what-surprised-you-about-estoni
```
