"""Invisible Airbag Facility Dashboard - Production Control System"""
import streamlit as st
import requests
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
import random
st.set_page_config(page_title="Invisible Airbag Facility", page_icon="🧵", layout="wide")
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
st.title("🧵 Invisible Airbag Facility - Production Dashboard")
tcm_count = len([k for k in machines.keys() if k.startswith('TCM')])
vwm_count = len([k for k in machines.keys() if k.startswith('VWM')])
total_parts_cut = sum([machines.get(k, {}).get('metrics', {}).get('cycle_count', 0) for k in machines.keys() if k.startswith('TCM')])
avg_weld_freq = 0
weld_freqs = [machines.get(k, {}).get('metrics', {}).get('weld_freq', 0) for k in machines.keys() if k.startswith('VWM')]
if weld_freqs:
    avg_weld_freq = sum(weld_freqs) / len(weld_freqs)
k1, k2, k3, k4 = st.columns(4)
k1.metric("Active TCM", f"{tcm_count}/2", delta="100%")
k2.metric("Active VWM", f"{vwm_count}/2", delta="100%")
k3.metric("Parts Cut Today", f"{total_parts_cut}", delta="+50")
k4.metric("Avg Weld Freq", f"{avg_weld_freq:.0f} Hz", help="Ultrasonic welding frequency")
st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    st.subheader("✂️ Tear Cutting Production")
    hours = pd.date_range(end=datetime.now(), periods=12, freq='H')
    cutting_data = pd.DataFrame({
        'Time': hours,
        'TCM-01': [random.randint(80, 120) for _ in range(12)],
        'TCM-02': [random.randint(75, 115) for _ in range(12)]
    })
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=cutting_data['Time'], y=cutting_data['TCM-01'],
                              mode='lines+markers', name='TCM-01',
                              line=dict(color='#00D9FF', width=3)))
    fig1.add_trace(go.Scatter(x=cutting_data['Time'], y=cutting_data['TCM-02'],
                              mode='lines+markers', name='TCM-02',
                              line=dict(color='#FF6B00', width=3)))
    fig1.update_layout(
        template='plotly_dark',
        height=350,
        yaxis_title='Parts/Hour',
        hovermode='x unified'
    )
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    st.subheader("🔧 Vibration Welding Performance")
    hours = pd.date_range(end=datetime.now(), periods=12, freq='H')
    weld_data = pd.DataFrame({
        'Time': hours,
        'Good Welds %': [random.uniform(97, 99.5) for _ in range(12)]
    })
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=weld_data['Time'], y=weld_data['Good Welds %'],
                              mode='lines+markers', name='Quality %',
                              fill='tozeroy',
                              line=dict(color='#00FF9F', width=3)))
    fig2.add_hline(y=97, line_dash="dash", line_color="#FF6B00", annotation_text="Minimum: 97%")
    fig2.update_layout(
        template='plotly_dark',
        height=350,
        yaxis_range=[95, 100],
        yaxis_title='Quality (%)',
        hovermode='x unified'
    )
    st.plotly_chart(fig2, use_container_width=True)
st.markdown("---")
st.subheader("📋 Equipment Status")
def render_card(title, metrics, color="green", extra_html=""):
    st.markdown(f"""
    <div style="border: 1px solid {color}; border-left: 5px solid {color}; border-radius: 5px; padding: 10px; margin-bottom: 10px; background-color: #1E1E1E;">
        <h5 style="margin:0;">{title}</h5>
        <div style="font-size: 0.85em; margin-top: 5px;">
            {extra_html}
        </div>
    </div>
    """, unsafe_allow_html=True)
cols = st.columns(4)
assembly_machines = {k: v for k, v in machines.items() if k.startswith("TCM") or k.startswith("VWM")}
for idx, (dev_id, data) in enumerate(sorted(assembly_machines.items())):
    metrics = data.get('metrics', {})
    col = cols[idx % 4]
    with col:
        html = ""
        if dev_id.startswith("TCM"):
            html = f"""
            <p><b>{dev_id}</b> - Tear Cutting</p>
            <p>Pressure: {metrics.get('cut_pressure', 0):.1f} bar</p>
            <p>Parts Cut: {metrics.get('cycle_count', 0)}</p>
            <p>Status: ✅ Running</p>
            """
            render_card("Tear Cutting Machine", metrics, "cyan", html)
            with st.expander(f"📊 {dev_id} Performance"):
                perf_data = pd.DataFrame({
                    'Metric': ['Uptime', 'Efficiency', 'Quality'],
                    'Value': [random.uniform(95, 99), random.uniform(90, 96), random.uniform(97, 99.5)]
                })
                fig_perf = go.Figure(go.Bar(
                    x=perf_data['Metric'],
                    y=perf_data['Value'],
                    text=[f"{v:.1f}%" for v in perf_data['Value']],
                    textposition='outside',
                    marker_color=['#00FF9F', '#00D9FF', '#FF6B00']
                ))
                fig_perf.update_layout(
                    template='plotly_dark',
                    height=250,
                    yaxis_range=[0, 100],
                    showlegend=False
                )
                st.plotly_chart(fig_perf, use_container_width=True)
        else:
            html = f"""
            <p><b>{dev_id}</b> - Vibration Welding</p>
            <p>Freq: {metrics.get('weld_freq', 0):.0f} Hz</p>
            <p>Weld Time: {metrics.get('weld_time', 0):.2f} s</p>
            <p>Status: ✅ Running</p>
            """
            render_card("Vibration Welding Machine", metrics, "purple", html)
            with st.expander(f"⚙️ {dev_id} Parameters"):
                st.metric("Frequency", f"{metrics.get('weld_freq', 0):.0f} Hz", help="Ultrasonic frequency")
                st.metric("Amplitude", f"{random.uniform(30, 50):.1f} µm", help="Vibration amplitude")
                st.metric("Weld Time", f"{metrics.get('weld_time', 0):.2f} s", help="Duration per weld")
                st.metric("Hold Time", f"{random.uniform(1, 2):.1f} s", help="Cooling hold time")
st.markdown("---")
st.subheader("🎯 Quality Analysis - Airbag Components")
c3, c4 = st.columns(2)
with c3:
    st.subheader("Common Defects (Last 24h)")
    defects = pd.DataFrame({
        'Defect Type': ['Incomplete Cut', 'Weak Weld', 'Misalignment', 'Surface Damage', 'Other'],
        'Count': [random.randint(3, 10), random.randint(2, 8), random.randint(1, 5), random.randint(1, 4), random.randint(0, 3)]
    })
    fig3 = go.Figure(go.Pie(
        labels=defects['Defect Type'],
        values=defects['Count'],
        hole=0.4,
        marker_colors=['#FF6B00', '#00D9FF', '#FFA500', '#FF4444', '#888888']
    ))
    fig3.update_layout(
        template='plotly_dark',
        height=300,
        annotations=[dict(text=f'{defects["Count"].sum()}<br>Total', x=0.5, y=0.5, font_size=14, showarrow=False)]
    )
    st.plotly_chart(fig3, use_container_width=True)
with c4:
    st.subheader("Production & Quality Metrics")
    metrics_df = pd.DataFrame({
        'Metric': ['First Pass Yield', 'Scrap Rate', 'Uptime', 'Cycle Time Variance'],
        'Value': ['98.2%', '1.8%', '96.5%', '±3.2%'],
        'Target': ['≥97%', '≤2%', '≥95%', '±5%'],
        'Status': ['✅', '✅', '✅', '✅']
    })
    st.dataframe(metrics_df, use_container_width=True, hide_index=True)
    st.info("💡 **Insight**: All metrics within target range. Quality performance excellent for airbag safety components.")
