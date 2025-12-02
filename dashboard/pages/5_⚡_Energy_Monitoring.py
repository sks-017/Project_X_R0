"""Energy Monitoring Dashboard - Production Control System"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
st.set_page_config(page_title="Energy Monitoring", page_icon="⚡", layout="wide")
st.title("⚡ Energy Monitoring Dashboard")
def generate_energy_data():
    machines = [f"IMM-{i:02d}" for i in range(1, 9)]
    power_kw = [random.uniform(45, 65) for _ in range(8)]
    return pd.DataFrame({
        'Machine': machines,
        'Power (kW)': power_kw,
        'Cost ($/hr)': [p * 0.12 for p in power_kw],
        'Daily Cost ($)': [p * 0.12 * 20 for p in power_kw]
    })
energy_data = generate_energy_data()
total_power = energy_data['Power (kW)'].sum()
total_cost = energy_data['Daily Cost ($)'].sum()
k1, k2, k3, k4 = st.columns(4)
k1.metric("Total Power", f"{total_power:.1f} kW")
k2.metric("Daily Cost", f"${total_cost:.2f}")
k3.metric("Avg Efficiency", "87.5%", delta="+1.2%")
k4.metric("Carbon (kg CO2)", f"{total_power * 0.5:.1f}", delta="-5.2")
st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    st.subheader("⚡ Power Consumption by Machine")
    fig1 = go.Figure(go.Bar(
        x=energy_data['Machine'],
        y=energy_data['Power (kW)'],
        text=[f"{v:.1f} kW" for v in energy_data['Power (kW)']],
        textposition='outside',
        marker_color='#00D9FF'
    ))
    fig1.update_layout(
        template='plotly_dark',
        height=400,
        yaxis_title='Power (kW)'
    )
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    st.subheader("💰 Daily Cost Distribution")
    fig2 = go.Figure(go.Pie(
        labels=energy_data['Machine'],
        values=energy_data['Daily Cost ($)'],
        hole=0.4
    ))
    fig2.update_layout(
        template='plotly_dark',
        height=400,
        annotations=[dict(text=f'${total_cost:.0f}<br>Total', x=0.5, y=0.5, font_size=16, showarrow=False)]
    )
    st.plotly_chart(fig2, use_container_width=True)
st.subheader("📈 Power Consumption Trend (24h)")
hours = pd.date_range(end=datetime.now(), periods=24, freq='H')
power_trend = pd.DataFrame({
    'Time': hours,
    'Power (kW)': [total_power * random.uniform(0.85, 1.15) for _ in range(24)]
})
fig3 = go.Figure(go.Scatter(
    x=power_trend['Time'],
    y=power_trend['Power (kW)'],
    mode='lines',
    fill='tozeroy',
    line=dict(color='#00FF9F', width=2)
))
fig3.update_layout(
    template='plotly_dark',
    height=300,
    yaxis_title='Total Power (kW)',
    hovermode='x unified'
)
st.plotly_chart(fig3, use_container_width=True)
st.subheader("🔍 Detailed Energy Metrics")
st.dataframe(energy_data, use_container_width=True)
