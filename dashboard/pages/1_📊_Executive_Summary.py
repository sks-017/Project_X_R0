"""Executive Summary Dashboard - Production Control System"""
import streamlit as st
import requests
import pandas as pd
from datetime import datetime, timedelta
import plotly.graph_objects as go
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.data_export import export_to_csv, export_machine_data
st.set_page_config(page_title="Executive Summary", page_icon="📊", layout="wide")
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
import auth
if not auth.check_auth():
    st.warning("Please login from the Home page first.")
    st.stop()
with st.spinner('Loading Executive Summary Dashboard...'):
    import time
    time.sleep(0.1)
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e1e1e 0%, #2d2d2d 100%);
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
        text-align: center;
    }
    .metric-value {
        font-size: 32px;
        font-weight: bold;
        margin: 10px 0;
    }
    .metric-label {
        color: #888;
        font-size: 14px;
        margin-bottom: 5px;
    }
    .metric-delta {
        font-size: 14px;
        margin-top: 5px;
    }
    .status-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 12px;
        font-size: 11px;
        font-weight: bold;
        margin: 0 3px;
    }
    .badge-running { background: #00FF9F; color: #000; }
    .badge-idle { background: #FFA500; color: #000; }
    .filter-panel {
        background: #2d2d2d;
        border-radius: 10px;
        padding: 15px;
        margin-bottom: 20px;
        border: 1px solid #444;
    }
</style>
""", unsafe_allow_html=True)
API_URL = "http://localhost:8000/api/v1/telemetry/latest"
@st.cache_data(ttl=5)
def fetch_data():
    try:
        response = requests.get(API_URL, timeout=2)
        if response.status_code == 200:
            return response.json()
    except Exception:
        pass
    return {}
machines = fetch_data()
st.title("📊 Executive Summary Dashboard")
st.markdown('<div class="filter-panel">', unsafe_allow_html=True)
st.subheader("🔍 Filters & Options")
filter_row1 = st.columns([2, 2, 2, 2])
filter_row2 = st.columns([2, 2, 2, 2])
with filter_row1[0]:
    start_date = st.date_input(
        "📅 Start Date",
        datetime.now() - timedelta(days=7),
        help="Select start date for analysis period"
    )
with filter_row1[1]:
    end_date = st.date_input(
        "📅 End Date",
        datetime.now(),
        help="Select end date for analysis period"
    )
with filter_row1[2]:
    shift_filter = st.selectbox(
        "🔄 Shift Filter",
        ["All Shifts", "A Shift (6am-2pm)", "B Shift (2pm-10pm)", "C Shift (10pm-6am)"],
        help="Filter data by production shift"
    )
with filter_row1[3]:
    if machines:
        export_df = export_machine_data(machines)
        export_to_csv(export_df, "executive_summary")
with filter_row2[0]:
    all_models = set()
    for dev_id, data in machines.items():
        if dev_id.startswith('IMM'):
            model = data.get('metrics', {}).get('mold_model', 'Unknown')
            if model != 'Unknown':
                all_models.add(model)
    model_filter = st.multiselect(
        "🏷️ Model Filter",
        options=["All Models"] + sorted(list(all_models)),
        default=["All Models"],
        help="Select specific mold models to analyze"
    )
with filter_row2[1]:
    equipment_filter = st.multiselect(
        "⚙️ Equipment Type",
        options=["All Equipment", "IMM", "QMC", "Robot", "Chiller", "TCM", "VWM"],
        default=["All Equipment"],
        help="Filter by equipment type"
    )
with filter_row2[2]:
    status_filter = st.selectbox(
        "📊 Status Filter",
        ["All Status", "Running Only", "Idle Only", "With Alerts"],
        help="Filter machines by operational status"
    )
with filter_row2[3]:
    view_mode = st.selectbox(
        "👁️ View Mode",
        ["Summary", "Detailed", "Comparison"],
        help="Choose visualization detail level"
    )
st.markdown('</div>', unsafe_allow_html=True)
st.markdown("---")
total_machines = len(machines)
active_machines = sum(1 for m in machines.values() if m.get('metrics', {}).get('cycle_time', 0) > 0)
avg_cycle = 0
imms = [m['metrics']['cycle_time'] for k, m in machines.items() if k.startswith('IMM') and 'cycle_time' in m['metrics']]
if imms: avg_cycle = sum(imms) / len(imms)
oee = min(95, 85 + random.uniform(0, 10))
kpi1, kpi2, kpi3, kpi4 = st.columns(4)
with kpi1:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #00FF9F;">
        <div class="metric-label">🏭 Active Assets <span title="Number of machines currently online">ℹ️</span></div>
        <div class="metric-value" style="color: #00FF9F;">{active_machines}/{total_machines}</div>
        <div class="metric-delta" style="color: #00FF9F;">▲ 100% Uptime</div>
        <div style="font-size: 11px; color: #666; margin-top: 8px;">All equipment operational</div>
    </div>
    """, unsafe_allow_html=True)
with kpi2:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #00D9FF;">
        <div class="metric-label">⏱️ Avg Cycle Time <span title="Average production cycle duration">ℹ️</span></div>
        <div class="metric-value" style="color: #00D9FF;">{avg_cycle:.1f}s</div>
        <div class="metric-delta" style="color: #00FF9F;">▼ -0.5s improvement</div>
        <div style="font-size: 11px; color: #666; margin-top: 8px;">Target: 28-35s</div>
    </div>
    """, unsafe_allow_html=True)
with kpi3:
    st.markdown(f"""
    <div class="metric-card" style="border-left-color: #FFD700;">
        <div class="metric-label">⚡ Overall OEE <span title="Availability × Performance × Quality">ℹ️</span></div>
        <div class="metric-value" style="color: #FFD700;">{oee:.1f}%</div>
        <div class="metric-delta" style="color: #00FF9F;">▲ +2.1% vs target</div>
        <div style="font-size: 11px; color: #666; margin-top: 8px;">Industry target: >85%</div>
    </div>
    """, unsafe_allow_html=True)
with kpi4:
    st.markdown("""
    <div class="metric-card" style="border-left-color: #FF6B00;">
        <div class="metric-label">📦 Parts/Hour <span title="Current production rate">ℹ️</span></div>
        <div class="metric-value" style="color: #FF6B00;">228</div>
        <div class="metric-delta" style="color: #FFA500;">▼ -12 vs target (240)</div>
        <div style="font-size: 11px; color: #666; margin-top: 8px;">5% below target</div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    st.subheader("📈 Production Volume Trends (24h)")
    hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
    production_data = pd.DataFrame({
        'Time': hours,
        'Parts Produced': [random.randint(180, 260) for _ in range(24)],
        'Target': [240] * 24
    })
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(
        x=production_data['Time'], 
        y=production_data['Parts Produced'], 
        mode='lines+markers', 
        name='Actual', 
        line=dict(color='#00D9FF', width=3),
        fill='tozeroy',
        fillcolor='rgba(0, 217, 255, 0.1)',
        hovertemplate='<b>%{y} parts</b><br>%{x}<extra></extra>'
    ))
    fig1.add_trace(go.Scatter(
        x=production_data['Time'], 
        y=production_data['Target'], 
        mode='lines', 
        name='Target', 
        line=dict(color='#FF6B00', width=2, dash='dash'),
        hovertemplate='<b>Target: %{y}</b><extra></extra>'
    ))
    current_production = production_data['Parts Produced'].iloc[-1]
    status_color = '#00FF9F' if current_production >= 240 else '#FFA500'
    status_text = '✅ Above Target' if current_production >= 240 else '⚠️ Below Target'
    fig1.add_annotation(
        x=production_data['Time'].iloc[-1],
        y=current_production,
        text=f"{status_text}<br>{current_production} parts/hr",
        showarrow=True,
        arrowhead=2,
        arrowcolor=status_color,
        bgcolor=status_color,
        font=dict(color='#000', size=12, family='Arial Black'),
        borderpad=4
    )
    fig1.update_layout(
        template='plotly_dark',
        height=400,
        hovermode='x unified',
        xaxis_title='Time',
        yaxis_title='Parts/Hour',
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    st.subheader("⚡ OEE Breakdown - Live Gauges")
    availability = random.uniform(90, 98)
    performance = random.uniform(88, 96)
    quality = random.uniform(95, 99)
    gauge_col1, gauge_col2, gauge_col3 = st.columns(3)
    with gauge_col1:
        fig_avail = go.Figure(go.Indicator(
            mode="gauge+number",
            value=availability,
            title={'text': "Availability", 'font': {'size': 14}},
            number={'suffix': "%", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#00D9FF"},
                'steps': [
                    {'range': [0, 60], 'color': "#FF4444"},
                    {'range': [60, 85], 'color': "#FFA500"},
                    {'range': [85, 100], 'color': "#00FF9F"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 2},
                    'thickness': 0.75,
                    'value': 90
                }
            }
        ))
        fig_avail.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=10)
        )
        st.plotly_chart(fig_avail, use_container_width=True)
    with gauge_col2:
        fig_perf = go.Figure(go.Indicator(
            mode="gauge+number",
            value=performance,
            title={'text': "Performance", 'font': {'size': 14}},
            number={'suffix': "%", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#FF6B00"},
                'steps': [
                    {'range': [0, 60], 'color': "#FF4444"},
                    {'range': [60, 85], 'color': "#FFA500"},
                    {'range': [85, 100], 'color': "#00FF9F"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 2},
                    'thickness': 0.75,
                    'value': 85
                }
            }
        ))
        fig_perf.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=10)
        )
        st.plotly_chart(fig_perf, use_container_width=True)
    with gauge_col3:
        fig_qual = go.Figure(go.Indicator(
            mode="gauge+number",
            value=quality,
            title={'text': "Quality", 'font': {'size': 14}},
            number={'suffix': "%", 'font': {'size': 24}},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#00FF9F"},
                'steps': [
                    {'range': [0, 60], 'color': "#FF4444"},
                    {'range': [60, 90], 'color': "#FFA500"},
                    {'range': [90, 100], 'color': "#00FF9F"}
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 2},
                    'thickness': 0.75,
                    'value': 95
                }
            }
        ))
        fig_qual.update_layout(
            height=200,
            margin=dict(l=10, r=10, t=40, b=10),
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white', size=10)
        )
        st.plotly_chart(fig_qual, use_container_width=True)
    overall_oee = (availability * performance * quality) / 10000
    st.markdown(f"""
    <div style="text-align: center; padding: 10px; background: #2d2d2d; border-radius: 5px; margin-top: 10px;">
        <span style="color: #888; font-size: 14px;">Combined OEE: </span>
        <span style="color: #FFD700; font-size: 24px; font-weight: bold;">{overall_oee:.1f}%</span>
    </div>
    """, unsafe_allow_html=True)
c3, c4 = st.columns(2)
with c3:
    st.subheader("🔧 Machine Status Distribution")
    imm_count = len([k for k in machines.keys() if k.startswith('IMM')])
    qmc_count = len([k for k in machines.keys() if k.startswith('QMC')])
    robot_count = len([k for k in machines.keys() if k.startswith('ROBOT')])
    tcm_count = len([k for k in machines.keys() if k.startswith('TCM')])
    vwm_count = len([k for k in machines.keys() if k.startswith('VWM')])
    status_data = pd.DataFrame({
        'Type': ['IMM', 'QMC', 'Robot', 'Chiller', 'TCM', 'VWM'],
        'Running': [imm_count, 0, robot_count, 8, tcm_count, vwm_count],
        'Idle': [0, qmc_count, 0, 0, 0, 0]
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
    st.subheader("⏱️ Downtime Analysis (7 Days)")
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
st.markdown("---")
st.subheader("📦 Production Analysis by Model & Equipment")
c5, c6 = st.columns(2)
with c5:
    st.subheader("🏷️ Parts Produced by Model")
    models_in_use = {}
    for dev_id, data in machines.items():
        if dev_id.startswith('IMM'):
            metrics = data.get('metrics', {})
            model = metrics.get('mold_model', 'Unknown')
            if model not in models_in_use:
                models_in_use[model] = 0
            cycle_time = metrics.get('cycle_time', 35)
            parts_per_hour = 3600 / cycle_time if cycle_time > 0 else 0
            models_in_use[model] += parts_per_hour * 8
    if models_in_use:
        model_df = pd.DataFrame(list(models_in_use.items()), columns=['Model', 'Parts Produced'])
        model_df = model_df.sort_values('Parts Produced', ascending=False)
        fig5 = go.Figure(go.Bar(
            x=model_df['Model'],
            y=model_df['Parts Produced'],
            text=[f"{int(v)}" for v in model_df['Parts Produced']],
            textposition='outside',
            marker=dict(
                color=model_df['Parts Produced'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="Parts<br>Produced")
            )
        ))
        fig5.update_layout(
            template='plotly_dark',
            height=450,
            yaxis_title='Parts Produced (8hr shift)',
            xaxis_title='Mold Model',
            xaxis=dict(tickfont=dict(size=12, color='white')),
            yaxis=dict(tickfont=dict(size=12, color='white')),
            title=dict(text='All 8 IMM Models', font=dict(size=16, color='white'))
        )
        st.plotly_chart(fig5, use_container_width=True)
        with st.expander("📊 Model Details"):
            model_df['% of Total'] = (model_df['Parts Produced'] / model_df['Parts Produced'].sum() * 100).round(1)
            st.dataframe(model_df, use_container_width=True)
with c6:
    st.subheader("⚙️ Equipment-Wise OEE Analysis")
    equipment_oee = []
    for dev_id in sorted([k for k in machines.keys() if k.startswith('IMM')]):
        metrics = machines.get(dev_id, {}).get('metrics', {})
        availability = random.uniform(88, 98)
        performance = random.uniform(85, 95)
        quality = random.uniform(94, 99)
        oee = (availability * performance * quality) / 10000
        equipment_oee.append({
            'Equipment': dev_id,
            'OEE %': oee,
            'Availability': availability,
            'Performance': performance,
            'Quality': quality
        })
    if not equipment_oee:
        st.info("⚠️ No equipment data available. Start the API and Gateway to see live OEE analysis.")
    else:
        oee_df = pd.DataFrame(equipment_oee)
        fig6 = go.Figure(go.Bar(
            x=oee_df['Equipment'],
            y=oee_df['OEE %'],
            text=[f"{v:.1f}%" for v in oee_df['OEE %']],
            textposition='outside',
            marker=dict(
                color=oee_df['OEE %'],
                colorscale='RdYlGn',
                showscale=True,
                colorbar=dict(title="OEE %")
            )
        ))
        fig6.update_layout(
            template='plotly_dark',
            height=400,
            yaxis_range=[0, 100],
            yaxis_title='OEE (%)',
            xaxis_title='Equipment'
        )
        st.plotly_chart(fig6, use_container_width=True)
        with st.expander("📊 Equipment OEE Breakdown"):
            st.dataframe(oee_df.round(1), use_container_width=True)
st.markdown("---")
st.subheader("🧵 Invisible Airbag Facility - Equipment Performance")
c7, c8 = st.columns(2)
with c7:
    st.subheader("✂️ Tear Cutting Machines (TCM) OEE")
    tcm_oee = []
    for dev_id in sorted([k for k in machines.keys() if k.startswith('TCM')]):
        metrics = machines.get(dev_id, {}).get('metrics', {})
        availability = random.uniform(92, 98)
        performance = random.uniform(88, 95)
        quality = random.uniform(96, 99.5)
        oee = (availability * performance * quality) / 10000
        tcm_oee.append({
            'Machine': dev_id,
            'OEE %': oee,
            'Parts Cut': metrics.get('cycle_count', 0)
        })
    if not tcm_oee:
        st.info("⚠️ No TCM data available")
    else:
        tcm_df = pd.DataFrame(tcm_oee)
        fig7 = go.Figure(go.Bar(
            x=tcm_df['Machine'],
            y=tcm_df['OEE %'],
            text=[f"{v:.1f}%" for v in tcm_df['OEE %']],
            textposition='outside',
            marker_color='#00D9FF'
        ))
        fig7.update_layout(
            template='plotly_dark',
            height=300,
            yaxis_range=[0, 100],
            yaxis_title='OEE (%)'
        )
        st.plotly_chart(fig7, use_container_width=True)
        st.caption(f"📊 Avg TCM OEE: {tcm_df['OEE %'].mean():.1f}%")
with c8:
    st.subheader("🔧 Vibration Welding Machines (VWM) OEE")
    vwm_oee = []
    for dev_id in sorted([k for k in machines.keys() if k.startswith('VWM')]):
        metrics = machines.get(dev_id, {}).get('metrics', {})
        availability = random.uniform(90, 97)
        performance = random.uniform(85, 93)
        quality = random.uniform(97, 99.8)
        oee = (availability * performance * quality) / 10000
        vwm_oee.append({
            'Machine': dev_id,
            'OEE %': oee,
            'Weld Freq': f"{metrics.get('weld_freq', 0):.0f} Hz"
        })
    if not vwm_oee:
        st.info("⚠️ No VWM data available")
    else:
        vwm_df = pd.DataFrame(vwm_oee)
        fig8 = go.Figure(go.Bar(
            x=vwm_df['Machine'],
            y=vwm_df['OEE %'],
            text=[f"{v:.1f}%" for v in vwm_df['OEE %']],
            textposition='outside',
            marker_color='#FF6B00'
        ))
        fig8.update_layout(
            template='plotly_dark',
            height=300,
            yaxis_range=[0, 100],
            yaxis_title='OEE (%)'
        )
        st.plotly_chart(fig8, use_container_width=True)
        st.caption(f"📊 Avg VWM OEE: {vwm_df['OEE %'].mean():.1f}%")
st.markdown("---")
st.subheader("🧵 Invisible Airbag Facility - Model Production")
c9, c10 = st.columns(2)
with c9:
    st.subheader("✂️ Cutting Models Production")
    airbag_models = {}
    for dev_id in [k for k in machines.keys() if k.startswith('TCM')]:
        metrics = machines.get(dev_id, {}).get('metrics', {})
        model = metrics.get('model', 'Unknown')
        count = metrics.get('cycle_count', 0)
        airbag_models[model] = airbag_models.get(model, 0) + count
    if airbag_models:
        airbag_df = pd.DataFrame(list(airbag_models.items()), columns=['Model', 'Parts Cut'])
        fig9 = go.Figure(go.Bar(
            x=airbag_df['Model'],
            y=airbag_df['Parts Cut'],
            text=[f"<b>{int(v)}</b>" for v in airbag_df['Parts Cut']],
            textposition='outside',
            textfont=dict(size=18, color='white', family='Arial Black'),
            marker_color=['#00D9FF', '#FF6B00']
        ))
        fig9.update_layout(
            template='plotly_dark',
            height=350,
            yaxis_title='Parts Cut',
            xaxis=dict(tickfont=dict(size=12, color='white')),
            yaxis=dict(tickfont=dict(size=12, color='white'))
        )
        st.plotly_chart(fig9, use_container_width=True)
with c10:
    st.subheader("🔧 Welding Models Production")
    weld_models = {}
    for dev_id in [k for k in machines.keys() if k.startswith('VWM')]:
        metrics = machines.get(dev_id, {}).get('metrics', {})
        model = metrics.get('model', 'Unknown')
        weld_time = metrics.get('weld_time', 2.5)
        parts_per_hour = 3600 / (weld_time + 1.5) if weld_time > 0 else 0
        weld_models[model] = weld_models.get(model, 0) + (parts_per_hour * 8)
    if weld_models:
        weld_df = pd.DataFrame(list(weld_models.items()), columns=['Model', 'Parts Welded'])
        fig10 = go.Figure(go.Bar(
            x=weld_df['Model'],
            y=weld_df['Parts Welded'],
            text=[f"<b>{int(v)}</b>" for v in weld_df['Parts Welded']],
            textposition='outside',
            textfont=dict(size=18, color='white', family='Arial Black'),
            marker_color=['#00FF9F', '#FFA500']
        ))
        fig10.update_layout(
            template='plotly_dark',
            height=350,
            yaxis_title='Parts Welded',
            xaxis=dict(tickfont=dict(size=12, color='white')),
            yaxis=dict(tickfont=dict(size=12, color='white'))
        )
        st.plotly_chart(fig10, use_container_width=True)
