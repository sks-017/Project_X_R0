"""
Utility module for tooltips and help text
Provides consistent help information across all dashboards
"""
TOOLTIPS = {
    "active_assets": "🏭 Number of machines currently online and operational out of total installed equipment",
    "oee": "⚡ Overall Equipment Effectiveness = Availability × Performance × Quality. Industry target: >85%",
    "cycle_time": "⏱️ Average time to complete one production cycle. Lower is better. Target: 28-35 seconds",
    "parts_per_hour": "📦 Production rate measured in parts manufactured per hour. Target: 240 parts/hour",
    "availability": "🟢 Percentage of planned production time that equipment is actually running. Target: >90%",
    "performance": "🟠 Speed at which equipment operates vs ideal cycle time. Target: >85%",
    "quality": "🟢 Percentage of good parts vs total parts produced (FPY). Target: >95%",
    "mold_temp": "🌡️ Temperature of the mold during injection. Typical range: 55-65°C",
    "machine_temp": "🌡️ Machine barrel temperature. Typical range: 40-50°C",
    "clamping_pressure": "💪 Force applied to hold mold closed during injection. Range: 1800-2500 tons",
    "zone_temps": "🔥 Temperature zones (48 total) for precise heating control. Target: 180-220°C per zone",
    "mold_model": "🏷️ Specific mold installed in this IMM. Each model produces different parts",
    "inlet_temp": "🔵 Temperature of water entering from mold (warmer). Typical: 25-35°C",
    "outlet_temp": "🔵 Temperature of cooled water returning to mold. Typical: 12-25°C",
    "flow_rate": "💧 Water flow rate through cooling system. Target: ~50 L/min",
    "axis_x": "📍 Horizontal position of robot arm (0-1000mm)",
    "axis_y": "📍 Vertical position of robot arm (0-500mm)",
    "axis_z": "📍 Depth position of robot arm (0-800mm)",
    "grip_pressure": "🤏 Pressure applied by gripper to hold part. Target: ~5 bar",
    "fpy": "🎯 First Pass Yield - percentage of parts passing quality check first time. Target: >97%",
    "defects": "❌ Total number of defective parts in current period",
    "scrap_rate": "♻️ Percentage of parts scrapped due to defects. Target: <2%",
    "power_consumption": "⚡ Current power draw in kilowatts (kW)",
    "energy_cost": "💰 Estimated cost based on ₹0.12/kWh industrial rate",
    "carbon_footprint": "🌱 CO2 emissions in kg based on power consumption",
    "shift": "👨‍🏭 Current production shift: A (6am-2pm), B (2pm-10pm), C (10pm-6am)",
    "alert_critical": "🔴 Critical - Immediate action required. Production may be affected",
    "alert_warning": "🟡 Warning - Attention needed. Monitor closely",
    "alert_info": "🔵 Info - Notification only. No action required",
    "api_connection": "🔌 Real-time connection status to data ingestion API",
    "uptime": "⏰ System availability percentage over last 30 days",
    "data_freshness": "🕐 Time elapsed since last data update",
}
def get_tooltip(metric_key):
    """Get tooltip text for a metric"""
    return TOOLTIPS.get(metric_key, "ℹ️ No description available")
def add_help_icon(text, tooltip_key):
    """Add inline help icon with tooltip"""
    tooltip = get_tooltip(tooltip_key)
    return f"{text} ℹ️"
