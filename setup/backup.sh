#!/usr/bin/env bash
# Backup AgentsFactory database and configs to GitHub
# Run via cron: 0 2 * * * (daily at 2 AM)

set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$REPO_DIR"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="backups"
mkdir -p "$BACKUP_DIR"

echo "📦 AgentsFactory Backup — $TIMESTAMP"

# Backup database
if [ -f "agentsfactory_metrics.db" ]; then
    cp "agentsfactory_metrics.db" "$BACKUP_DIR/agentsfactory_metrics_$TIMESTAMP.db"
    # Keep only last 7 backups
    ls -t "$BACKUP_DIR"/agentsfactory_metrics_*.db 2>/dev/null | tail -n +8 | xargs rm -f 2>/dev/null
    echo "  ✅ Database backed up"
fi

# Backup configs
tar -czf "$BACKUP_DIR/configs_$TIMESTAMP.tar.gz" \
    .env.example \
    src/agents/ocoya_client.py \
    src/agentkit/observability/command_center.py \
    setup/ \
    2>/dev/null || true
echo "  ✅ Configs backed up"

# Git commit and push
if [ -d ".git" ]; then
    git add -A
    git commit -m "Auto-backup: $TIMESTAMP" --allow-empty 2>/dev/null || true
    git push origin master:main 2>/dev/null || echo "  ⚠️  Git push failed (network?)"
    echo "  ✅ Pushed to GitHub"
fi

echo "✅ Backup complete: $BACKUP_DIR/"
