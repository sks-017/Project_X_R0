"""
Production Control System - Enhanced Home Page
Multi-page Streamlit application with animated KPIs and activity feed
"""
import streamlit as st
import sys
from pathlib import Path
import random
from datetime import datetime, timedelta
import plotly.graph_objects as go
sys.path.insert(0, str(Path(__file__).parent))
from utils.alerts import AlertSystem
st.set_page_config(
    page_title="Production Control System",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)
import auth
if not auth.check_auth():
    auth.render_login_page()
    st.stop()
st.markdown("""
<style>
    .kpi-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        border-radius: 10px;
        padding: 20px;
        border-left: 5px solid;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.3s ease;
    }
    .kpi-card:hover {
        transform: translateY(-5px);
    }
    .activity-item {
        background: #2d2d2d;
        border-left: 3px solid;
        padding: 10px 15px;
        margin: 8px 0;
        border-radius: 5px;
        animation: slideIn 0.5s ease-out;
    }
    @keyframes slideIn {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }
    .pulse {
        animation: pulse 2s infinite;
    }
    @keyframes pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
    }
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
    }
    .badge-success { background: #00FF9F; color: #000; }
    .badge-warning { background: #FFA500; color: #000; }
    .badge-error { background: #FF4444; color: #fff; }
</style>
""", unsafe_allow_html=True)
if 'alert_config' not in st.session_state:
    st.session_state.alert_config = {
        'cycle_time_threshold': 10.0,
        'temp_min': 180,
        'temp_max': 220
    }
alert_system = AlertSystem()
with st.sidebar:
    try:
        # Premium logo styling
        st.markdown("""
        <style>
            .logo-container {
                padding: 20px 10px;
                background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
                border-radius: 12px;
                box-shadow: 0 4px 12px rgba(0,0,0,0.3);
                margin-bottom: 20px;
                text-align: center;
            }
            .logo-container img {
                max-width: 85%;
                height: auto;
                filter: drop-shadow(0 2px 8px rgba(0,0,0,0.4));
            }
        </style>
        """, unsafe_allow_html=True)
        
        # Display logo with premium container
        import base64
        with open("assets/logo.png", "rb") as f:
            img_data = base64.b64encode(f.read()).decode()
        
        st.markdown(f"""
        <div class="logo-container">
            <img src="data:image/png;base64,{img_data}" alt="s7 Inc. Logo">
        </div>
        """, unsafe_allow_html=True)
    except Exception as e:
        st.title("🏭 Production Control")
    st.markdown("---")
    if st.session_state.get('user'):
        with st.expander(f"👤 {st.session_state.user['username']}", expanded=True):
            st.caption(f"Role: {st.session_state.user['role'].upper()}")
            if st.button("Sign Out", use_container_width=True):
                auth.logout()
    st.markdown("### ⚙️ Settings")
    refresh_interval = st.selectbox(
        "Auto-Refresh",
        options=[5, 10, 30, 60, 0],
        index=0,
        format_func=lambda x: "⏸️ Paused" if x == 0 else f"⏱️ {x}s",
        key='refresh_interval'
    )
    # TODO: Optimize this refresh logic. Currently re-renders the whole page.
    # Should switch to WebSocket for partial updates in v2.0 to reduce server load.
    with st.expander("🔔 Alert Thresholds"):
        st.session_state.alert_config['cycle_time_threshold'] = st.slider(
            "Cycle Time Deviation (%)", 5.0, 20.0, 10.0, 1.0
        )
        st.session_state.alert_config['temp_min'] = st.number_input(
            "Min Zone Temp (°C)", value=180, step=5
        )
        st.session_state.alert_config['temp_max'] = st.number_input(
            "Max Zone Temp (°C)", value=220, step=5
        )
    st.markdown("### 🟢 System Status")
    st.markdown("""
    <div style="background: #1e1e1e; padding: 10px; border-radius: 5px; border: 1px solid #333;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="color: #888;">Gateway</span>
            <span style="color: #00FF9F;">● Online</span>
        </div>
        <div style="display: flex; justify-content: space-between; margin-bottom: 5px;">
            <span style="color: #888;">Database</span>
            <span style="color: #00FF9F;">● Connected</span>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #888;">API Latency</span>
            <span style="color: #00D9FF;">12ms</span>
        </div>
    </div>
    """, unsafe_allow_html=True)
alert_system.render_alert_panel()
st.title("🏭 Production Control System")
st.markdown("### Welcome to the Injection Molding and Bumper Shop Control Center")
st.markdown("---")
col1, col2, col3, col4 = st.columns(4)
with col1:
    st.markdown("""
    <div class="kpi-card pulse" style="border-left-color: #00FF9F;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <p style="color: #888; margin: 0; font-size: 14px;">Active Machines</p>
                <h1 style="margin: 5px 0; color: #00FF9F;">29</h1>
                <p style="color: #00FF9F; margin: 0; font-size: 12px;">▲ 100% Uptime</p>
            </div>
            <div style="font-size: 48px;">✅</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="kpi-card" style="border-left-color: #00D9FF;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <p style="color: #888; margin: 0; font-size: 14px;">Current OEE</p>
                <h1 style="margin: 5px 0; color: #00D9FF;">87.5%</h1>
                <p style="color: #00FF9F; margin: 0; font-size: 12px;">▲ +2.1% vs target</p>
            </div>
            <div style="font-size: 48px;">⚡</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="kpi-card" style="border-left-color: #FF6B00;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <p style="color: #888; margin: 0; font-size: 14px;">Parts/Hour</p>
                <h1 style="margin: 5px 0; color: #FF6B00;">228</h1>
                <p style="color: #FFA500; margin: 0; font-size: 12px;">▼ -12 vs target (240)</p>
            </div>
            <div style="font-size: 48px;">📦</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col4:
    st.markdown("""
    <div class="kpi-card" style="border-left-color: #FFA500;">
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <div>
                <p style="color: #888; margin: 0; font-size: 14px;">Current Shift</p>
                <h1 style="margin: 5px 0; color: #FFA500;">B</h1>
                <p style="color: #888; margin: 0; font-size: 12px;">Ends in 4h 32m</p>
            </div>
            <div style="font-size: 48px;">👨‍🏭</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("---")
col_left, col_right = st.columns([2, 1])
with col_left:
    st.subheader("📋 Quick Navigation")
    nav_cols = st.columns(3)
    with nav_cols[0]:
        st.info("""
        **📊 Executive Summary**
        - Production trends
        - OEE breakdown
        - Machine status
        - Downtime analysis
        """)
        st.success("""
        **🏭 Shop Floor (Cells)**
        - 8 Production cells
        - Real-time metrics
        - Zone temperatures
        - Equipment status
        """)
    with nav_cols[1]:
        st.warning("""
        **👨‍🏭 Shift Analysis**
        - Shift comparison  
        - Handover reports
        - Shift-based KPIs
        - Performance trends
        """)
        st.error("""
        **🎯 Quality Dashboard**
        - Defect tracking
        - First Pass Yield
        - Pareto analysis
        - Quality trends
        """)
    with nav_cols[2]:
        st.info("""
        **⚡ Energy Monitoring**
        - Power consumption
        - Cost analysis
        - Efficiency metrics
        - Carbon footprint
        """)
        st.success("""
        **🧵 Invisible Airbag Facility**
        - Assembly equipment
        - Cutting machines
        - Welding stations
        """)
with col_right:
    st.subheader("🔔 Live Activity Feed")
    filter_type = st.multiselect(
        "Filter by Type",
        ["Success", "Warning", "Error"],
        default=["Success", "Warning", "Error"],
        label_visibility="collapsed"
    )
    all_activities = [
        {"time": "2 min ago", "type": "Success", "msg": "IMM-03 completed 100 parts", "icon": "✅"},
        {"time": "5 min ago", "type": "Warning", "msg": "Zone 12 temp at 219°C", "icon": "⚠️"},
        {"time": "8 min ago", "type": "Success", "msg": "Shift B started", "icon": "👨‍🏭"},
        {"time": "12 min ago", "type": "Success", "msg": "Quality check passed (FPY: 98.2%)", "icon": "🎯"},
        {"time": "15 min ago", "type": "Error", "msg": "TCM-01 maintenance alert", "icon": "🔧"},
        {"time": "18 min ago", "type": "Success", "msg": "Model AB-X100: 500 parts milestone", "icon": "🏆"},
    ]
    activities = [a for a in all_activities if a['type'] in filter_type]
    for activity in activities:
        color = {"Success": "#00FF9F", "Warning": "#FFA500", "Error": "#FF4444"}[activity['type']]
        st.markdown(f"""
        <div class="activity-item" style="border-left-color: {color};">
            <span style="font-size: 20px;">{activity['icon']}</span>
            <strong style="margin-left: 8px;">{activity['msg']}</strong>
            <p style="color: #888; font-size: 12px; margin: 5px 0 0 28px;">{activity['time']}</p>
        </div>
        """, unsafe_allow_html=True)
st.markdown("---")
st.subheader("🔧 System Health")
health_cols = st.columns(4)
with health_cols[0]:
    fig_api = go.Figure(go.Indicator(
        mode="gauge+number",
        value=100,
        title={'text': "API Connection"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#00FF9F"},
            'steps': [
                {'range': [0, 50], 'color': "#FF4444"},
                {'range': [50, 80], 'color': "#FFA500"},
                {'range': [80, 100], 'color': "#00FF9F"}
            ],
            'threshold': {
                'line': {'color': "white", 'width': 4},
                'thickness': 0.75,
                'value': 95
            }
        }
    ))
    fig_api.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig_api, use_container_width=True)
with health_cols[1]:
    fig_uptime = go.Figure(go.Indicator(
        mode="gauge+number",
        value=99.8,
        title={'text': "System Uptime %"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#00D9FF"},
            'steps': [
                {'range': [0, 90], 'color': "#FF4444"},
                {'range': [90, 95], 'color': "#FFA500"},
                {'range': [95, 100], 'color': "#00FF9F"}
            ]
        }
    ))
    fig_uptime.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig_uptime, use_container_width=True)
with health_cols[2]:
    active_alerts = len(alert_system.get_active_alerts())
    alert_percentage = max(0, 100 - (active_alerts * 10))
    fig_alerts = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=active_alerts,
        title={'text': "Active Alerts"},
        delta={'reference': 0},
        gauge={
            'axis': {'range': [0, 10]},
            'bar': {'color': "#FF6B00"},
            'steps': [
                {'range': [0, 3], 'color': "#00FF9F"},
                {'range': [3, 6], 'color': "#FFA500"},
                {'range': [6, 10], 'color': "#FF4444"}
            ]
        }
    ))
    fig_alerts.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig_alerts, use_container_width=True)
with health_cols[3]:
    fig_perf = go.Figure(go.Indicator(
        mode="gauge+number",
        value=92.5,
        title={'text': "Performance Score"},
        gauge={
            'axis': {'range': [0, 100]},
            'bar': {'color': "#FFD700"},
            'steps': [
                {'range': [0, 60], 'color': "#FF4444"},
                {'range': [60, 85], 'color': "#FFA500"},
                {'range': [85, 100], 'color': "#00FF9F"}
            ]
        }
    ))
    fig_perf.update_layout(height=200, margin=dict(l=10, r=10, t=50, b=10), paper_bgcolor='rgba(0,0,0,0)', plot_bgcolor='rgba(0,0,0,0)', font=dict(color='white'))
    st.plotly_chart(fig_perf, use_container_width=True)
st.markdown("---")
st.caption("💡 Use the sidebar to navigate between dashboards. Auto-refresh enabled for real-time updates.")
