"""Data Export Utilities for Production Control System"""
import pandas as pd
import streamlit as st
from io import BytesIO
from datetime import datetime
def export_to_csv(data: pd.DataFrame, filename: str = "export"):
    """Export DataFrame to CSV and provide download button"""
    csv = data.to_csv(index=False)
    st.download_button(
        label="📥 Download CSV",
        data=csv,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )
def export_to_excel(data: pd.DataFrame, filename: str = "export"):
    """Export DataFrame to Excel and provide download button"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine='openpyxl') as writer:
        data.to_excel(writer, index=False, sheet_name='Data')
    excel_data = output.getvalue()
    st.download_button(
        label="📥 Download Excel",
        data=excel_data,
        file_name=f"{filename}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
def export_machine_data(machines: dict):
    """Export all machine data to DataFrame"""
    rows = []
    for dev_id, data in machines.items():
        metrics = data.get('metrics', {})
        row = {
            'Device': dev_id,
            'Timestamp': data.get('ts', ''),
        }
        for key, value in metrics.items():
            if key != 'zone_temps':
                row[key] = value
        rows.append(row)
    return pd.DataFrame(rows)
def export_alerts(alerts: list):
    """Export alerts to DataFrame"""
    if not alerts:
        return pd.DataFrame()
    rows = [a.to_dict() for a in alerts]
    return pd.DataFrame(rows)
