#!/usr/bin/env bash
# AgentsFactory Bootstrap Script
# Run this on a new machine to recreate the entire system.
#
# Usage: bash setup/bootstrap.sh

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

echo "============================================"
echo "  AgentsFactory Bootstrap"
echo "============================================"
echo ""

# ---- Step 1: Check prerequisites ----
echo "📋 Checking prerequisites..."

check_cmd() {
    if command -v "$1" &>/dev/null; then
        echo "  ✅ $1 ($(command -v "$1"))"
    else
        echo "  ❌ $1 — NOT FOUND"
        return 1
    fi
}

MISSING=0
check_cmd git || MISSING=1
check_cmd python3 || MISSING=1
check_cmd uv || MISSING=1
check_cmd curl || MISSING=1

if [ "$MISSING" -eq 1 ]; then
    echo ""
    echo "⚠️  Missing prerequisites. Install them first:"
    echo "  - git:     https://git-scm.com/downloads"
    echo "  - python3: https://www.python.org/downloads/"
    echo "  - uv:      curl -LsSf https://astral.sh/uv/install.sh | sh"
    echo "  - curl:    Usually pre-installed"
    exit 1
fi

# ---- Step 2: Python virtual environment ----
echo ""
echo "🐍 Setting up Python virtual environment..."
if [ ! -d ".venv" ]; then
    uv venv .venv --python 3.11
    echo "  ✅ Virtual environment created"
else
    echo "  ✅ Virtual environment already exists"
fi

# ---- Step 3: Install dependencies ----
echo ""
echo "📦 Installing Python dependencies..."

# Create pyproject.toml if it doesn't exist
if [ ! -f "pyproject.toml" ]; then
    cat > pyproject.toml << 'PYEOF'
[project]
name = "agentsfactory"
version = "1.0.0"
description = "AI Automation Agency"
requires-python = ">=3.11"
dependencies = [
    "streamlit>=1.30",
    "plotly>=5.18",
    "pandas>=2.0",
    "requests>=2.31",
]
PYEOF
    echo "  ✅ Created pyproject.toml"
fi

# Install deps
uv pip install streamlit plotly pandas requests 2>&1 | tail -3
echo "  ✅ Dependencies installed"

# ---- Step 4: Create directory structure ----
echo ""
echo "📁 Creating directory structure..."
mkdir -p src/agents
mkdir -p src/agentkit/observability
mkdir -p docs/landing
mkdir -p setup
mkdir -p backups
mkdir -p .hermes
echo "  ✅ Directories created"

# ---- Step 5: Environment file ----
echo ""
echo "🔑 Setting up environment..."
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo "  ✅ Created .env from template"
    else
        cat > .env << 'ENVEOF'
# AgentsFactory Environment Variables
# Fill in your API keys below

# Notion API Key (from notion.so/my-integrations)
NOTION_API_KEY=ntn_YOUR_KEY_HERE

# Ocoya API Key (from app.ocoya.com → Settings → API)
OCoYA_API_KEY=YOUR_OCoYA_KEY_HERE

# GitHub Token (for backups)
GITHUB_TOKEN=ghp_YOUR_TOKEN_HERE
ENVEOF
        echo "  ✅ Created .env template"
    fi
    echo ""
    echo "  ⚠️  IMPORTANT: Edit .env and add your API keys!"
    echo "     nano .env"
else
    echo "  ✅ .env already exists"
fi

# ---- Step 6: Initialize database ----
echo ""
echo "🗄️  Initializing database..."
if [ ! -f "agentsfactory_metrics.db" ]; then
    python3 -c "
import sqlite3
conn = sqlite3.connect('agentsfactory_metrics.db')
conn.execute('CREATE TABLE IF NOT EXISTS leads (id INTEGER PRIMARY KEY AUTOINCREMENT, company TEXT, email TEXT, phone TEXT, website TEXT, category TEXT, social_lead_score TEXT, facebook_followers INTEGER DEFAULT 0, twitter_followers INTEGER DEFAULT 0, facebook_url TEXT, twitter_url TEXT, gmb_url TEXT, keyword TEXT, created_at TEXT DEFAULT (datetime(\"now\")))')
conn.execute('CREATE TABLE IF NOT EXISTS agent_activity (id INTEGER PRIMARY KEY AUTOINCREMENT, agent_name TEXT NOT NULL, action TEXT NOT NULL, target TEXT DEFAULT \"\", status TEXT DEFAULT \"completed\", details TEXT DEFAULT \"\", created_at TEXT DEFAULT (datetime(\"now\")))')
conn.commit()
conn.close()
print('  ✅ Database initialized')
"
else
    echo "  ✅ Database already exists"
fi

# ---- Step 7: Install cron jobs ----
echo ""
echo "⏰ Setting up cron jobs..."
if [ -f "setup/install-crons.sh" ]; then
    bash setup/install-crons.sh
    echo "  ✅ Cron jobs installed"
else
    echo "  ⚠️  setup/install-crons.sh not found — skipping cron setup"
fi

# ---- Step 8: Verify ----
echo ""
echo "============================================"
echo "  ✅ Bootstrap Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Edit .env with your API keys:  nano .env"
echo "  2. Start the dashboard:           uv run streamlit run src/agentkit/observability/command_center.py"
echo "  3. Load leads:                    python src/agents/lead_loader.py --download"
echo ""
echo "Dashboard will be at: http://localhost:8501"
echo ""
