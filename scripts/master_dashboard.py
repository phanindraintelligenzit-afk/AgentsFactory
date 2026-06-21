"""
AgentsFactory Master Dashboard — Kanban Board + Agent Activity + Cron Health.

Run with:
    cd C:/Users/Admin/Projects/AgentsFactory
    uv run streamlit run scripts/master_dashboard.py --server.port 8501

Panels:
  1. KPI Overview — agents, tasks, crons, messages
  2. Kanban Board — drag-and-drop style task board per agent
  3. Agent Activity Feed — live War Room messages + action log
  4. Agent Performance — per-agent stats, charts
  5. Cron Health — all cron jobs, last run, success rate
  6. Pipelines — active projects with progress
"""

from __future__ import annotations

import json
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add scripts dir to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from agent_activity import ActivityLogger, init_activity_db
from pipeline_manager import PipelineManager, OPPORTUNITY_TEMPLATES

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentsFactory — Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS — Stripe-grade design ─────────────────────────────────────────
st.markdown("""
<style>
  /* Design tokens */
  :root {
    --purple: #533afd;
    --purple-hover: #4434d4;
    --purple-light: #b9b9f9;
    --navy: #061b31;
    --slate: #64748d;
    --dark-slate: #273951;
    --border: #e5edf5;
    --bg: #ffffff;
    --bg-soft: #f6f9fc;
    --brand-dark: #1c1e54;
    --success: #15be53;
    --warning: #d97706;
    --danger: #dc2626;
    --shadow: rgba(50,50,93,0.25) 0px 30px 45px -30px, rgba(0,0,0,0.1) 0px 18px 36px -18px;
    --shadow-sm: rgba(23,23,23,0.08) 0px 15px 35px 0px;
    --radius: 6px;
    --radius-sm: 4px;
    --radius-lg: 8px;
  }

  /* Global */
  .main .block-container { padding-top: 2rem; padding-bottom: 2rem; }
  body { font-family: 'Inter', system-ui, sans-serif; color: var(--navy); }

  /* KPI Cards */
  .kpi-grid { display: grid; grid-template-columns: repeat(8, 1fr); gap: 12px; margin-bottom: 24px; }
  .kpi-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 16px 12px;
    text-align: center;
    box-shadow: rgba(23,23,23,0.06) 0px 3px 6px;
    transition: box-shadow 0.2s;
  }
  .kpi-card:hover { box-shadow: var(--shadow-sm); }
  .kpi-value { font-size: 28px; font-weight: 300; letter-spacing: -0.5px; color: var(--navy); line-height: 1.2; }
  .kpi-label { font-size: 11px; font-weight: 500; color: var(--slate); text-transform: uppercase; letter-spacing: 0.3px; margin-top: 4px; }
  .kpi-card.purple { border-top: 3px solid var(--purple); }
  .kpi-card.green { border-top: 3px solid var(--success); }
  .kpi-card.orange { border-top: 3px solid var(--warning); }
  .kpi-card.red { border-top: 3px solid var(--danger); }
  .kpi-card.navy { border-top: 3px solid var(--navy); }
  .kpi-card.slate { border-top: 3px solid var(--slate); }
  .kpi-card.dark { border-top: 3px solid var(--brand-dark); }
  .kpi-card.soft-purple { border-top: 3px solid var(--purple-light); }

  /* Kanban Board */
  .kanban-grid { display: grid; grid-template-columns: repeat(5, 1fr); gap: 12px; }
  .kanban-col {
    background: var(--bg-soft);
    border-radius: var(--radius-lg);
    padding: 16px;
    min-height: 400px;
  }
  .kanban-col-header {
    font-size: 13px; font-weight: 600; color: var(--slate);
    text-transform: uppercase; letter-spacing: 0.5px;
    margin-bottom: 12px; padding-bottom: 8px;
    border-bottom: 2px solid var(--border);
    display: flex; justify-content: space-between; align-items: center;
  }
  .kanban-col-header .count {
    background: var(--border); color: var(--slate);
    font-size: 11px; font-weight: 600;
    padding: 2px 8px; border-radius: 10px;
  }
  .kanban-card {
    background: var(--bg);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 14px;
    margin-bottom: 10px;
    box-shadow: rgba(23,23,23,0.04) 0px 2px 4px;
    transition: box-shadow 0.15s, transform 0.15s;
    cursor: default;
  }
  .kanban-card:hover { box-shadow: var(--shadow-sm); transform: translateY(-1px); }
  .kanban-card-title { font-size: 14px; font-weight: 500; color: var(--navy); margin-bottom: 6px; line-height: 1.3; }
  .kanban-card-meta { display: flex; justify-content: space-between; align-items: center; }
  .kanban-card-agent {
    font-size: 11px; font-weight: 500; color: var(--purple);
    background: rgba(83,58,253,0.08);
    padding: 2px 8px; border-radius: var(--radius-sm);
  }
  .kanban-card-priority {
    font-size: 10px; font-weight: 600; text-transform: uppercase; letter-spacing: 0.3px;
  }
  .priority-high { color: var(--danger); }
  .priority-normal { color: var(--warning); }
  .priority-low { color: var(--success); }

  /* Section headers */
  .section-header {
    font-size: 20px; font-weight: 300; letter-spacing: -0.3px;
    color: var(--navy); margin: 32px 0 16px;
    padding-bottom: 8px; border-bottom: 1px solid var(--border);
  }

  /* Activity feed */
  .activity-item {
    display: flex; gap: 12px; padding: 10px 0;
    border-bottom: 1px solid var(--border);
  }
  .activity-dot {
    width: 8px; height: 8px; border-radius: 50%;
    margin-top: 6px; flex-shrink: 0;
  }
  .dot-green { background: var(--success); }
  .dot-yellow { background: var(--warning); }
  .dot-red { background: var(--danger); }
  .dot-purple { background: var(--purple); }
  .activity-content { flex: 1; }
  .activity-title { font-size: 14px; font-weight: 500; color: var(--navy); }
  .activity-detail { font-size: 13px; color: var(--slate); margin-top: 2px; }
  .activity-time { font-size: 11px; color: var(--slate); white-space: nowrap; }

  /* Cron health */
  .cron-item {
    display: flex; align-items: center; gap: 12px;
    padding: 8px 0; border-bottom: 1px solid var(--border);
  }
  .cron-status { width: 10px; height: 10px; border-radius: 50%; flex-shrink: 0; }
  .cron-ok { background: var(--success); }
  .cron-error { background: var(--danger); }
  .cron-pending { background: var(--slate); }
  .cron-name { font-size: 14px; font-weight: 500; color: var(--navy); flex: 1; }
  .cron-schedule { font-size: 12px; color: var(--slate); font-family: 'JetBrains Mono', monospace; }
  .cron-rate { font-size: 12px; font-weight: 500; }

  /* Sidebar */
  .sidebar-info { font-size: 12px; color: var(--slate); margin-top: 8px; }

  /* Hide Streamlit branding */
  #MainMenu { visibility: hidden; }
  footer { visibility: hidden; }
  header { visibility: hidden; }

  /* Responsive */
  @media (max-width: 1200px) {
    .kpi-grid { grid-template-columns: repeat(4, 1fr); }
    .kanban-grid { grid-template-columns: repeat(3, 1fr); }
  }
  @media (max-width: 768px) {
    .kpi-grid { grid-template-columns: repeat(2, 1fr); }
    .kanban-grid { grid-template-columns: 1fr; }
  }
</style>
""", unsafe_allow_html=True)


# ── Data layer ───────────────────────────────────────────────────────────────
@st.cache_resource
def get_logger() -> ActivityLogger:
    init_activity_db()
    return ActivityLogger()

@st.cache_resource
def get_pipeline_manager() -> PipelineManager:
    return PipelineManager()

@st.cache_data(ttl=30)
def get_summary(_logger: ActivityLogger) -> dict:
    return _logger.get_summary()

@st.cache_data(ttl=30)
def get_agent_stats(_logger: ActivityLogger, hours: int) -> list:
    return _logger.get_agent_stats(hours=hours)

@st.cache_data(ttl=30)
def get_recent_activity(_logger: ActivityLogger, limit: int, hours: int) -> list:
    return _logger.get_recent_activity(limit=limit, hours=hours)

@st.cache_data(ttl=30)
def get_war_room_history(_logger: ActivityLogger, limit: int, hours: int) -> list:
    return _logger.get_war_room_history(limit=limit, hours=hours)

@st.cache_data(ttl=30)
def get_tasks(_logger: ActivityLogger) -> list:
    return _logger.get_tasks()

@st.cache_data(ttl=30)
def get_cron_health(_logger: ActivityLogger) -> list:
    return _logger.get_cron_health()

@st.cache_data(ttl=30)
def get_pipeline_status(_pm: PipelineManager) -> list:
    return _pm.get_pipeline_status()

@st.cache_data(ttl=30)
def get_agent_workload(_pm: PipelineManager) -> dict:
    return _pm.get_agent_workload()


# ── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🤖 AgentsFactory")
    st.markdown("*Master Dashboard*")
    st.divider()

    time_range = st.selectbox(
        "Time Range",
        ["Last 1 hour", "Last 4 hours", "Last 24 hours", "Last 7 days"],
        index=2,
    )
    hours_map = {"Last 1 hour": 1, "Last 4 hours": 4, "Last 24 hours": 24, "Last 7 days": 168}
    hours = hours_map[time_range]

    auto_refresh = st.checkbox("Auto-refresh (30s)", value=True)
    if auto_refresh:
        st.markdown('<meta http-equiv="refresh" content="30">', unsafe_allow_html=True)

    st.divider()

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    st.divider()
    st.markdown("### Active Agents")
    agents = {
        "🦉 OWL": "Orchestrator",
        "🔬 Researcher": "Research",
        "💻 Coder": "Development",
        "📋 Planner": "Planning",
        "🔍 Reviewer": "QA/Review",
        "📱 Social": "Social Media",
        "📧 Outreach": "Lead Outreach",
    }
    for emoji_name, role in agents.items():
        st.markdown(f"`{emoji_name}` {role}")

    st.divider()
    st.markdown(f"<div class='sidebar-info'>Last updated: {datetime.now().strftime('%d %b %H:%M:%S')}</div>", unsafe_allow_html=True)

# ── Main content ─────────────────────────────────────────────────────────────
logger = get_logger()
summary = get_summary(logger)

st.markdown("# 🤖 AgentsFactory — Dashboard")
st.markdown(f"*{datetime.now().strftime('%A, %d %B %Y %H:%M:%S IST')} | {time_range}*")

# ── Row 1: KPI Cards ────────────────────────────────────────────────────────
kpi_data = [
    ("Actions Today", summary.get("total_actions_today", 0), "purple"),
    ("This Week", summary.get("total_actions_week", 0), "navy"),
    ("Active Tasks", summary.get("active_tasks", 0), "orange"),
    ("Completed", summary.get("completed_tasks", 0), "green"),
    ("Backlog", summary.get("backlog_tasks", 0), "slate"),
    ("Blocked", summary.get("blocked_tasks", 0), "red"),
    ("Cron OK", f"{summary.get('healthy_crons', 0)}/{summary.get('total_crons', 0)}", "dark"),
    ("WR Messages", summary.get("war_room_messages_today", 0), "soft-purple"),
]

cols = st.columns(8)
for col, (label, value, color) in zip(cols, kpi_data):
    col.markdown(
        f'<div class="kpi-card {color}">'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

# ── Row 2: Kanban Board ──────────────────────────────────────────────────────
st.markdown('<div class="section-header">📋 Kanban Board</div>', unsafe_allow_html=True)

tasks = get_tasks(logger)

if tasks:
    cols_map = {"backlog": [], "assigned": [], "in_progress": [], "completed": [], "blocked": []}
    for t in tasks:
        s = t.get("status", "backlog")
        cols_map.get(s, cols_map["backlog"]).append(t)

    kanban_cols = st.columns(5)
    kanban_config = [
        ("backlog", "📥 Backlog", "#6c757d"),
        ("assigned", "📌 Assigned", "#533afd"),
        ("in_progress", "🔄 In Progress", "#d97706"),
        ("completed", "✅ Done", "#15be53"),
        ("blocked", "🚫 Blocked", "#dc2626"),
    ]

    for col, (status, title, color) in zip(kanban_cols, kanban_config):
        with col:
            st.markdown(
                f'<div class="kanban-col">'
                f'<div class="kanban-col-header">'
                f'<span>{title}</span>'
                f'<span class="count">{len(cols_map[status])}</span>'
                f'</div>',
                unsafe_allow_html=True,
            )
            for t in cols_map[status]:
                priority = t.get("priority", "normal")
                priority_class = {"high": "priority-high", "normal": "priority-normal", "low": "priority-low"}.get(priority, "priority-normal")
                priority_icon = {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(priority, "🟡")
                assigned = t.get("assigned_to", "Unassigned")
                title_text = t.get("title", "Untitled")

                st.markdown(
                    f'<div class="kanban-card">'
                    f'<div class="kanban-card-title">{title_text}</div>'
                    f'<div class="kanban-card-meta">'
                    f'<span class="kanban-card-agent">{assigned}</span>'
                    f'<span class="kanban-card-priority {priority_class}">{priority_icon} {priority}</span>'
                    f'</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
            st.markdown("</div>", unsafe_allow_html=True)
else:
    st.info("No tasks yet. Create a project from the Pipelines tab below.")

# ── Row 3: Agent Activity + War Room ────────────────────────────────────────
st.markdown('<div class="section-header">📡 Activity & War Room</div>', unsafe_allow_html=True)

left_col, right_col = st.columns([3, 2])

with left_col:
    st.markdown("**Recent Activity**")
    activity = get_recent_activity(logger, limit=30, hours=hours)
    if activity:
        for item in activity[:15]:
            agent = item["agent_name"]
            action = item.get("action", "")
            target = item.get("target", "")
            status = item.get("status", "")
            details = item.get("details", "")
            ts = item.get("created_at", "")

            dot_class = {"completed": "dot-green", "in_progress": "dot-yellow", "blocked": "dot-red"}.get(status, "dot-purple")

            st.markdown(
                f'<div class="activity-item">'
                f'<div class="activity-dot {dot_class}"></div>'
                f'<div class="activity-content">'
                f'<div class="activity-title">{agent} — {action} → {target or "—"}</div>'
                f'<div class="activity-detail">{details[:100]}</div>'
                f'</div>'
                f'<div class="activity-time">{ts[:16]}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No activity in the selected time range.")

with right_col:
    st.markdown("**War Room**")
    wr_messages = get_war_room_history(logger, limit=20, hours=max(hours, 24))
    if wr_messages:
        for msg in wr_messages[:10]:
            agent = msg["agent_name"]
            message = msg.get("message", "")[:120]
            status_tag = msg.get("status_tag", "")
            ts = msg.get("created_at", "")[:16]
            st.markdown(
                f'<div class="activity-item">'
                f'<div class="activity-dot dot-purple"></div>'
                f'<div class="activity-content">'
                f'<div class="activity-title">{agent} {status_tag}</div>'
                f'<div class="activity-detail">{message}</div>'
                f'</div>'
                f'<div class="activity-time">{ts}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No War Room messages yet.")

# ── Row 4: Agent Performance + Cron Health ──────────────────────────────────
st.markdown('<div class="section-header">📊 Performance & Health</div>', unsafe_allow_html=True)

perf_col, cron_col = st.columns([3, 2])

with perf_col:
    st.markdown("**Agent Performance**")
    stats = get_agent_stats(logger, hours=hours)
    if stats:
        df = pd.DataFrame(stats)
        fig = go.Figure()
        fig.add_trace(go.Bar(x=df["agent_name"], y=df["completed"], name="Completed", marker_color="#15be53"))
        fig.add_trace(go.Bar(x=df["agent_name"], y=df["in_progress"], name="In Progress", marker_color="#d97706"))
        fig.add_trace(go.Bar(x=df["agent_name"], y=df["blocked"], name="Blocked", marker_color="#dc2626"))
        fig.update_layout(
            barmode="stack", title=f"Actions per Agent ({time_range})",
            xaxis_title="Agent", yaxis_title="Actions", height=320,
            margin=dict(l=20, r=20, t=40, b=20),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#64748d"),
        )
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No agent stats available yet.")

with cron_col:
    st.markdown("**Cron Health**")
    crons = get_cron_health(logger)
    if crons:
        for cron in crons:
            name = cron.get("name", "Unknown")
            status = cron.get("last_status", "unknown")
            schedule = cron.get("schedule", "")
            total = cron.get("total_runs", 0)
            success = cron.get("total_success", 0)

            status_class = {"ok": "cron-ok", "error": "cron-error"}.get(status, "cron-pending")
            rate = f"{success}/{total}" if total > 0 else "N/A"

            st.markdown(
                f'<div class="cron-item">'
                f'<div class="cron-status {status_class}"></div>'
                f'<div class="cron-name">{name}</div>'
                f'<div class="cron-schedule">{schedule}</div>'
                f'<div class="cron-rate">{rate}</div>'
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No cron health data yet.")

# ── Row 5: Pipelines ────────────────────────────────────────────────────────
st.markdown('<div class="section-header">🚀 Pipelines</div>', unsafe_allow_html=True)

pm = get_pipeline_manager()
pipelines = get_pipeline_status(pm)

if pipelines:
    for p in pipelines:
        total = p["total"]
        done = p["completed"]
        pct = (done / total * 100) if total > 0 else 0
        st.progress(int(pct) / 100, text=f"📊 {p['project_id'][:30]} — {done}/{total} tasks done ({pct:.0f}%)")
else:
    st.info("No active pipelines.")

# ── Row 6: Quick Add Task ───────────────────────────────────────────────────
st.markdown('<div class="section-header">➕ Quick Add Task</div>', unsafe_allow_html=True)

with st.form("add_task_form"):
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        task_title = st.text_input("Task Title", placeholder="e.g., Fix auth middleware")
    with tc2:
        task_agent = st.selectbox("Assign to", ["Coder", "Researcher", "Planner", "Reviewer", "Social", "Outreach", "OWL"])
    with tc3:
        task_priority = st.selectbox("Priority", ["high", "normal", "low"], index=1)
    task_desc = st.text_area("Description", placeholder="Task details...", height=80)
    if st.form_submit_button("Create Task", use_container_width=True):
        if task_title:
            task_id = f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.create_task(task_id=task_id, title=task_title, assigned_to=task_agent,
                               description=task_desc, priority=task_priority, created_by="Dashboard")
            logger.log("Phani", "create_task", task_title, "completed", f"Assigned to {task_agent}")
            st.success(f"Task created and assigned to {task_agent}!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Please enter a task title.")

# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center; color:#9ca3af; font-size:12px;'>"
    f"AgentsFactory Dashboard | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Auto-refresh: {'ON' if auto_refresh else 'OFF'}</div>",
    unsafe_allow_html=True,
)
