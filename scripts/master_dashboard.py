"""
AgentsFactory Master Dashboard — The Kanban + Agent Activity + Cron Health center.

Run with:
    cd C:/Users/Admin/Projects/AgentsFactory
    uv run streamlit run scripts/master_dashboard.py

Panels:
  1. Overview KPIs — agents, tasks, crons, messages
  2. Agent Activity Feed — live War Room messages + action log
  3. Task Board — Kanban board (backlog / assigned / in_progress / done / blocked)
  4. Agent Performance — per-agent stats, charts
  5. Cron Health — all cron jobs, last run, success rate
  6. War Room — read-only view of recent Slack messages
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
from pipeline_manager import PipelineManager, OPPORTUNITY_TEMPLATES, format_project_summary

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AgentsFactory — Master Dashboard",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ───────────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main-header {
        font-size: 28px;
        font-weight: 700;
        color: #1a1a2e;
        margin-bottom: 4px;
    }
    .sub-header {
        font-size: 14px;
        color: #666;
        margin-bottom: 20px;
    }
    .kpi-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border-radius: 12px;
        padding: 16px 20px;
        color: white;
        text-align: center;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
    }
    .kpi-value {
        font-size: 32px;
        font-weight: 800;
        line-height: 1.2;
    }
    .kpi-label {
        font-size: 12px;
        opacity: 0.85;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .kpi-green {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        box-shadow: 0 4px 15px rgba(17, 153, 142, 0.3);
    }
    .kpi-orange {
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
        box-shadow: 0 4px 15px rgba(240, 147, 251, 0.3);
    }
    .kpi-blue {
        background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);
        box-shadow: 0 4px 15px rgba(79, 172, 254, 0.3);
    }
    .kpi-dark {
        background: linear-gradient(135deg, #2c3e50 0%, #4ca1af 100%);
        box-shadow: 0 4px 15px rgba(44, 62, 80, 0.3);
    }
    .kpi-red {
        background: linear-gradient(135deg, #eb3349 0%, #f45c43 100%);
        box-shadow: 0 4px 15px rgba(235, 51, 73, 0.3);
    }
    .kpi-teal {
        background: linear-gradient(135deg, #0cebeb 0%, #20e3b2 100%);
        box-shadow: 0 4px 15px rgba(12, 235, 235, 0.3);
    }
    .agent-badge {
        display: inline-block;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: 600;
        margin: 2px;
    }
    .status-done { background: #d4edda; color: #155724; }
    .status-progress { background: #fff3cd; color: #856404; }
    .status-blocked { background: #f8d7da; color: #721c24; }
    .status-backlog { background: #e2e3e5; color: #383d41; }
    .status-assigned { background: #cce5ff; color: #004085; }
    div[data-testid="stMetricValue"] { font-size: 24px; }
</style>
""", unsafe_allow_html=True)


# ── Data layer ───────────────────────────────────────────────────────────────
@st.cache_resource
def get_logger() -> ActivityLogger:
    init_activity_db()
    return ActivityLogger()


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


@st.cache_resource
def get_pipeline_manager() -> PipelineManager:
    return PipelineManager()


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
        st.markdown(
            '<meta http-equiv="refresh" content="30">',
            unsafe_allow_html=True,
        )

    st.divider()
    st.markdown("### Quick Actions")

    if st.button("🔄 Refresh Data", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

    if st.button("📊 Run Standup", use_container_width=True):
        st.info("Run: `python scripts/owl_orchestrate.py --daily-standup`")

    if st.button("📋 Sprint Review", use_container_width=True):
        st.info("Run: `python scripts/owl_orchestrate.py --sprint-review`")

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

# ── Main content ─────────────────────────────────────────────────────────────
logger = get_logger()
summary = get_summary(logger)

st.markdown('<div class="main-header">🤖 AgentsFactory — Master Dashboard</div>', unsafe_allow_html=True)
st.markdown(
    f'<div class="sub-header">Last updated: {datetime.now().strftime("%d %b %Y %H:%M:%S IST")} | '
    f"Showing: {time_range}</div>",
    unsafe_allow_html=True,
)

# ── Row 1: KPI Cards ────────────────────────────────────────────────────────
c1, c2, c3, c4, c5, c6, c7, c8 = st.columns(8)

kpi_data = [
    (c1, "Actions Today", summary.get("total_actions_today", 0), "kpi-blue"),
    (c2, "This Week", summary.get("total_actions_week", 0), "kpi-dark"),
    (c3, "Active Tasks", summary.get("active_tasks", 0), "kpi-orange"),
    (c4, "Done", summary.get("completed_tasks", 0), "kpi-green"),
    (c5, "Backlog", summary.get("backlog_tasks", 0), "kpi-dark"),
    (c6, "Blocked", summary.get("blocked_tasks", 0), "kpi-red"),
    (c7, "Cron OK", f"{summary.get('healthy_crons', 0)}/{summary.get('total_crons', 0)}", "kpi-teal"),
    (c8, "WR Msgs Today", summary.get("war_room_messages_today", 0), "kpi-blue"),
]

for col, label, value, css_class in kpi_data:
    col.markdown(
        f'<div class="kpi-card {css_class}">'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-label">{label}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )

st.markdown("---")

# ── Row 2: Agent Activity + War Room ────────────────────────────────────────
left_col, right_col = st.columns([3, 2])

with left_col:
    st.subheader("📡 Agent Activity Feed")

    activity = get_recent_activity(logger, limit=50, hours=hours)

    if activity:
        for item in activity[:20]:
            agent = item["agent_name"]
            action = item["action"]
            target = item.get("target", "")
            status = item.get("status", "")
            details = item.get("details", "")
            ts = item.get("created_at", "")

            # Color-code by status
            if status == "completed":
                status_color = "🟢"
            elif status == "in_progress":
                status_color = "🟡"
            elif status == "blocked":
                status_color = "🔴"
            else:
                status_color = "⚪"

            with st.expander(f"{status_color} **{agent}** — `{action}` → {target or '—'} _{ts}_"):
                if details:
                    st.markdown(details)
    else:
        st.info("No agent activity in the selected time range. Agents will appear here as they work.")

with right_col:
    st.subheader("💬 War Room (Recent)")

    wr_messages = get_war_room_history(logger, limit=20, hours=max(hours, 24))

    if wr_messages:
        for msg in wr_messages[:15]:
            agent = msg["agent_name"]
            message = msg.get("message", "")
            task_ref = msg.get("task_ref", "")
            status_tag = msg.get("status_tag", "")
            ts = msg.get("created_at", "")

            badge_class = "status-backlog"
            if "[DONE]" in status_tag or "[COMPLETE]" in status_tag:
                badge_class = "status-done"
            elif "[IN_PROGRESS]" in status_tag or "[ACKNOWLEDGED]" in status_tag:
                badge_class = "status-progress"
            elif "[BLOCKED]" in status_tag:
                badge_class = "status-blocked"
            elif "[ASSIGNED]" in status_tag:
                badge_class = "status-assigned"

            st.markdown(
                f'<div style="padding:8px 12px; margin:4px 0; background:#f8f9fa; '
                f'border-radius:8px; border-left:3px solid #667eea;">'
                f'<span class="agent-badge {badge_class}">{agent}</span> '
                f'<span style="font-size:11px;color:#999;">{status_tag}</span>'
                f'<br/><span style="font-size:13px;">{message[:120]}</span>'
                f'<br/><span style="font-size:10px;color:#aaa;">{task_ref} | {ts}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
    else:
        st.info("No War Room messages yet. Agents post to #agentsfactory-war-room.")

st.markdown("---")

# ── Row 3: Task Board (Kanban) ──────────────────────────────────────────────
st.subheader("📋 Task Board")

tasks = get_tasks(logger)

if tasks:
    # Group by status
    cols_map = {
        "backlog": [],
        "assigned": [],
        "in_progress": [],
        "completed": [],
        "blocked": [],
    }
    for t in tasks:
        s = t.get("status", "backlog")
        if s in cols_map:
            cols_map[s].append(t)
        else:
            cols_map["backlog"].append(t)

    kanban_cols = st.columns(5)

    kanban_config = [
        ("backlog", "📥 Backlog", "#6c757d"),
        ("assigned", "📌 Assigned", "#007bff"),
        ("in_progress", "🔄 In Progress", "#ffc107"),
        ("completed", "✅ Done", "#28a745"),
        ("blocked", "🚫 Blocked", "#dc3545"),
    ]

    for col, (status, title, color) in zip(kanban_cols, kanban_config):
        with col:
            st.markdown(f"**{title}** ({len(cols_map[status])})")
            for t in cols_map[status]:
                priority = t.get("priority", "normal")
                priority_dot = {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(priority, "🟡")
                assigned = t.get("assigned_to", "Unassigned")
                title_text = t.get("title", "Untitled")
                task_id = t.get("id", "")

                st.markdown(
                    f'<div style="padding:10px; margin:6px 0; background:white; '
                    f'border-radius:8px; border-left:4px solid {color}; '
                    f'box-shadow:0 1px 3px rgba(0,0,0,0.1);">'
                    f'<div style="font-size:13px;font-weight:600;">{priority_dot} {title_text}</div>'
                    f'<div style="font-size:11px;color:#666;margin-top:4px;">'
                    f'👤 {assigned} | `{task_id}`</div>'
                    f"</div>",
                    unsafe_allow_html=True,
                )
else:
    st.info("No tasks yet. Use `owl_orchestrate.py` to create and assign tasks.")

st.markdown("---")

# ── Row 4: Agent Performance + Cron Health ──────────────────────────────────
perf_col, cron_col = st.columns([3, 2])

with perf_col:
    st.subheader("📊 Agent Performance")

    stats = get_agent_stats(logger, hours=hours)

    if stats:
        df = pd.DataFrame(stats)

        # Bar chart: actions per agent
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=df["agent_name"],
            y=df["completed"],
            name="Completed",
            marker_color="#28a745",
        ))
        fig.add_trace(go.Bar(
            x=df["agent_name"],
            y=df["in_progress"],
            name="In Progress",
            marker_color="#ffc107",
        ))
        fig.add_trace(go.Bar(
            x=df["agent_name"],
            y=df["blocked"],
            name="Blocked",
            marker_color="#dc3545",
        ))
        fig.update_layout(
            barmode="stack",
            title=f"Actions per Agent ({time_range})",
            xaxis_title="Agent",
            yaxis_title="Actions",
            height=350,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig, use_container_width=True)

        # Data table
        st.dataframe(
            df[["agent_name", "actions", "completed", "in_progress", "blocked"]],
            use_container_width=True,
            hide_index=True,
        )
    else:
        st.info("No agent stats available yet.")

with cron_col:
    st.subheader("⏰ Cron Health")

    crons = get_cron_health(logger)

    if crons:
        for cron in crons:
            name = cron.get("name", "Unknown")
            status = cron.get("last_status", "unknown")
            last_run = cron.get("last_run_at", "Never")
            schedule = cron.get("schedule", "")
            total = cron.get("total_runs", 0)
            success = cron.get("total_success", 0)
            fail = cron.get("total_fail", 0)
            error = cron.get("last_error", "")

            if status == "ok":
                icon = "🟢"
            elif status == "error":
                icon = "🔴"
            else:
                icon = "⚪"

            rate = f"{success}/{total}" if total > 0 else "N/A"

            with st.expander(f"{icon} {name}"):
                st.markdown(f"**Schedule:** `{schedule}`")
                st.markdown(f"**Last run:** {last_run}")
                st.markdown(f"**Success rate:** {rate}")
                if error:
                    st.error(f"Last error: {error[:100]}")
    else:
        st.info("No cron health data. Cron jobs will be tracked here after first run.")

        # Show expected crons
        expected_crons = [
            "Morning Brief (8 AM daily)",
            "Business Scanner (9 AM daily)",
            "AF Outreach (9:06 AM daily)",
            "AF Social Post (10 AM weekdays)",
            "DPI-LS Report (6 PM weekdays)",
            "Daily Standup (9:30 AM daily)",
            "Sprint Planning (Mon 11 AM)",
            "Sprint Review (Fri 5 PM)",
        ]
        st.markdown("**Expected cron jobs:**")
        for c in expected_crons:
            st.markdown(f"- {c}")

st.markdown("---")

# ── Row 5: Pipelines ─────────────────────────────────────────────────────────
st.subheader("🚀 Pipelines — Opportunity → Project → Build")

pm = get_pipeline_manager()
pipelines = get_pipeline_status(pm)

if pipelines:
    for p in pipelines:
        total = p["total"]
        done = p["completed"]
        pct = (done / total * 100) if total > 0 else 0

        # Progress bar
        st.progress(int(pct) / 100, text=f"📊 {p['project_id']} — {done}/{total} tasks done ({pct:.0f}%)")

        # Task breakdown by agent
        agent_work = get_agent_workload(pm)
        if agent_work:
            cols = st.columns(len(agent_work))
            for col, (agent, data) in zip(cols, agent_work.items()):
                with col:
                    st.markdown(f"**{agent}**")
                    st.markdown(f"Total: {data['total']} | 🔄 {data['in_progress']} | ✅ {data['completed']} | 🚫 {data['blocked']}")
                    for t in data["tasks"][:3]:
                        icon = {"completed": "✅", "in_progress": "🔄", "blocked": "🚫", "assigned": "📌", "backlog": "📥"}.get(t["status"], "⚪")
                        st.markdown(f"{icon} {t['title'][:40]}")

        st.markdown("---")
else:
    st.info("No active pipelines. Create one from an opportunity below.")

# ── Create Project from Opportunity ──────────────────────────────────────────
st.subheader("💡 Create Project from Opportunity")

with st.form("create_project_form"):
    opp_col1, opp_col2 = st.columns(2)
    with opp_col1:
        selected_opp = st.selectbox(
            "Select Opportunity",
            list(OPPORTUNITY_TEMPLATES.keys()),
            format_func=lambda k: f"{OPPORTUNITY_TEMPLATES[k]['title']} ({OPPORTUNITY_TEMPLATES[k]['revenue']})",
        )
    with opp_col2:
        custom_title = st.text_input("Custom Title (optional)", placeholder="Leave blank for default")

    # Show opportunity details
    opp = OPPORTUNITY_TEMPLATES[selected_opp]
    st.markdown(f"**{opp['title']}** — {opp['tagline']}")
    st.markdown(f"Revenue: {opp['revenue']} | Build: {opp['build_weeks']} weeks | Tasks: {len(opp['tasks'])}")

    # Show task breakdown
    with st.expander("Preview task breakdown"):
        for t in opp["tasks"]:
            priority = {"high": "🔴", "normal": "🟡", "low": "🟢"}.get(t["priority"], "🟡")
            st.markdown(f"{priority} **{t['agent']}** — {t['title']}")

    if st.form_submit_button("🚀 Create Project & Assign Agents", use_container_width=True):
        result = pm.create_project(selected_opp, custom_title or None)
        if "error" in result:
            st.error(result["error"])
        else:
            st.success(f"Project created! {result['tasks_created']} tasks assigned to agents.")
            st.cache_data.clear()
            st.rerun()

st.markdown("---")

# ── Row 6: Add Task ─────────────────────────────────────────────────────────
st.subheader("➕ Quick Add Task")

with st.form("add_task_form"):
    tc1, tc2, tc3 = st.columns(3)
    with tc1:
        task_title = st.text_input("Task Title", placeholder="e.g., Fix auth middleware")
    with tc2:
        task_agent = st.selectbox(
            "Assign to",
            ["Coder", "Researcher", "Planner", "Reviewer", "Social", "Outreach", "OWL"],
        )
    with tc3:
        task_priority = st.selectbox("Priority", ["high", "normal", "low"], index=1)

    task_desc = st.text_area("Description", placeholder="Task details...", height=80)

    if st.form_submit_button("Create Task", use_container_width=True):
        if task_title:
            task_id = f"task-{datetime.now().strftime('%Y%m%d%H%M%S')}"
            logger.create_task(
                task_id=task_id,
                title=task_title,
                assigned_to=task_agent,
                description=task_desc,
                priority=task_priority,
                created_by="Phani (Dashboard)",
            )
            logger.log("Phani", "create_task", task_title, "completed", f"Assigned to {task_agent}")
            st.success(f"Task `{task_id}` created and assigned to {task_agent}!")
            st.cache_data.clear()
            st.rerun()
        else:
            st.error("Please enter a task title.")

# ── Footer ──────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f"<div style='text-align:center; color:#999; font-size:12px;'>"
    f"AgentsFactory Master Dashboard | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | "
    f"Auto-refresh: {'ON' if auto_refresh else 'OFF'} | "
    f"Data refreshes every 30s</div>",
    unsafe_allow_html=True,
)
