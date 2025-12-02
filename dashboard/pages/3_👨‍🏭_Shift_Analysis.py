"""Shift Analysis Dashboard - Production Control System"""
import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
import random
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from utils.quality_metrics import QualityTracker
st.set_page_config(page_title="Shift Analysis", page_icon="👨‍🏭", layout="wide")
st.title("👨‍🏭 Shift Analysis Dashboard")
shift_col, date_col = st.columns(2)
with shift_col:
    selected_shift = st.selectbox("Select Shift", ["All Shifts", "A Shift", "B Shift", "C Shift"])
with date_col:
    analysis_date = st.date_input("Date", datetime.now())
st.subheader("📊 Shift Performance Comparison")
shifts = ['A', 'B', 'C']
shift_data = []
qt = QualityTracker()
for shift in shifts:
    quality = qt.calculate_shift_quality(shift)
    shift_data.append({
        'Shift': f"{shift} Shift",
        'Parts Produced': quality['parts'],
        'Defects': quality['defects'],
        'FPY %': quality['fpy'],
        'OEE %': random.uniform(85, 95),
        'Avg Cycle (s)': random.uniform(30, 38)
    })
df_shifts = pd.DataFrame(shift_data)
col1, col2, col3 = st.columns(3)
for idx, shift in enumerate(['A', 'B', 'C']):
    with [col1, col2, col3][idx]:
        st.metric(
            f"{shift} Shift Parts",
            f"{df_shifts.iloc[idx]['Parts Produced']}",
            delta=f"{df_shifts.iloc[idx]['FPY %']:.1f}% FPY"
        )
c1, c2 = st.columns(2)
with c1:
    st.subheader("Production by Shift")
    fig1 = go.Figure(go.Bar(
        x=df_shifts['Shift'],
        y=df_shifts['Parts Produced'],
        text=df_shifts['Parts Produced'],
        textposition='outside',
        marker_color=['#00D9FF', '#FF6B00', '#00FF9F']
    ))
    fig1.update_layout(template='plotly_dark', height=400, yaxis_title='Parts Produced')
    st.plotly_chart(fig1, use_container_width=True)
with c2:
    st.subheader("OEE Comparison")
    fig2 = go.Figure(go.Bar(
        x=df_shifts['Shift'],
        y=df_shifts['OEE %'],
        text=[f"{v:.1f}%" for v in df_shifts['OEE %']],
        textposition='outside',
        marker_color=['#00D9FF', '#FF6B00', '#00FF9F']
    ))
    fig2.update_layout(template='plotly_dark', height=400, yaxis_range=[0, 100], yaxis_title='OEE %')
    st.plotly_chart(fig2, use_container_width=True)
st.subheader("Detailed Shift Metrics")
st.dataframe(df_shifts, use_container_width=True)
