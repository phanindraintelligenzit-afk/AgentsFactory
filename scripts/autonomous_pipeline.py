#!/usr/bin/env python3
"""AIdentify Autonomous Opportunity Pipeline

Full loop: Scan → Score → Build → Test → Push → Marketplace

Designed to run as Hermes cron job (no_agent mode).
Reads from scripts/opportunity_scanner.py and scripts/project_pipeline.py.
Pushes to GitHub and updates the docs/data/projects.json marketplace.

Usage:
    python autonomous_pipeline.py              # Run full pipeline
    python autonomous_pipeline.py --dry-run    # Only scan + select (no build/push)
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
import textwrap
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

def _find_repo_root() -> Path:
    """Find the AIdentify repo root.

    Prefer the clean clone at /tmp/agentsfactory-publish (always synced with remote).
    Fall back to walking up from this script.
    """
    # Primary: clean clone (always in sync with main)
    clean = Path("/tmp/agentsfactory-publish")
    if (clean / ".git").exists() and (clean / "docs" / "marketplace.html").exists():
        return clean
    clean_windows = Path("C:/tmp/agentsfactory-publish")
    if (clean_windows / ".git").exists() and (clean_windows / "docs" / "marketplace.html").exists():
        return clean_windows
    # Fallback: walk up from script location
    p = Path(__file__).resolve().parent
    for _ in range(6):
        if (p / ".git").exists() and (p / "docs" / "marketplace.html").exists():
            return p
        p = p.parent
    return Path(__file__).resolve().parents[1]

PROJECT_ROOT = _find_repo_root()
SCANNER = str(PROJECT_ROOT / "scripts" / "opportunity_scanner.py")
PIPELINE = str(PROJECT_ROOT / "scripts" / "project_pipeline.py")
TESTS_JSON = str(PROJECT_ROOT / "tests" / "test_opportunity_scanner.py")
PROJECTS_DIR = PROJECT_ROOT / "projects"
MARKETPLACE_JSON = PROJECT_ROOT / "docs" / "data" / "projects.json"
MARKETPLACE_HTML = PROJECT_ROOT / "docs" / "marketplace.html"

IST = timezone(timedelta(hours=5, minutes=30))
NOW = datetime.now(IST)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

SCORE_THRESHOLD = 40
CATEGORIES = ["healthcare", "ecommerce", "legal", "hr", "realestate",
              "finance", "marketing", "devtools"]

ICON_MAP = {"healthcare": "🏥", "ecommerce": "🛒", "legal": "⚖️", "hr": "👥",
            "realestate": "🏠", "finance": "💰", "marketing": "🎯",
            "devtools": "🔧", "other": "⚡"}


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

def log(msg: str) -> None:
    ts = NOW.strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{ts}] {msg}", flush=True)


# ---------------------------------------------------------------------------
# Execute helper
# ---------------------------------------------------------------------------

def run(cmd: str, timeout: int = 120) -> tuple[int, str, str]:
    """Run a shell command. Returns (exit_code, stdout, stderr)."""
    try:
        r = subprocess.run(
            cmd, shell=True, capture_output=True, text=True,
            timeout=timeout, cwd=str(PROJECT_ROOT)
        )
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except subprocess.TimeoutExpired:
        return -1, "", "TIMEOUT"
    except Exception as e:
        return -1, "", str(e)


# ---------------------------------------------------------------------------
# Phase 1: SCAN
# ---------------------------------------------------------------------------

def scan_opportunities() -> list[dict]:
    log("═══ PHASE 1: SCAN ═══")
    code, out, err = run(f"python3 {SCANNER} --json", timeout=60)
    if code != 0:
        log(f"Scanner failed (exit {code}): {err[:200]}")
        return []
    try:
        items = json.loads(out)
    except json.JSONDecodeError:
        log(f"Scanner output not valid JSON: {out[:200]}")
        return []

    items.sort(key=lambda x: x.get("opportunity_score", 0), reverse=True)
    top = items[0]["opportunity_score"] if items else 0
    log(f"Scanned {len(items)} signals → top score {top}/100")
    return items


# ---------------------------------------------------------------------------
# Phase 2: SELECT
# ---------------------------------------------------------------------------

def _slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^a-z0-9\s-]", "", text)
    text = re.sub(r"[\s]+", "-", text)
    text = re.sub(r"-+", "-", text)
    return text[:50]


def _detect_category(opp: dict) -> str:
    text = " ".join(str(opp.get(k, "")).lower()
                    for k in ("title", "text", "notes" if "notes" in opp else ""))
    keywords = {
        "healthcare": ["healthcare", "medical", "pharma", "clinical", "hipaa", "ehr", "patient", "doctor"],
        "ecommerce": ["ecommerce", "e-commerce", "shopify", "store", "product", "dropshipping", "cart"],
        "legal": ["legal", "law", "contract", "compliance", "gdpr", "soc2", "regulation"],
        "hr": ["hr", "hiring", "recruiting", "onboarding", "resume", "candidate", "payroll"],
        "realestate": ["real estate", "property", "listing", "brokerage", "rental"],
        "finance": ["finance", "accounting", "reconciliation", "invoice", "payment", "banking", "tax"],
        "marketing": ["marketing", "content", "seo", "social media", "outreach", "lead gen", "email", "ads"],
        "devtools": ["developer", "ci/cd", "deployment", "monitoring", "observability", "devops"],
    }
    scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in keywords.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "other"


def select_opportunity(opportunities: list[dict]) -> dict | None:
    log("═══ PHASE 2: SELECT ═══")
    if not opportunities:
        return None

    existing = {p.name for p in PROJECTS_DIR.iterdir() if p.is_dir()} if PROJECTS_DIR.exists() else set()

    for opp in opportunities:
        score = opp.get("opportunity_score", 0)
        title = opp.get("title", "Untitled").strip()
        slug = _slugify(title)

        if score < SCORE_THRESHOLD:
            log(f"  Skip '{title[:40]}' — score {score} < {SCORE_THRESHOLD}")
            continue
        if slug in existing:
            log(f"  Skip '{title[:40]}' — already built")
            continue

        cat = _detect_category(opp)
        log(f"  ✅ Selected: '{title[:50]}' (score={score}, cat={cat}, slug={slug})")
        return {"title": title, "score": score, "slug": slug,
                "category": cat, "source": opp.get("source", ""),
                "url": opp.get("url", ""), "text": opp.get("text", "")[:300],
                "signals": opp.get("signals", [])}

    log("No opportunity passed threshold")
    return None


# ---------------------------------------------------------------------------
# Phase 3: BUILD
# ---------------------------------------------------------------------------

def build_project(sel: dict) -> dict:
    log("═══ PHASE 3: BUILD ═══")
    cat = sel["category"]
    # Use a clean, ASCII-safe idea description
    idea_text = f"{cat} automation - AI-powered multi-agent system for {cat} workflows"

    # On Windows/MSYS, shlex.quote single-quotes break in subprocess.shell=True
    # Use double-quote wrapping instead
    idea_escaped = idea_text.replace('"', '\\"')
    cmd = f'python3 {PIPELINE} run --idea "{idea_escaped}" --category {cat} --skip-publish'

    code, out, err = run(cmd, timeout=120)
    if code != 0:
        log(f"Build failed: {err[:300]}")
        return {"error": err[:200]}

    # The pipeline generates a slug from the idea text — find the newest dir
    slug = sel["slug"]
    project_dir = PROJECTS_DIR / slug

    if not project_dir.exists():
        # Slug may differ — find the most recently created project dir
        if PROJECTS_DIR.exists():
            dirs = sorted(PROJECTS_DIR.iterdir(), key=lambda d: d.stat().st_mtime, reverse=True)
            for d in dirs:
                if d.is_dir() and (d / "pipeline_output.json").exists():
                    project_dir = d
                    break
        if not project_dir.exists():
            log(f"Build output not found in {PROJECTS_DIR}")
            return {"error": "Project directory not created"}

    n_files = len([f for f in project_dir.rglob("*") if f.is_file()])
    log(f"Built '{slug}': {n_files} files")
    return {"slug": slug, "project_dir": str(project_dir), "file_count": n_files}


# ---------------------------------------------------------------------------
# Phase 4: TEST
# ---------------------------------------------------------------------------

def _validate_html(content: str) -> list[str]:
    errors = []
    if "<!DOCTYPE" not in content:
        errors.append("Missing DOCTYPE")
    if "<html" not in content:
        errors.append("Missing <html>")
    opens = len(re.findall(r"<div[ >]", content))
    closes = len(re.findall(r"</div>", content))
    if opens != closes:
        errors.append(f"Unbalanced <div>: {opens} open / {closes} close")
    return errors


def test_project(build: dict) -> bool:
    log("═══ PHASE 4: TEST ═══")
    slug = build["slug"]
    all_ok = True

    # pytest
    code, out, err = run(
        "python3 -m pytest tests/test_opportunity_scanner.py -v --noconftest --tb=short",
        timeout=60,
    )
    if code == 0:
        log(f"  ✅ Unit tests passed")
    else:
        log(f"  ⚠️ Tests failed: {err[:150]}")
        all_ok = False

    # HTML validation
    project_dir = Path(build["project_dir"])
    for html_file in project_dir.glob("*.html"):
        errors = _validate_html(html_file.read_text(encoding="utf-8"))
        if errors:
            log(f"  ⚠️ {html_file.name}: {errors}")
            all_ok = False
        else:
            log(f"  ✅ {html_file.name} valid")

    # marketplace JSON
    if MARKETPLACE_JSON.exists():
        try:
            json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
            log("  ✅ projects.json valid")
        except json.JSONDecodeError as e:
            log(f"  ⚠️ projects.json invalid: {e}")
            all_ok = False

    return all_ok


# ---------------------------------------------------------------------------
# Phase 5: PUSH
# ---------------------------------------------------------------------------

def push_to_git(build: dict, ok: bool) -> str:
    log("═══ PHASE 5: PUSH ═══")
    slug = build["slug"]
    # Truncate branch name to avoid git ref limits
    short_slug = slug[:30]
    branch = f"feat/auto-{short_slug}"
    msg = f"feat(auto): {slug}" + ("" if ok else " (tests failed)")

    msg_escaped = msg.replace('"', '\\"')
    cmds = [
        "git add -A",
        f'git commit -m "{msg_escaped}"',
        f"git checkout -b {branch} 2>/dev/null || git checkout {branch}",
        f"git push -u origin {branch}",
    ]
    code, out, err = run(" && ".join(cmds), timeout=30)
    if code != 0:
        # If branch already exists on remote, just push
        code2, _, err2 = run(f"git push origin {branch}", timeout=20)
        if code2 != 0:
            log(f"Push failed: {err2[:200]}")
            return ""

    log(f"Pushed to {branch}")
    return branch


# ---------------------------------------------------------------------------
# Phase 6: PUBLISH to marketplace
# ---------------------------------------------------------------------------

def publish_to_marketplace(build: dict, branch: str) -> bool:
    log("═══ PHASE 6: PUBLISH ═══")
    slug = build["slug"]
    project_dir = Path(build["project_dir"])
    proj_file = project_dir / "pipeline_output.json"

    if not proj_file.exists():
        log("No pipeline_output.json")
        return False

    try:
        proj = json.loads(proj_file.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        log("Invalid pipeline_output.json")
        return False

    # Load or init marketplace
    if MARKETPLACE_JSON.exists():
        try:
            mp = json.loads(MARKETPLACE_JSON.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            mp = {"generated_at": NOW.isoformat(), "total_projects": 0, "projects": []}
    else:
        mp = {"generated_at": NOW.isoformat(), "total_projects": 0, "projects": []}

    # Skip if already present
    if any(p.get("id") == slug for p in mp["projects"]):
        log(f"{slug} already in marketplace")
        return True

    cat = proj.get("category", "other")
    agents = proj.get("agents", 4)
    entry = {
        "id": slug,
        "name": proj.get("idea", slug).split("—")[0].strip()[:60],
        "description": proj.get("research", {}).get("problem_statement", "")[:120],
        "category": cat,
        "icon": ICON_MAP.get(cat, "⚡"),
        "tags": [f"{agents} Agents"] + proj.get("tags", [])[:2],
        "agents": agents,
        "github_url": (
            f"https://github.com/phanindraintelligenzit-afk/"
            f"AgentsFactory/tree/{branch}/{slug}"
        ),
        "stars": 0, "forks": 0,
        "language": "Python",
        "monetization": proj.get("monetization", "Free repo + custom quote"),
        "updated_at": NOW.isoformat(),
    }

    mp["projects"].append(entry)
    mp["total_projects"] = len(mp["projects"])
    mp["generated_at"] = NOW.isoformat()

    MARKETPLACE_JSON.write_text(
        json.dumps(mp, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    log(f"Added {slug} → {mp['total_projects']} projects in marketplace")

    # Add filter tab to HTML if new category
    if MARKETPLACE_HTML.exists():
        html = MARKETPLACE_HTML.read_text(encoding="utf-8")
        btn = f'data-filter="{cat}"'
        if btn not in html:
            new_btn = (
                f'        <button class="filter-tab" data-filter="{cat}">'
                f'{cat.title()}</button>\n'
            )
            html = html.replace(
                '        <button class="filter-tab" data-filter="realestate">Real Estate</button>\n',
                '        <button class="filter-tab" data-filter="realestate">Real Estate</button>\n'
                + new_btn,
            )
            MARKETPLACE_HTML.write_text(html, encoding="utf-8")
            log(f"Added '{cat}' filter tab")

    code, _, err = run(
        f"git add docs/data/projects.json docs/marketplace.html && "
        f"git commit -m {shlex.quote(f'marketplace: add {slug}')} && "
        f"git push origin main",
        timeout=30,
    )
    if code != 0:
        log(f"Marketplace push failed: {err[:200]}")
        return False

    log(f"✅ {slug} published to marketplace")
    return True


# ---------------------------------------------------------------------------
# Orchestrator
# ---------------------------------------------------------------------------

def run_pipeline() -> str:
    log("╔══════════════════════════════════════════╗")
    log("║  AIdentify Autonomous Pipeline          ║")
    log("╚══════════════════════════════════════════╝")

    # 1. SCAN
    opportunities = scan_opportunities()
    if not opportunities:
        return "Pipeline aborted: no opportunities."

    # 2. SELECT
    sel = select_opportunity(opportunities)
    if not sel:
        return "Pipeline aborted: nothing new to build (all below threshold or already done)."

    # 3. BUILD
    build = build_project(sel)
    if "error" in build:
        return f"BUILD FAILED: {build['error']}"

    # 4. TEST
    ok = test_project(build)

    # 5. PUSH
    branch = push_to_git(build, ok)
    if not branch:
        return f"PUSH FAILED for {build['slug']}"

    # 6. PUBLISH
    published = publish_to_marketplace(build, branch)

    # Summary
    summary = f"""
╔══════════════════════════════════════════╗
║  ✅ Pipeline Complete                    ║
╠══════════════════════════════════════════╣
║  Pick:    {sel['title'][:30]:30s}     ║
║  Score:   {sel['score']}/100                      ║
║  Files:   {build['file_count']:3d}                       ║
║  Tests:   {'PASS' if ok else 'FAIL':4s}                      ║
║  Branch:  {branch[:30]:30s}     ║
║  Live:    {'✅' if published else '⚠️':2s}                        ║
╚══════════════════════════════════════════╝"""
    log(summary)
    return summary


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    result = run_pipeline()
    print(result)
