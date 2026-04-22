"""
GE Pulse dashboard home.
"""
import os
from datetime import datetime

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st

import auth

API_URL = os.getenv("API_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(
    page_title="GE Pulse | S7 Inc",
    page_icon="GP",
    layout="wide",
    initial_sidebar_state="expanded",
)


def api_get(path, default):
    try:
        response = requests.get(f"{API_URL}{path}", timeout=5)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return default


def api_post(path, payload=None):
    headers = {}
    if st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    response = requests.post(f"{API_URL}{path}", json=payload or {}, headers=headers, timeout=10)
    response.raise_for_status()
    return response.json()


if not auth.check_auth():
    auth.render_login_page()
    st.stop()

user = st.session_state.get("user") or {"username": "demo", "role": "operator"}

st.markdown(
    """
    <style>
    .block-container {padding-top: 1.4rem;}
    [data-testid="stSidebar"] {background: #121722;}
    .brand-kicker {color: #55d6be; font-weight: 700; letter-spacing: .04em;}
    .soft-note {color: #8a94a7;}
    .health-ok {color: #42d392; font-weight: 700;}
    .health-warn {color: #ffb020; font-weight: 700;}
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown("## GE Pulse")
    st.caption("Factory rhythm, clear.")
    st.caption("S7 Inc")
    st.divider()
    st.write(f"Signed in as **{user['username']}**")
    st.caption(f"Role: {user['role']}")
    if st.button("Sign out", use_container_width=True):
        auth.logout()
    st.divider()
    if user.get("role") in {"admin", "manager"}:
        if st.button("Reset demo data", use_container_width=True):
            try:
                api_post("/api/v1/demo/reset")
                st.success("Demo data reset.")
                st.rerun()
            except Exception as exc:
                st.error(f"Reset failed: {exc}")
    if st.button("Refresh", use_container_width=True):
        st.rerun()
    st.caption(f"Last refresh: {datetime.now().strftime('%H:%M:%S')}")

health = api_get("/api/v1/health", {"status": "degraded", "checks": {}})
machines = api_get("/api/v1/telemetry/latest", {})
oee = api_get("/api/v1/oee", [])
machine_master = api_get("/api/v1/factory/machines", [])

st.markdown('<div class="brand-kicker">S7 INC SHOP-FLOOR INTELLIGENCE</div>', unsafe_allow_html=True)
st.title("GE Pulse")
st.caption("Real-time OEE, Andon readiness, downtime capture, and machine telemetry for injection molding and automotive components.")

if health.get("status") != "healthy":
    st.warning("The demo is running in degraded mode. API is reachable, but one or more services need attention.")

total_assets = len(machine_master) or len(machines)
active_assets = len(machines)
avg_oee = sum(item["oee"] for item in oee) / len(oee) if oee else 0
critical_assets = sum(1 for item in oee if item["oee"] < 75)

k1, k2, k3, k4 = st.columns(4)
k1.metric("Configured assets", total_assets)
k2.metric("Live assets", active_assets)
k3.metric("Average OEE", f"{avg_oee:.1f}%" if avg_oee else "Waiting")
k4.metric("Assets below 75% OEE", critical_assets)

st.divider()

health_cols = st.columns(4)
for idx, check_name in enumerate(["api", "database", "dashboard", "simulator"]):
    check = health.get("checks", {}).get(check_name, {})
    status = check.get("status", "unknown")
    with health_cols[idx]:
        st.subheader(check_name.title())
        if status in {"up", "connected", "ready", "running"}:
            st.markdown(f'<span class="health-ok">{status}</span>', unsafe_allow_html=True)
        else:
            st.markdown(f'<span class="health-warn">{status}</span>', unsafe_allow_html=True)

st.divider()

left, right = st.columns([1.3, 1])

with left:
    st.subheader("OEE by machine")
    if oee:
        oee_df = pd.DataFrame(oee).sort_values("oee", ascending=True).head(12)
        fig = go.Figure()
        fig.add_trace(go.Bar(
            x=oee_df["oee"],
            y=oee_df["equipment_id"],
            orientation="h",
            marker_color=["#ef4444" if value < 75 else "#22c55e" for value in oee_df["oee"]],
            text=[f"{value:.1f}%" for value in oee_df["oee"]],
            textposition="auto",
        ))
        fig.update_layout(height=420, margin=dict(l=8, r=8, t=8, b=8), xaxis_range=[0, 100])
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("OEE will appear after telemetry starts flowing.")

with right:
    st.subheader("Role workspace")
    role = user.get("role", "operator")
    role_copy = {
        "operator": "Capture downtime reasons, watch cell status, and keep the shift record clean.",
        "supervisor": "Track OEE losses, acknowledge Andon events, and coordinate shift recovery.",
        "maintenance": "Prioritize repeat stops, high vibration, temperature drift, and MTTR risks.",
        "manager": "Review line performance, top losses, escalation status, and daily production health.",
        "admin": "Configure machines, connectors, demo data, users, and deployment health.",
    }
    st.write(role_copy.get(role, role_copy["operator"]))
    st.subheader("Downtime reasons")
    reasons = api_get("/api/v1/downtime/reasons", [])
    st.dataframe(pd.DataFrame(reasons), use_container_width=True, hide_index=True)

st.divider()

st.subheader("Machine master")
if machine_master:
    st.dataframe(pd.DataFrame(machine_master), use_container_width=True, hide_index=True)
else:
    st.info("No machine master data is configured yet. Use the API or reset demo data to seed the sample plant.")
