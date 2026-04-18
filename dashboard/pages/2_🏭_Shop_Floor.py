"""Shop Floor Dashboard - Production Control System"""
import streamlit as st
import requests
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.alerts import AlertSystem
from utils.data_export import export_to_csv, export_machine_data
st.set_page_config(page_title="Shop Floor", page_icon="🏭", layout="wide")
import auth
if not auth.check_auth():
    st.warning("Please login from the Home page first.")
    st.stop()
st.markdown("""
<style>
    .status-badge {
        display: inline-block;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 12px;
        font-weight: bold;
        margin: 5px 5px 5px 0;
    }
    .badge-running { background: #00FF9F; color: #000; }
    .badge-idle { background: #FFA500; color: #000; }
    .badge-alert { background: #FF4444; color: #fff; }
    .machine-card {
        border-radius: 8px;
        padding: 15px;
        background: linear-gradient(135deg, #1e1e1e 0%, #2a2a2a 100%);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        transition: transform 0.2s;
    }
    .machine-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 6px 12px rgba(0,0,0,0.4);
    }
    .metric-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin: 8px 0;
        padding: 5px 0;
        border-bottom: 1px solid #333;
    }
    .metric-label {
        color: #888;
        font-size: 13px;
    }
    .metric-value {
        color: #fff;
        font-weight: bold;
        font-size: 14px;
    }
</style>
""", unsafe_allow_html=True)
API_URL = "http://localhost:8000/api/v1/telemetry/latest"
@st.cache_data(ttl=2)
def fetch_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}
machines = fetch_data()
alert_system = AlertSystem()
st.title("🏭 Injection Molding and Bumper Shop A & B Line")
if machines:
    export_df = export_machine_data(machines)
    export_to_csv(export_df, "shop_floor_data")
all_alerts = []
for dev_id, data in machines.items():
    metrics = data.get('metrics', {})
    alerts = alert_system.check_machine(dev_id, metrics)
    all_alerts.extend(alerts)
if all_alerts:
    alert_system.add_alerts(all_alerts)
def render_card(title, metrics, color="green", extra_html="", dev_id=""):
    has_cycle = metrics.get('cycle_time', 0) > 0
    status = "running" if has_cycle else "idle"
    status_badge = f'<span class="status-badge badge-{status}">{"✅ RUNNING" if status == "running" else "⏸️ IDLE"}</span>'
    st.markdown(f"""
    <div class="machine-card" style="border: 1px solid {color}; border-left: 5px solid {color};">
        <div style="display: flex; justify-content: space-between; align-items: center;">
            <h5 style="margin:0;">{title}</h5>
            {status_badge}
        </div>
        <div style="font-size: 0.85em; margin-top: 10px;">
            {extra_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
for i in range(1, 9):
    cell_id = f"{i:02d}"
    imm_id = f"IMM-{cell_id}"
    qmc_id = f"QMC-{cell_id}"
    chiller_id = f"CHILLER-{cell_id}"
    robot_id = f"ROBOT-{cell_id}"
    imm_data = machines.get(imm_id, {}).get('metrics', {})
    qmc_data = machines.get(qmc_id, {}).get('metrics', {})
    chiller_data = machines.get(chiller_id, {}).get('metrics', {})
    robot_data = machines.get(robot_id, {}).get('metrics', {})
    with st.container():
        st.subheader(f"📍 IMM-{cell_id} and its Auxiliaries")
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            model = imm_data.get('mold_model', 'N/A')
            html = f"<p style='font-size:16px'><b>IMM-{cell_id}</b> | <span style='color:#00FF9F'>Model: {model}</span></p><p>Cycle: {imm_data.get('cycle_time', 0):.1f} s</p><p>Mold Temp: {imm_data.get('mold_temp', 0):.1f} °C</p><p>Clamp: {imm_data.get('clamping_pressure', 0):.0f} ton</p>"
            render_card("Injection Molding", imm_data, "green", html)
            if 'zone_temps' in imm_data:
                with st.expander(f"🌡️ IMM-{cell_id} Temperature Zones (48) - Interactive View"):
                    zone_temps = imm_data['zone_temps']
                    temp_grid = []
                    for row in range(8):
                        temp_grid.append(zone_temps[row*6:(row+1)*6])
                    import plotly.graph_objects as go
                    fig_temp = go.Figure(data=go.Heatmap(
                        z=temp_grid,
                        text=[[f"Z{row*6+col+1}<br>{temp_grid[row][col]:.0f}°C" 
                               for col in range(6)] for row in range(8)],
                        texttemplate="%{text}",
                        textfont={"size": 10},
                        colorscale='RdYlGn_r',
                        zmin=180,
                        zmax=220,
                        colorbar=dict(title="°C")
                    ))
                    fig_temp.update_layout(
                        template='plotly_dark',
                        height=400,
                        xaxis=dict(title="Column", showgrid=False),
                        yaxis=dict(title="Row", showgrid=False)
                    )
                    st.plotly_chart(fig_temp, use_container_width=True)
                    avg_temp = sum(zone_temps) / len(zone_temps)
                    min_temp = min(zone_temps)
                    max_temp = max(zone_temps)
                    st.caption(f"📊 Avg: {avg_temp:.1f}°C | Min: {min_temp:.0f}°C | Max: {max_temp:.0f}°C")
        with c2:
            html = f"<p><b>QMC-{cell_id}</b> | Status: {qmc_data.get('status', 'N/A')}</p><p>Pre-Heat: {qmc_data.get('temp', 0):.1f} °C</p>"
            render_card("Quick Mold Change", qmc_data, "orange", html)
            if 'zone_temps' in qmc_data:
                with st.expander(f"🌡️ QMC-{cell_id} Temperature Zones (48) - Interactive View"):
                    zone_temps = qmc_data['zone_temps']
                    temp_grid = []
                    for row in range(8):
                        temp_grid.append(zone_temps[row*6:(row+1)*6])
                    import plotly.graph_objects as go
                    fig_temp = go.Figure(data=go.Heatmap(
                        z=temp_grid,
                        text=[[f"Z{row*6+col+1}<br>{temp_grid[row][col]:.0f}°C" 
                               for col in range(6)] for row in range(8)],
                        texttemplate="%{text}",
                        textfont={"size": 10},
                        colorscale='RdYlGn_r',
                        zmin=180,
                        zmax=220,
                        colorbar=dict(title="°C")
                    ))
                    fig_temp.update_layout(
                        template='plotly_dark',
                        height=400,
                        xaxis=dict(title="Column", showgrid=False),
                        yaxis=dict(title="Row", showgrid=False)
                    )
                    st.plotly_chart(fig_temp, use_container_width=True)
                    avg_temp = sum(zone_temps) / len(zone_temps)
                    min_temp = min(zone_temps)
                    max_temp = max(zone_temps)
                    st.caption(f"📊 Avg: {avg_temp:.1f}°C | Min: {min_temp:.0f}°C | Max: {max_temp:.0f}°C")
        with c3:
            html = f"<p><b>CHILLER-{cell_id}</b></p><p>Inlet: {chiller_data.get('inlet_temp', 0):.1f} °C | Outlet: {chiller_data.get('outlet_temp', 0):.1f} °C</p><p>Flow: {chiller_data.get('flow_rate', 0):.1f} L/m</p>"
            render_card("Chiller", chiller_data, "blue", html)
        with c4:
            html = f"<p><b>ROBOT-{cell_id}</b></p><p>Grip: {robot_data.get('grip_pressure', 0):.1f} bar</p><p>X: {robot_data.get('axis_x', 0):.0f} | Y: {robot_data.get('axis_y', 0):.0f} | Z: {robot_data.get('axis_z', 0):.0f}</p>"
            render_card("Take-out Robot", robot_data, "cyan", html)
            with st.expander(f"📍 ROBOT-{cell_id} 3D Position"):
                import plotly.graph_objects as go
                x_pos = robot_data.get('axis_x', 0)
                y_pos = robot_data.get('axis_y', 0)
                z_pos = robot_data.get('axis_z', 0)
                fig_robot = go.Figure(data=[go.Scatter3d(
                    x=[0, x_pos],
                    y=[0, y_pos],
                    z=[0, z_pos],
                    mode='markers+lines',
                    marker=dict(size=[8, 12], color=['cyan', 'red']),
                    line=dict(color='cyan', width=3)
                )])
                fig_robot.update_layout(
                    template='plotly_dark',
                    scene=dict(
                        xaxis=dict(title='X Axis (mm)', range=[0, 1000]),
                        yaxis=dict(title='Y Axis (mm)', range=[0, 500]),
                        zaxis=dict(title='Z Axis (mm)', range=[0, 800]),
                    ),
                    height=300,
                    margin=dict(l=0, r=0, t=0, b=0)
                )
                st.plotly_chart(fig_robot, use_container_width=True)
                st.caption(f"📍 Position: X={x_pos:.0f}mm, Y={y_pos:.0f}mm, Z={z_pos:.0f}mm")
        st.markdown("---")
st.markdown("---")
st.title("🧵 Multi-Process Support")
st.subheader("Assembly Equipment - Cutting & Welding Operations")
tcm_vwm_cols = st.columns(4)
with tcm_vwm_cols[0]:
    tcm01_data = machines.get('TCM-01', {}).get('metrics', {})
    model = tcm01_data.get('model', 'N/A')
    html = (
        f"<p style='font-size:16px'><b>TCM-01</b> | <span style='color:#00D9FF'>Model: {model}</span></p>"
        f"<p>Cut Pressure: {tcm01_data.get('cut_pressure', 0):.1f} bar</p>"
        f"<p>Parts Cut: {tcm01_data.get('cycle_count', 0)}</p>"
        f"<p>Status: ✅ Running</p>"
    )
    st.markdown(f"""
<div class="machine-card" style="border: 1px solid cyan; border-left: 5px solid cyan; margin-bottom: 10px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h5 style="margin:0;">✂️ Tear Cutting</h5>
        <span class="status-badge badge-running">✅ RUNNING</span>
    </div>
    <div style="font-size: 0.85em; margin-top: 10px;">{html}</div>
</div>
""", unsafe_allow_html=True)
    with st.expander("📊 Performance"):
        import plotly.graph_objects as go
        import random
        import pandas as pd
        perf_data = pd.DataFrame({'Metric': ['Uptime', 'Efficiency', 'Quality'], 'Value': [random.uniform(95, 99), random.uniform(90, 96), random.uniform(97, 99.5)]})
        fig = go.Figure(go.Bar(x=perf_data['Metric'], y=perf_data['Value'], text=[f"{v:.1f}%" for v in perf_data['Value']], textposition='outside', marker_color=['#00FF9F', '#00D9FF', '#FF6B00']))
        fig.update_layout(template='plotly_dark', height=200, yaxis_range=[0, 100], showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

with tcm_vwm_cols[1]:
    tcm02_data = machines.get('TCM-02', {}).get('metrics', {})
    model = tcm02_data.get('model', 'N/A')
    html = (
        f"<p style='font-size:16px'><b>TCM-02</b> | <span style='color:#00D9FF'>Model: {model}</span></p>"
        f"<p>Cut Pressure: {tcm02_data.get('cut_pressure', 0):.1f} bar</p>"
        f"<p>Parts Cut: {tcm02_data.get('cycle_count', 0)}</p>"
        f"<p>Status: ✅ Running</p>"
    )
    st.markdown(f"""
<div class="machine-card" style="border: 1px solid cyan; border-left: 5px solid cyan; margin-bottom: 10px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h5 style="margin:0;">✂️ Tear Cutting</h5>
        <span class="status-badge badge-running">✅ RUNNING</span>
    </div>
    <div style="font-size: 0.85em; margin-top: 10px;">{html}</div>
</div>
""", unsafe_allow_html=True)
    with st.expander("📊 Performance"):
        import plotly.graph_objects as go
        import random
        import pandas as pd
        perf_data = pd.DataFrame({'Metric': ['Uptime', 'Efficiency', 'Quality'], 'Value': [random.uniform(95, 99), random.uniform(90, 96), random.uniform(97, 99.5)]})
        fig = go.Figure(go.Bar(x=perf_data['Metric'], y=perf_data['Value'], text=[f"{v:.1f}%" for v in perf_data['Value']], textposition='outside', marker_color=['#00FF9F', '#00D9FF', '#FF6B00']))
        fig.update_layout(template='plotly_dark', height=200, yaxis_range=[0, 100], showlegend=False, margin=dict(l=0, r=0, t=10, b=0))
        st.plotly_chart(fig, use_container_width=True)

with tcm_vwm_cols[2]:
    vwm01_data = machines.get('VWM-01', {}).get('metrics', {})
    model = vwm01_data.get('model', 'N/A')
    html = (
        f"<p style='font-size:16px'><b>VWM-01</b> | <span style='color:#FF6B00'>Model: {model}</span></p>"
        f"<p>Weld Freq: {vwm01_data.get('weld_freq', 0):.0f} Hz</p>"
        f"<p>Weld Time: {vwm01_data.get('weld_time', 0):.2f} s</p>"
        f"<p>Status: ✅ Running</p>"
    )
    st.markdown(f"""
<div class="machine-card" style="border: 1px solid purple; border-left: 5px solid purple; margin-bottom: 10px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h5 style="margin:0;">🔧 Vibration Welding</h5>
        <span class="status-badge badge-running">✅ RUNNING</span>
    </div>
    <div style="font-size: 0.85em; margin-top: 10px;">{html}</div>
</div>
""", unsafe_allow_html=True)
    with st.expander("⚙️ Parameters"):
        st.metric("Frequency", f"{vwm01_data.get('weld_freq', 0):.0f} Hz")
        st.metric("Amplitude", f"{random.uniform(30, 50):.1f} µm")
        st.metric("Weld Time", f"{vwm01_data.get('weld_time', 0):.2f} s")

with tcm_vwm_cols[3]:
    vwm02_data = machines.get('VWM-02', {}).get('metrics', {})
    model = vwm02_data.get('model', 'N/A')
    html = (
        f"<p style='font-size:16px'><b>VWM-02</b> | <span style='color:#FF6B00'>Model: {model}</span></p>"
        f"<p>Weld Freq: {vwm02_data.get('weld_freq', 0):.0f} Hz</p>"
        f"<p>Weld Time: {vwm02_data.get('weld_time', 0):.2f} s</p>"
        f"<p>Status: ✅ Running</p>"
    )
    st.markdown(f"""
<div class="machine-card" style="border: 1px solid purple; border-left: 5px solid purple; margin-bottom: 10px;">
    <div style="display: flex; justify-content: space-between; align-items: center;">
        <h5 style="margin:0;">🔧 Vibration Welding</h5>
        <span class="status-badge badge-running">✅ RUNNING</span>
    </div>
    <div style="font-size: 0.85em; margin-top: 10px;">{html}</div>
</div>
""", unsafe_allow_html=True)
    with st.expander("⚙️ Parameters"):
        st.metric("Frequency", f"{vwm02_data.get('weld_freq', 0):.0f} Hz")
        st.metric("Amplitude", f"{random.uniform(30, 50):.1f} µm")
        st.metric("Weld Time", f"{vwm02_data.get('weld_time', 0):.2f} s")
st.markdown("---")
st.caption("💡 Multi-Process Support produces safety-critical components for multi-process systems")
