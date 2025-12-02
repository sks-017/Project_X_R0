"""Quality Dashboard - Production Control System"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.quality_metrics import QualityTracker
st.set_page_config(page_title="Quality Dashboard", page_icon="🎯", layout="wide")
st.title("🎯 Quality Management Dashboard")
qt = QualityTracker()
quality_data = qt.generate_mock_defects()
k1, k2, k3, k4 = st.columns(4)
k1.metric("First Pass Yield", f"{quality_data['fpy']:.2f}%", delta="+0.8%")
k2.metric("Total Parts", quality_data['total_parts'])
k3.metric("Total Defects", quality_data['total_defects'], delta="-5")
k4.metric("Scrap Rate", f"{quality_data['scrap_rate']:.2f}%", delta="-0.1%")
st.markdown("---")
c1, c2 = st.columns(2)
with c1:
    st.subheader("📊 Defect Pareto Chart")
    defects = quality_data['defect_breakdown']
    sorted_defects = sorted(defects.items(), key=lambda x: x[1], reverse=True)
    df_defects = pd.DataFrame(sorted_defects, columns=['Type', 'Count'])
    df_defects['Cumulative %'] = (df_defects['Count'].cumsum() / df_defects['Count'].sum() * 100)
    fig1 = go.Figure()
    fig1.add_trace(go.Bar(name='Count', x=df_defects['Type'], y=df_defects['Count'], 
                          marker_color='#FF6B00', yaxis='y'))
    fig1.add_trace(go.Scatter(name='Cumulative %', x=df_defects['Type'], y=df_defects['Cumulative %'],
                              mode='lines+markers', marker_color='#00D9FF', yaxis='y2'))
    fig1.update_layout(
        template='plotly_dark',
        height=400,
        yaxis=dict(title='Defect Count'),
        yaxis2=dict(title='Cumulative %', overlaying='y', side='right', range=[0, 100])
    )
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    st.subheader("📈 Quality Trend (24h)")
    quality_trend = qt.generate_hourly_quality_data()
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=quality_trend['Time'], y=quality_trend['FPY %'],
                              mode='lines+markers', name='FPY %',
                              line=dict(color='#00FF9F', width=3)))
    fig2.add_hline(y=95, line_dash="dash", line_color="#FF6B00", annotation_text="Target: 95%")
    fig2.update_layout(
        template='plotly_dark',
        height=400,
        yaxis_range=[90, 100],
        yaxis_title='First Pass Yield (%)',
        hovermode='x unified'
    )
    st.plotly_chart(fig2, use_container_width=True)
st.subheader("🔍 Defect Breakdown")
st.dataframe(df_defects, use_container_width=True)
