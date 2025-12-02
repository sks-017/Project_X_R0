"""Alert Management System for Production Control System"""
import streamlit as st
from datetime import datetime
from typing import List, Dict
class Alert:
    def __init__(self, severity: str, machine: str, message: str, metric: str = "", value: float = 0):
        self.severity = severity
        self.machine = machine
        self.message = message
        self.metric = metric
        self.value = value
        self.timestamp = datetime.now()
    def to_dict(self):
        return {
            'severity': self.severity,
            'machine': self.machine,
            'message': self.message,
            'metric': self.metric,
            'value': self.value,
            'timestamp': self.timestamp.strftime('%H:%M:%S')
        }
class AlertSystem:
    def __init__(self):
        if 'alerts' not in st.session_state:
            st.session_state.alerts = []
        if 'alert_config' not in st.session_state:
            st.session_state.alert_config = {
                'cycle_time_threshold': 10.0,
                'temp_min': 180,
                'temp_max': 220,
                'enable_browser_notifications': True
            }
    def check_machine(self, dev_id: str, metrics: Dict) -> List[Alert]:
        """Check machine metrics and generate alerts"""
        alerts = []
        config = st.session_state.alert_config
        if dev_id.startswith('IMM') and 'cycle_time' in metrics:
            cycle_time = metrics['cycle_time']
            target = 35
            deviation = abs((cycle_time - target) / target * 100)
            if deviation > config['cycle_time_threshold']:
                alerts.append(Alert(
                    'warning',
                    dev_id,
                    f"Cycle time deviation: {deviation:.1f}%",
                    'cycle_time',
                    cycle_time
                ))
        if 'zone_temps' in metrics:
            for idx, temp in enumerate(metrics['zone_temps']):
                if temp < config['temp_min'] or temp > config['temp_max']:
                    alerts.append(Alert(
                        'critical',
                        dev_id,
                        f"Zone {idx+1} temp out of range: {temp:.0f}°C",
                        'zone_temp',
                        temp
                    ))
                    break
        if dev_id.startswith('IMM') and 'clamping_pressure' in metrics:
            pressure = metrics['clamping_pressure']
            if pressure < 1800 or pressure > 2500:
                alerts.append(Alert(
                    'warning',
                    dev_id,
                    f"Clamping pressure unusual: {pressure:.0f} ton",
                    'pressure',
                    pressure
                ))
        return alerts
    def add_alerts(self, new_alerts: List[Alert]):
        """Add new alerts to the session"""
        st.session_state.alerts.extend(new_alerts)
        st.session_state.alerts = st.session_state.alerts[-50:]
    def get_active_alerts(self, severity: str = None) -> List[Alert]:
        """Get active alerts, optionally filtered by severity"""
        if severity:
            return [a for a in st.session_state.alerts if a.severity == severity]
        return st.session_state.alerts
    def clear_alerts(self):
        """Clear all alerts"""
        st.session_state.alerts = []
    def render_alert_panel(self):
        """Render alert panel in sidebar"""
        alerts = self.get_active_alerts()
        critical = [a for a in alerts if a.severity == 'critical']
        warnings = [a for a in alerts if a.severity == 'warning']
        if critical:
            st.sidebar.error(f"🚨 {len(critical)} Critical Alerts")
        if warnings:
            st.sidebar.warning(f"⚠️ {len(warnings)} Warnings")
        if alerts:
            with st.sidebar.expander(f"Recent Alerts ({len(alerts)})"):
                for alert in reversed(alerts[-10:]):
                    icon = "🚨" if alert.severity == 'critical' else "⚠️"
                    st.caption(f"{icon} {alert.timestamp.strftime('%H:%M')} - {alert.machine}: {alert.message}")
                if st.button("Clear All Alerts"):
                    self.clear_alerts()
                    st.rerun()
