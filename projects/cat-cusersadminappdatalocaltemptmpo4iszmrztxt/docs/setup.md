# Setup Guide — Cat Cusersadminappdatalocaltemptmpo4iszmrztxt

## Prerequisites

- Python 3.11+
- Docker (optional)
- Git

## Installation

```bash
git clone https://github.com/phanindraintelligenzit-afk/cat-cusersadminappdatalocaltemptmpo4iszmrztxt.git
cd cat-cusersadminappdatalocaltemptmpo4iszmrztxt
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
docker build -t cat-cusersadminappdatalocaltemptmpo4iszmrztxt .
docker run -p 8000:8000 cat-cusersadminappdatalocaltemptmpo4iszmrztxt
```
