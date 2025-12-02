import streamlit as st
import requests
import time
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import plotly.graph_objects as go
import random

st.set_page_config(page_title="Production Control System", layout="wide", initial_sidebar_state="expanded")

API_URL = "http://localhost:8000/api/v1/telemetry/latest"

# --- Data Fetching ---
def fetch_data():
    try:
        response = requests.get(API_URL)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}

machines = fetch_data()

# --- Sidebar Navigation ---
st.sidebar.title("🏭 Production Control System")
page = st.sidebar.radio("Navigate", ["Executive Summary", "Shop Floor (Cells)", "Invisible Airbag Facility"])

st.sidebar.markdown("---")
if st.sidebar.button("Refresh Data"):
    st.rerun()
st.sidebar.caption(f"Last Update: {datetime.now().strftime('%H:%M:%S')}")

# --- Helper Functions ---
def get_status_color(metrics):
    status = metrics.get("status", "RUNNING")
    if status == "RUNNING": return "green"
    if status == "PREHEATING": return "orange"
    return "red"

def render_card(title, metrics, color="green", extra_html=""):
    st.markdown(f"""
    <div style="border: 1px solid {color}; border-left: 5px solid {color}; border-radius: 5px; padding: 10px; margin-bottom: 10px; background-color: #1E1E1E;">
        <h5 style="margin:0;">{title}</h5>
        <div style="font-size: 0.85em; margin-top: 5px;">
            {extra_html}
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Page: Executive Summary ---
if page == "Executive Summary":
    st.title("📊 Production Control System - Executive Dashboard")
    
    # KPIs
    total_machines = len(machines)
    active_machines = sum(1 for m in machines.values() if m.get('metrics', {}).get('cycle_time', 0) > 0)
    avg_cycle = 0
    imms = [m['metrics']['cycle_time'] for k, m in machines.items() if k.startswith('IMM') and 'cycle_time' in m['metrics']]
    if imms: avg_cycle = sum(imms) / len(imms)
    
    # Calculate OEE (mock calculation)
    oee = min(95, 85 + random.uniform(0, 10))
    
    kpi1, kpi2, kpi3, kpi4 = st.columns(4)
    kpi1.metric("Active Assets", f"{active_machines}/{total_machines}", delta="100%")
    kpi2.metric("Avg Cycle Time (IMM)", f"{avg_cycle:.1f} s", delta="-0.5 s")
    kpi3.metric("Overall OEE", f"{oee:.1f}%", delta="+2.1%")
    kpi4.metric("Parts/Hour (Target: 240)", "228", delta="-12")
    
    st.markdown("---")
    
    # Interactive Charts
    c1, c2 = st.columns(2)
    
    with c1:
        st.subheader("📈 Production Volume Trends (Last 24h)")
        # Generate realistic hourly data
        hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
        production_data = pd.DataFrame({
            'Time': hours,
            'Parts Produced': [random.randint(180, 260) for _ in range(24)],
            'Target': [240] * 24
        })
        
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=production_data['Time'], y=production_data['Parts Produced'], 
                                  mode='lines+markers', name='Actual', 
                                  line=dict(color='#00D9FF', width=3)))
        fig1.add_trace(go.Scatter(x=production_data['Time'], y=production_data['Target'], 
                                  mode='lines', name='Target', 
                                  line=dict(color='#FF6B00', width=2, dash='dash')))
        fig1.update_layout(
            template='plotly_dark',
            height=400,
            hovermode='x unified',
            xaxis_title='Time',
            yaxis_title='Parts/Hour'
        )
        st.plotly_chart(fig1, use_container_width=True)
        
    with c2:
        st.subheader("⚡ OEE Breakdown")
        # OEE components
        availability = random.uniform(90, 98)
        performance = random.uniform(88, 96)
        quality = random.uniform(95, 99)
        
        oee_data = pd.DataFrame({
            'Metric': ['Availability', 'Performance', 'Quality'],
            'Value': [availability, performance, quality]
        })
        
        fig2 = go.Figure(go.Bar(
            x=oee_data['Metric'],
            y=oee_data['Value'],
            text=[f"{v:.1f}%" for v in oee_data['Value']],
            textposition='outside',
            marker_color=['#00D9FF', '#FF6B00', '#00FF9F']
        ))
        fig2.update_layout(
            template='plotly_dark',
            height=400,
            yaxis_range=[0, 100],
            yaxis_title='Percentage (%)',
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)
    
    # Second Row
    c3, c4 = st.columns(2)
    
    with c3:
        st.subheader("🔧 Machine Status Distribution")
        # Count machines by type and status
        imm_count = len([k for k in machines.keys() if k.startswith('IMM')])
        qmc_count = len([k for k in machines.keys() if k.startswith('QMC')])
        robot_count = len([k for k in machines.keys() if k.startswith('ROBOT')])
        
        status_data = pd.DataFrame({
            'Type': ['IMM', 'QMC', 'Robot', 'Chiller', 'Assembly'],
            'Running': [imm_count, 0, robot_count, 8, 4],
            'Idle': [0, qmc_count, 0, 0, 0]
        })
        
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name='Running', x=status_data['Type'], y=status_data['Running'], 
                              marker_color='#00FF9F'))
        fig3.add_trace(go.Bar(name='Standby', x=status_data['Type'], y=status_data['Idle'], 
                              marker_color='#FFA500'))
        
        fig3.update_layout(
            template='plotly_dark',
            barmode='stack',
            height=400,
            yaxis_title='Count'
        )
        st.plotly_chart(fig3, use_container_width=True)
        
    with c4:
        st.subheader("⏱️ Downtime Analysis (Last 7 Days)")
        # Mock downtime data
        reasons = ['Mold Change', 'Maintenance', 'Material Wait', 'Quality Issue', 'Other']
        downtime_mins = [120, 85, 45, 30, 20]
        
        fig4 = go.Figure(go.Pie(
            labels=reasons,
            values=downtime_mins,
            hole=0.4,
            marker_colors=['#FF6B00', '#00D9FF', '#FFA500', '#FF4444', '#888888']
        ))
        fig4.update_layout(
            template='plotly_dark',
            height=400,
            annotations=[dict(text='300 mins<br>Total', x=0.5, y=0.5, font_size=16, showarrow=False)]
        )
        st.plotly_chart(fig4, use_container_width=True)

# --- Page: Shop Floor (Cells) ---
elif page == "Shop Floor (Cells)":
    st.title("🏭 Injection Molding and Bumper Shop A & B Line")
    
    # Group by Cell (1-8)
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
            
            # IMM Card
            with c1:
                model = imm_data.get('mold_model', 'N/A')
                html = f"<p><b>IMM-{cell_id}</b> | Model: {model}</p><p>Cycle: {imm_data.get('cycle_time', 0):.1f} s</p><p>Mold Temp: {imm_data.get('mold_temp', 0):.1f} °C</p><p>Clamp: {imm_data.get('clamping_pressure', 0):.0f} ton</p>"
                render_card("Injection Molding", imm_data, "green", html)
                
                if 'zone_temps' in imm_data:
                    with st.expander(f"IMM-{cell_id} Zones (48)"):
                        z_cols = st.columns(6)
                        for z_idx, temp in enumerate(imm_data['zone_temps']):
                             z_cols[z_idx % 6].caption(f"Z{z_idx+1}: {temp:.0f}°")

            # QMC Card
            with c2:
                html = f"<p><b>QMC-{cell_id}</b> | Status: {qmc_data.get('status', 'N/A')}</p><p>Pre-Heat: {qmc_data.get('temp', 0):.1f} °C</p>"
                render_card("Quick Mold Change", qmc_data, "orange", html)
                
                if 'zone_temps' in qmc_data:
                    with st.expander(f"QMC-{cell_id} Zones (48)"):
                        z_cols = st.columns(6)
                        for z_idx, temp in enumerate(qmc_data['zone_temps']):
                             z_cols[z_idx % 6].caption(f"Z{z_idx+1}: {temp:.0f}°")

            # Chiller Card
            with c3:
                html = f"<p><b>CHILLER-{cell_id}</b></p><p>Water: {chiller_data.get('water_temp', 0):.1f} °C</p><p>Flow: {chiller_data.get('flow_rate', 0):.1f} L/m</p>"
                render_card("Chiller", chiller_data, "blue", html)

            # Robot Card
            with c4:
                html = f"<p><b>ROBOT-{cell_id}</b></p><p>Grip Pressure: {robot_data.get('grip_pressure', 0):.1f} bar</p><p>Axis X: {robot_data.get('axis_x', 0):.0f}</p>"
                render_card("Take-out Robot", robot_data, "cyan", html)
            
            st.markdown("---")

# --- Page: Invisible Airbag Facility ---
elif page == "Invisible Airbag Facility":
    st.title("🧵 Invisible Airbag Facility")
    
    cols = st.columns(4)
    
    # Filter for TCM and VWM
    assembly_machines = {k: v for k, v in machines.items() if k.startswith("TCM") or k.startswith("VWM")}
    
    for idx, (dev_id, data) in enumerate(sorted(assembly_machines.items())):
        metrics = data.get('metrics', {})
        col = cols[idx % 4]
        with col:
            html = ""
            if dev_id.startswith("TCM"):
                html = f"<p>Pressure: {metrics.get('cut_pressure', 0):.1f} bar</p><p>Count: {metrics.get('cycle_count', 0)}</p>"
            else:
                html = f"<p>Freq: {metrics.get('weld_freq', 0):.0f} Hz</p><p>Time: {metrics.get('weld_time', 0):.2f} s</p>"
            
            render_card(dev_id, metrics, "purple", html)
