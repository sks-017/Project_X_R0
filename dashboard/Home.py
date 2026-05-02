"""
Acron dashboard home — Intelligence meets reality.
"""
import html
import os
from datetime import datetime, timedelta

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

import auth

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="Acron | S7 Corp",
    page_icon="⬡",
    layout="wide",
    initial_sidebar_state="expanded",
)


def api_get(path, default):
    try:
        response = requests.get(f"{API_URL}{path}", timeout=5)
        if response.status_code == 200:
            return response.json(), None
        return default, f"{response.status_code}: {response.text[:140]}"
    except Exception as exc:
        return default, str(exc)


def api_post(path, payload=None):
    headers = {}
    if st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    response = requests.post(f"{API_URL}{path}", json=payload or {}, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


def esc(value):
    return html.escape(str(value if value is not None else ""))


def inject_css():
    st.markdown(
        """
        <style>
        :root {
            --ink: #111827;
            --muted: #5b6678;
            --subtle: #eef2f6;
            --panel: #ffffff;
            --line: #d7dee8;
            --green: #0c8f6d;
            --blue: #2563eb;
            --amber: #b7791f;
            --red: #c2412d;
            --violet: #6d5dfc;
        }

        html, body, [data-testid="stAppViewContainer"] {
            background: #f4f6f9;
            color: var(--ink);
        }

        .block-container {
            max-width: 1580px;
            padding-top: 1rem;
            padding-bottom: 2rem;
        }

        [data-testid="stSidebar"] {
            background: #111827;
            border-right: 1px solid #263241;
        }

        [data-testid="stSidebar"] * {
            color: #f8fafc;
        }

        [data-testid="stSidebar"] [data-testid="stCaptionContainer"] {
            color: #aab4c3;
        }

        h1, h2, h3 {
            color: var(--ink);
            letter-spacing: 0;
        }

        div[data-testid="stMetric"] {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            padding: 14px 16px;
            box-shadow: 0 1px 1px rgba(17, 24, 39, .04);
            min-height: 104px;
        }

        div[data-testid="stMetricLabel"] p {
            color: var(--muted);
            font-size: .82rem;
            font-weight: 650;
        }

        div[data-testid="stMetricValue"] {
            color: var(--ink);
        }

        .topbar {
            align-items: center;
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            gap: 18px;
            margin: 0 0 14px;
            padding: 14px 16px;
        }

        .brand-lockup {
            display: flex;
            gap: 12px;
            align-items: center;
            min-width: 260px;
        }

        .brand-mark {
            align-items: center;
            background: #111827;
            border: 1px solid #263241;
            border-radius: 8px;
            color: #ffffff;
            display: flex;
            font-weight: 800;
            height: 42px;
            justify-content: center;
            width: 42px;
        }

        .brand-title {
            font-size: 1.05rem;
            font-weight: 800;
            line-height: 1.1;
        }

        .brand-subtitle {
            color: var(--muted);
            font-size: .8rem;
            margin-top: 2px;
        }

        .status-strip {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 8px;
        }

        .status-pill {
            align-items: center;
            background: #f8fafc;
            border: 1px solid var(--line);
            border-radius: 999px;
            color: var(--muted);
            display: flex;
            font-size: .78rem;
            font-weight: 700;
            gap: 7px;
            min-height: 30px;
            padding: 5px 10px;
            white-space: nowrap;
        }

        .dot {
            border-radius: 50%;
            display: inline-block;
            height: 8px;
            width: 8px;
        }

        .dot-ok {background: var(--green);}
        .dot-warn {background: var(--amber);}
        .dot-bad {background: var(--red);}

        .section-header {
            align-items: baseline;
            display: flex;
            justify-content: space-between;
            gap: 18px;
            margin: 12px 0 10px;
        }

        .section-title {
            color: var(--ink);
            font-size: 1rem;
            font-weight: 800;
        }

        .section-note {
            color: var(--muted);
            font-size: .82rem;
            text-align: right;
        }

        .panel {
            background: var(--panel);
            border: 1px solid var(--line);
            border-radius: 8px;
            box-shadow: 0 1px 1px rgba(17, 24, 39, .04);
            padding: 14px;
        }

        .action-row {
            display: grid;
            gap: 10px;
            grid-template-columns: repeat(2, minmax(0, 1fr));
        }

        .action-tile {
            background: #f8fafc;
            border: 1px solid var(--line);
            border-radius: 8px;
            min-height: 88px;
            padding: 12px;
        }

        .action-title {
            color: var(--ink);
            font-size: .88rem;
            font-weight: 800;
            margin-bottom: 5px;
        }

        .action-copy {
            color: var(--muted);
            font-size: .8rem;
            line-height: 1.35;
        }

        .andon-grid {
            display: grid;
            gap: 10px;
            grid-template-columns: repeat(4, minmax(0, 1fr));
        }

        .andon-tile {
            background: #ffffff;
            border: 1px solid var(--line);
            border-left: 5px solid var(--green);
            border-radius: 8px;
            min-height: 112px;
            padding: 12px;
        }

        .andon-tile.watch {border-left-color: var(--amber);}
        .andon-tile.critical {border-left-color: var(--red);}
        .andon-title {
            align-items: center;
            display: flex;
            font-size: .92rem;
            font-weight: 850;
            justify-content: space-between;
            margin-bottom: 7px;
        }
        .andon-meta {
            color: var(--muted);
            font-size: .78rem;
            line-height: 1.45;
        }
        .badge {
            border-radius: 999px;
            font-size: .7rem;
            font-weight: 800;
            padding: 3px 8px;
            text-transform: uppercase;
        }
        .badge-stable {background: #e8f7f1; color: var(--green);}
        .badge-watch {background: #fff4db; color: var(--amber);}
        .badge-critical {background: #fde8e4; color: var(--red);}

        .mini-table {
            width: 100%;
            border-collapse: collapse;
            font-size: .82rem;
        }
        .mini-table th {
            color: var(--muted);
            font-weight: 750;
            padding: 8px 6px;
            text-align: left;
            border-bottom: 1px solid var(--line);
        }
        .mini-table td {
            padding: 9px 6px;
            border-bottom: 1px solid #edf1f5;
        }
        .mini-table tr:last-child td {
            border-bottom: 0;
        }

        .empty-state {
            background: #ffffff;
            border: 1px dashed #b9c3d2;
            border-radius: 8px;
            color: var(--muted);
            padding: 18px;
        }

        div[data-testid="stDataFrame"] {
            border: 1px solid var(--line);
            border-radius: 8px;
        }

        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }

        .stTabs [data-baseweb="tab"] {
            background: #ffffff;
            border: 1px solid var(--line);
            border-radius: 8px;
            color: var(--muted);
            font-weight: 700;
            height: 38px;
            padding: 0 14px;
        }

        .stTabs [aria-selected="true"] {
            background: #111827;
            color: #ffffff;
        }

        @media (max-width: 1100px) {
            .topbar {align-items: flex-start; flex-direction: column;}
            .status-strip {justify-content: flex-start;}
            .andon-grid {grid-template-columns: repeat(2, minmax(0, 1fr));}
            .action-row {grid-template-columns: 1fr;}
        }

        @media (max-width: 680px) {
            .andon-grid {grid-template-columns: 1fr;}
            .section-header {align-items: flex-start; flex-direction: column;}
            .section-note {text-align: left;}
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def health_pill(name, status):
    ok = status in {"up", "connected", "ready", "running", "healthy"}
    dot = "dot-ok" if ok else "dot-warn"
    label = status or "unknown"
    return f'<div class="status-pill"><span class="dot {dot}"></span>{esc(name)}: {esc(label)}</div>'


def build_machine_frame(machine_master, machines, oee):
    oee_by_id = {item.get("equipment_id"): item for item in oee}
    rows = []
    if machine_master:
        for machine in machine_master:
            equipment_id = machine.get("equipment_id")
            machine_oee = oee_by_id.get(equipment_id, {})
            live = machines.get(equipment_id, {})
            metrics = live.get("metrics", {}) if isinstance(live, dict) else {}
            value = machine_oee.get("oee")
            if value is None:
                state = "Waiting"
            elif value < 75:
                state = "Critical"
            elif value < 85:
                state = "Watch"
            else:
                state = "Stable"
            rows.append(
                {
                    "equipment_id": equipment_id,
                    "line": machine.get("line") or "Unassigned",
                    "cell": machine.get("cell") or "Unassigned",
                    "type": machine.get("equipment_type") or "",
                    "process": machine.get("process") or "",
                    "model": machine.get("mold_model") or "",
                    "protocol": machine.get("plc_protocol") or "simulator",
                    "cycle_time": metrics.get("cycle_time"),
                    "oee": value,
                    "availability": machine_oee.get("availability"),
                    "performance": machine_oee.get("performance"),
                    "quality": machine_oee.get("quality"),
                    "state": state,
                }
            )
    else:
        for equipment_id, live in machines.items():
            metrics = live.get("metrics", {}) if isinstance(live, dict) else {}
            machine_oee = oee_by_id.get(equipment_id, {})
            rows.append(
                {
                    "equipment_id": equipment_id,
                    "line": "Live feed",
                    "cell": equipment_id[-2:] if len(equipment_id) >= 2 else "",
                    "type": live.get("meta", {}).get("type", ""),
                    "process": "",
                    "model": metrics.get("mold_model", metrics.get("model", "")),
                    "protocol": "simulator",
                    "cycle_time": metrics.get("cycle_time"),
                    "oee": machine_oee.get("oee"),
                    "availability": machine_oee.get("availability"),
                    "performance": machine_oee.get("performance"),
                    "quality": machine_oee.get("quality"),
                    "state": "Live",
                }
            )
    return pd.DataFrame(rows)


def make_oee_bar(df):
    chart_df = df.dropna(subset=["oee"]).sort_values("oee", ascending=True).head(14)
    if chart_df.empty:
        return None
    colors = [
        "#c2412d" if value < 75 else "#b7791f" if value < 85 else "#0c8f6d"
        for value in chart_df["oee"]
    ]
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=chart_df["oee"],
            y=chart_df["equipment_id"],
            orientation="h",
            marker=dict(color=colors),
            text=[f"{value:.1f}%" for value in chart_df["oee"]],
            textposition="auto",
            hovertemplate="%{y}<br>OEE %{x:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        height=390,
        margin=dict(l=6, r=12, t=10, b=16),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(range=[0, 100], gridcolor="#edf1f5", title=""),
        yaxis=dict(title=""),
        font=dict(color="#111827"),
    )
    return fig


def make_component_radar(oee):
    if not oee:
        return None
    values = {
        "Availability": sum(item.get("availability", 0) for item in oee) / len(oee),
        "Performance": sum(item.get("performance", 0) for item in oee) / len(oee),
        "Quality": sum(item.get("quality", 0) for item in oee) / len(oee),
    }
    fig = go.Figure()
    fig.add_trace(
        go.Scatterpolar(
            r=list(values.values()) + [list(values.values())[0]],
            theta=list(values.keys()) + [list(values.keys())[0]],
            fill="toself",
            line=dict(color="#2563eb", width=2),
            fillcolor="rgba(37, 99, 235, .16)",
            hovertemplate="%{theta}: %{r:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        height=300,
        margin=dict(l=16, r=16, t=10, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        polar=dict(
            bgcolor="rgba(0,0,0,0)",
            radialaxis=dict(range=[0, 100], gridcolor="#edf1f5", tickfont=dict(size=10)),
            angularaxis=dict(gridcolor="#edf1f5"),
        ),
        showlegend=False,
        font=dict(color="#111827"),
    )
    return fig


def make_loss_tree(oee):
    if not oee:
        return None
    loss = {
        "Downtime minutes": sum(item.get("loss_tree", {}).get("downtime_minutes", 0) for item in oee),
        "Performance loss %": sum(item.get("loss_tree", {}).get("performance_loss_percent", 0) for item in oee) / len(oee),
        "Quality loss %": sum(item.get("loss_tree", {}).get("quality_loss_percent", 0) for item in oee) / len(oee),
    }
    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=list(loss.values()),
            y=list(loss.keys()),
            orientation="h",
            marker_color=["#c2412d", "#b7791f", "#2563eb"],
            text=[f"{value:.1f}" for value in loss.values()],
            textposition="auto",
            hovertemplate="%{y}: %{x:.1f}<extra></extra>",
        )
    )
    fig.update_layout(
        height=260,
        margin=dict(l=4, r=8, t=4, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#edf1f5", title=""),
        yaxis=dict(title=""),
        font=dict(color="#111827"),
    )
    return fig


def make_shift_trend(avg_oee):
    now = datetime.now().replace(minute=0, second=0, microsecond=0)
    base = avg_oee or 82
    points = []
    for index in range(12):
        drift = ((index % 5) - 2) * 1.4
        points.append(
            {
                "time": now - timedelta(hours=11 - index),
                "oee": max(58, min(96, base + drift - (2 if index in {3, 7} else 0))),
                "target": 85,
            }
        )
    trend = pd.DataFrame(points)
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=trend["time"],
            y=trend["oee"],
            mode="lines+markers",
            line=dict(color="#0c8f6d", width=3),
            marker=dict(size=6),
            name="OEE",
            hovertemplate="%{x|%H:%M}<br>OEE %{y:.1f}%<extra></extra>",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=trend["time"],
            y=trend["target"],
            mode="lines",
            line=dict(color="#b7791f", width=2, dash="dash"),
            name="Target",
            hovertemplate="Target %{y:.1f}%<extra></extra>",
        )
    )
    fig.update_layout(
        height=270,
        margin=dict(l=8, r=10, t=6, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(gridcolor="#edf1f5", title=""),
        yaxis=dict(range=[50, 100], gridcolor="#edf1f5", title=""),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, x=0),
        font=dict(color="#111827"),
    )
    return fig


def render_section_header(title, note=""):
    st.markdown(
        f"""
        <div class="section-header">
            <div class="section-title">{esc(title)}</div>
            <div class="section-note">{esc(note)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_andon_grid(df):
    if df.empty:
        st.markdown('<div class="empty-state">No machine data is available yet.</div>', unsafe_allow_html=True)
        return
    cell_df = df.copy()
    cell_df["cell_index"] = cell_df["cell"].astype(str).str.extract(r"(\d+)", expand=False).fillna("0").astype(int)
    html_tiles = []
    for cell, group in cell_df.sort_values(["cell_index", "equipment_id"]).groupby("cell"):
        group_oee = group["oee"].dropna()
        avg = group_oee.mean() if not group_oee.empty else None
        if avg is None:
            state = "watch"
            label = "waiting"
            display = "No OEE"
        elif avg < 75:
            state = "critical"
            label = "critical"
            display = f"{avg:.1f}% OEE"
        elif avg < 85:
            state = "watch"
            label = "watch"
            display = f"{avg:.1f}% OEE"
        else:
            state = "stable"
            label = "stable"
            display = f"{avg:.1f}% OEE"
        imm_count = len(group[group["type"].str.contains("IMM", na=False)])
        aux_count = max(len(group) - imm_count, 0)
        top_assets = ", ".join(group["equipment_id"].head(4).astype(str).tolist())
        html_tiles.append(
            f"""
            <div class="andon-tile {state}">
                <div class="andon-title">
                    <span>{esc(cell)}</span>
                    <span class="badge badge-{state}">{esc(label)}</span>
                </div>
                <div class="andon-meta">
                    <strong>{esc(display)}</strong><br>
                    {imm_count} molding asset, {aux_count} auxiliaries<br>
                    {esc(top_assets)}
                </div>
            </div>
            """
        )
    st.markdown(f'<div class="andon-grid">{"".join(html_tiles)}</div>', unsafe_allow_html=True)


def render_priority_table(df):
    if df.empty or "oee" not in df:
        st.markdown('<div class="empty-state">No priority list is available.</div>', unsafe_allow_html=True)
        return
    priority = df.dropna(subset=["oee"]).sort_values("oee", ascending=True).head(6)
    rows = []
    for _, item in priority.iterrows():
        state = "critical" if item["oee"] < 75 else "watch" if item["oee"] < 85 else "stable"
        rows.append(
            f"""
            <tr>
                <td><strong>{esc(item["equipment_id"])}</strong></td>
                <td>{esc(item["line"])}</td>
                <td>{esc(item["process"])}</td>
                <td>{item["oee"]:.1f}%</td>
                <td><span class="badge badge-{state}">{esc(state)}</span></td>
            </tr>
            """
        )
    st.markdown(
        f"""
        <table class="mini-table">
            <thead>
                <tr><th>Machine</th><th>Line</th><th>Process</th><th>OEE</th><th>Status</th></tr>
            </thead>
            <tbody>{"".join(rows)}</tbody>
        </table>
        """,
        unsafe_allow_html=True,
    )


if not auth.check_auth():
    auth.render_login_page()
    st.stop()

inject_css()
user = st.session_state.get("user") or {"username": "demo", "role": "operator"}
role = user.get("role", "operator")

with st.sidebar:
    st.markdown("## ⬡ Acron")
    st.caption("Intelligence meets reality.")
    st.caption("S7 Corp")
    st.divider()
    st.write(f"Signed in as **{user.get('username', 'demo')}**")
    st.caption(f"Role: {role}")
    st.progress(min(1.0, (st.session_state.get("expires_in", 1800) or 1800) / 1800), text="Session active")
    if st.button("Sign out", width="stretch"):
        auth.logout()
    st.divider()
    if role in {"admin", "manager"}:
        if st.button("Reset demo data", width="stretch"):
            try:
                api_post("/api/v1/demo/reset")
                st.success("Demo data reset.")
                st.rerun()
            except Exception as exc:
                st.error(f"Reset failed: {exc}")
    if st.button("Refresh", width="stretch"):
        st.rerun()
    st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

health, health_error = api_get("/api/v1/health", {"status": "degraded", "checks": {}})
machines, machines_error = api_get("/api/v1/telemetry/latest", {})
oee, oee_error = api_get("/api/v1/oee", [])
machine_master, master_error = api_get("/api/v1/factory/machines", [])
reasons, reasons_error = api_get("/api/v1/downtime/reasons", [])
connectors, connectors_error = api_get("/api/v1/connectors", [])

machine_df = build_machine_frame(machine_master, machines, oee)
avg_oee = machine_df["oee"].dropna().mean() if not machine_df.empty else 0
stable_assets = len(machine_df[machine_df["state"] == "Stable"]) if not machine_df.empty else 0
watch_assets = len(machine_df[machine_df["state"] == "Watch"]) if not machine_df.empty else 0
critical_assets = len(machine_df[machine_df["state"] == "Critical"]) if not machine_df.empty else 0
live_assets = len(machines)
total_assets = len(machine_df)
best_machine = ""
if not machine_df.empty and machine_df["oee"].notna().any():
    best_machine = machine_df.sort_values("oee", ascending=False).iloc[0]["equipment_id"]

checks = health.get("checks", {})
status_html = "".join(
    [
        health_pill("API", checks.get("api", {}).get("status", "unknown")),
        health_pill("Database", checks.get("database", {}).get("status", "unknown")),
        health_pill("Dashboard", checks.get("dashboard", {}).get("status", "unknown")),
        health_pill("Simulator", checks.get("simulator", {}).get("status", "unknown")),
    ]
)

st.markdown(
    f"""
    <div class="topbar">
        <div class="brand-lockup">
            <div class="brand-mark">⬡</div>
            <div>
                <div class="brand-title">Acron</div>
                <div class="brand-subtitle">S7 Corp / Intelligence meets reality.</div>
            </div>
        </div>
        <div class="status-strip">{status_html}</div>
    </div>
    """,
    unsafe_allow_html=True,
)

if any([health_error, machines_error, oee_error, master_error]):
    with st.expander("System messages", expanded=health.get("status") != "healthy"):
        for label, error in [
            ("Health", health_error),
            ("Telemetry", machines_error),
            ("OEE", oee_error),
            ("Machine master", master_error),
        ]:
            if error:
                st.warning(f"{label}: {error}")

kpi_1, kpi_2, kpi_3, kpi_4, kpi_5 = st.columns(5)
kpi_1.metric("Average OEE", f"{avg_oee:.1f}%" if avg_oee else "Waiting", delta=f"{avg_oee - 85:.1f} vs target" if avg_oee else None)
kpi_2.metric("Live assets", f"{live_assets}/{total_assets}" if total_assets else live_assets)
kpi_3.metric("Stable cells", stable_assets)
kpi_4.metric("Watch list", watch_assets)
kpi_5.metric("Critical assets", critical_assets, delta=best_machine or None, delta_color="off")

overview_tab, andon_tab, losses_tab, machines_tab, admin_tab = st.tabs(
    ["Command", "Andon", "Losses", "Machines", "Admin"]
)

with overview_tab:
    left, right = st.columns([1.45, 1])
    with left:
        render_section_header("OEE control chart", "Lowest performing machines first")
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        fig = make_oee_bar(machine_df)
        if fig:
            st.plotly_chart(fig, width="stretch")
        else:
            st.markdown('<div class="empty-state">OEE will appear when telemetry starts flowing.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    with right:
        render_section_header("Priority board", "Where the next shift action should focus")
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        render_priority_table(machine_df)
        st.markdown("</div>", unsafe_allow_html=True)

    lower_left, lower_right = st.columns([1, 1])
    with lower_left:
        render_section_header("Shift trend", "Target line at 85% OEE")
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        st.plotly_chart(make_shift_trend(avg_oee), width="stretch")
        st.markdown("</div>", unsafe_allow_html=True)
    with lower_right:
        render_section_header("Role workspace", f"{role.title()} mode")
        actions = {
            "operator": [
                ("Capture downtime", "Log the stop reason while the event is still fresh."),
                ("Check cell status", "Watch cycle time, auxiliaries, and current shift health."),
                ("Escalate issue", "Flag repeated stops before they become shift losses."),
                ("Confirm restart", "Record recovery after maintenance or material action."),
            ],
            "supervisor": [
                ("Clear Andon queue", "Acknowledge stops and assign ownership."),
                ("Protect target", "Compare target, cycle time, and live OEE."),
                ("Shift handover", "Review losses before the next team takes over."),
                ("Coach reason codes", "Fix vague downtime entries before reporting."),
            ],
            "maintenance": [
                ("MTTR focus", "Prioritize repeated critical stops and temperature drift."),
                ("Connector health", "Check PLC and gateway status before troubleshooting."),
                ("Resolve event", "Close maintenance downtime with repair notes."),
                ("Prevent repeat", "Use loss tree and recent stops to schedule action."),
            ],
            "manager": [
                ("Line review", "Scan OEE, availability, performance, and quality together."),
                ("Top losses", "Challenge the largest loss buckets first."),
                ("Demo reset", "Restore clean data for customer or investor walkthroughs."),
                ("Daily report", "Use this as the operating snapshot for production review."),
            ],
            "admin": [
                ("Machine setup", "Maintain plant, line, cell, process, and connector data."),
                ("Role access", "Use role-specific sessions to validate screens."),
                ("Reset demo", "Restore sample factory data before a walkthrough."),
                ("Deployment health", "Confirm API, database, dashboard, and simulator status."),
            ],
        }
        html_actions = "".join(
            f"""
            <div class="action-tile">
                <div class="action-title">{esc(title)}</div>
                <div class="action-copy">{esc(copy)}</div>
            </div>
            """
            for title, copy in actions.get(role, actions["operator"])
        )
        st.markdown(f'<div class="action-row">{html_actions}</div>', unsafe_allow_html=True)

with andon_tab:
    render_section_header("Live Andon board", "Grouped by production cell")
    render_andon_grid(machine_df)

    st.divider()
    form_col, reason_col = st.columns([1, 1.1])
    with form_col:
        render_section_header("Capture downtime", "Operator-grade reason entry")
        if machine_df.empty:
            st.info("Machine master is not available.")
        else:
            with st.form("downtime_form", clear_on_submit=True):
                equipment_id = st.selectbox("Machine", machine_df["equipment_id"].dropna().unique())
                reason_labels = [reason.get("label", reason.get("code", "")) for reason in reasons] or [
                    "Machine stop",
                    "Material shortage",
                    "Quality issue",
                    "Changeover",
                    "Maintenance",
                ]
                reason_label = st.selectbox("Reason", reason_labels)
                minutes = st.number_input("Minutes", min_value=1.0, max_value=480.0, value=10.0, step=1.0)
                comment = st.text_area("Comment", placeholder="Short production note")
                submitted = st.form_submit_button("Log downtime", width="stretch")
                if submitted:
                    selected = next((item for item in reasons if item.get("label") == reason_label), {})
                    try:
                        api_post(
                            "/api/v1/downtime",
                            {
                                "equipment_id": equipment_id,
                                "reason_code": selected.get("code", reason_label.upper().replace(" ", "_")),
                                "category": selected.get("category", reason_label.lower()),
                                "minutes": minutes,
                                "comment": comment,
                            },
                        )
                        st.success("Downtime logged.")
                    except Exception as exc:
                        st.error(f"Downtime could not be logged: {exc}")
    with reason_col:
        render_section_header("Reason codes", "Standard loss taxonomy")
        if reasons:
            st.dataframe(pd.DataFrame(reasons), width="stretch", hide_index=True)
        elif reasons_error:
            st.warning(f"Reason codes unavailable: {reasons_error}")
        else:
            st.info("No reason codes are configured.")

with losses_tab:
    c1, c2 = st.columns([1, 1])
    with c1:
        render_section_header("OEE components", "Availability / Performance / Quality")
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        radar = make_component_radar(oee)
        if radar:
            st.plotly_chart(radar, width="stretch")
        else:
            st.markdown('<div class="empty-state">Component scores are waiting for OEE data.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)
    with c2:
        render_section_header("Loss tree", "Downtime and hidden performance loss")
        st.markdown('<div class="panel">', unsafe_allow_html=True)
        loss_tree = make_loss_tree(oee)
        if loss_tree:
            st.plotly_chart(loss_tree, width="stretch")
        else:
            st.markdown('<div class="empty-state">Loss data will appear after shift events are recorded.</div>', unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    render_section_header("Loss by machine", "Sorted by OEE risk")
    if not machine_df.empty:
        loss_df = machine_df[["equipment_id", "line", "cell", "process", "oee", "availability", "performance", "quality", "state"]].copy()
        st.dataframe(
            loss_df.sort_values("oee", na_position="last"),
            width="stretch",
            hide_index=True,
            column_config={
                "oee": st.column_config.ProgressColumn("OEE", format="%.1f%%", min_value=0, max_value=100),
                "availability": st.column_config.ProgressColumn("Availability", format="%.1f%%", min_value=0, max_value=100),
                "performance": st.column_config.ProgressColumn("Performance", format="%.1f%%", min_value=0, max_value=100),
                "quality": st.column_config.ProgressColumn("Quality", format="%.1f%%", min_value=0, max_value=100),
            },
        )

with machines_tab:
    render_section_header("Machine master", "Plant / line / cell / machine / process / model")
    if machine_df.empty:
        st.markdown('<div class="empty-state">No machine master data is configured yet.</div>', unsafe_allow_html=True)
    else:
        filters = st.columns([1, 1, 1, 1])
        with filters[0]:
            line_filter = st.multiselect("Line", sorted(machine_df["line"].dropna().unique()))
        with filters[1]:
            cell_filter = st.multiselect("Cell", sorted(machine_df["cell"].dropna().unique()))
        with filters[2]:
            process_filter = st.multiselect("Process", sorted(machine_df["process"].dropna().unique()))
        with filters[3]:
            state_filter = st.multiselect("State", sorted(machine_df["state"].dropna().unique()))

        filtered = machine_df.copy()
        if line_filter:
            filtered = filtered[filtered["line"].isin(line_filter)]
        if cell_filter:
            filtered = filtered[filtered["cell"].isin(cell_filter)]
        if process_filter:
            filtered = filtered[filtered["process"].isin(process_filter)]
        if state_filter:
            filtered = filtered[filtered["state"].isin(state_filter)]

        st.dataframe(
            filtered.sort_values(["line", "cell", "equipment_id"]),
            width="stretch",
            hide_index=True,
            column_config={
                "oee": st.column_config.ProgressColumn("OEE", format="%.1f%%", min_value=0, max_value=100),
                "cycle_time": st.column_config.NumberColumn("Cycle time", format="%.1f s"),
            },
        )

with admin_tab:
    render_section_header("Platform readiness", "Deployment, connectors, and demo operations")
    admin_cols = st.columns([1, 1])
    with admin_cols[0]:
        st.subheader("Health checks")
        health_rows = []
        for name, check in checks.items():
            health_rows.append({"service": name, "status": check.get("status", "unknown")})
        st.dataframe(pd.DataFrame(health_rows), width="stretch", hide_index=True)

        if role in {"admin", "manager"}:
            if st.button("Reset sample factory data", width="stretch"):
                try:
                    api_post("/api/v1/demo/reset")
                    st.success("Sample factory data reset.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"Reset failed: {exc}")
        else:
            st.info("Demo reset is available to manager and admin roles.")

    with admin_cols[1]:
        st.subheader("Connector paths")
        if connectors:
            st.dataframe(pd.DataFrame(connectors), width="stretch", hide_index=True)
        elif connectors_error:
            st.warning(f"Connectors unavailable: {connectors_error}")
        else:
            st.info("No connector configs are active.")

