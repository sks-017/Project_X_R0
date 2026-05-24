"""
Acron TechMate AI Chat Assistant
RAG-based intelligent assistant querying live database telemetry, OEE, downtime, anomalies, and active alerts.
"""
import re
from datetime import datetime, timedelta
from app import models
from app.ml.health_score import compute_health_scores
from app.ml.anomaly import detect_anomalies

def get_oee_summary(db):
    cutoff = datetime.utcnow() - timedelta(hours=8)
    equipment = db.query(models.Equipment).filter_by(active=True).all()
    results = []
    for item in equipment:
        telemetry = db.query(models.Telemetry).filter(
            models.Telemetry.equipment_id == item.equipment_id,
            models.Telemetry.time >= cutoff,
        ).all()
        downtime_minutes = sum(
            event.minutes for event in db.query(models.DowntimeEvent).filter(
                models.DowntimeEvent.equipment_id == item.equipment_id,
                models.DowntimeEvent.started_at >= cutoff,
            ).all()
        )
        planned_minutes = max(8 * 60 - 30, 1)
        availability = max(0.0, min(1.0, (planned_minutes - downtime_minutes) / planned_minutes))
        cycle_values = [t.metric_value for t in telemetry if t.metric_name == "cycle_time" and t.metric_value]
        avg_cycle = sum(cycle_values) / len(cycle_values) if cycle_values else item.cycle_time_standard
        performance = max(0.0, min(1.0, item.cycle_time_standard / avg_cycle if avg_cycle else 1.0))
        quality = 0.98
        oee = availability * performance * quality
        results.append({
            "equipment_id": item.equipment_id,
            "availability": availability * 100,
            "performance": performance * 100,
            "quality": quality * 100,
            "oee": oee * 100
        })
    return results

def generate_chat_response(query: str, db) -> dict:
    query_lower = query.lower()
    
    # 1. Look for equipment mentioned in the query
    # E.g. IMM-01, QMC-02, CHILLER-03, ROBOT-04, TCM-01, VWM-01
    equipment_ids = re.findall(r'\b(?:imm|qmc|chiller|robot|tcm|vwm)-\d{2}\b', query_lower)
    equipment_ids = [eq.upper() for eq in equipment_ids]
    
    context_used = []
    response = ""
    
    if equipment_ids:
        eq_id = equipment_ids[0]
        context_used.append(f"Equipment Master for {eq_id}")
        eq = db.query(models.Equipment).filter_by(equipment_id=eq_id, active=True).first()
        if not eq:
            response = f"I found a reference to **{eq_id}** in your query, but it doesn't appear to be active or configured in the factory database. Please check the Machine Master page."
        else:
            # Let's fetch latest telemetry
            latest_telemetry = db.query(models.Telemetry).filter_by(equipment_id=eq_id).order_by(models.Telemetry.time.desc()).limit(20).all()
            # Let's calculate health score
            health_scores = compute_health_scores(db, hours=8)
            eq_health = next((h for h in health_scores if h["equipment_id"] == eq_id), None)
            
            # Let's get recent alerts
            alerts = db.query(models.Alert).filter_by(equipment_id=eq_id).order_by(models.Alert.created_at.desc()).limit(3).all()
            
            # Let's get recent downtime events
            downtimes = db.query(models.DowntimeEvent).filter_by(equipment_id=eq_id).order_by(models.DowntimeEvent.started_at.desc()).limit(3).all()
            
            # Formulate response
            response = f"### 🤖 TechMate Diagnostics for **{eq_id}**\n\n"
            response += f"**Description:** {eq.description or 'N/A'} | **Process:** {eq.process.name if eq.process else eq.equipment_type}\n"
            if eq.mold_model:
                response += f"**Current Mold:** `{eq.mold_model.model_code}` ({eq.mold_model.part_name})\n"
            response += f"**PLC Connection:** {eq.plc_protocol.upper()} via `{eq.plc_address}`\n\n"
            
            if eq_health:
                response += f"#### ❤️ Composite Health Score: **{eq_health['health_score']}/100**\n"
                response += f"- **OEE Component:** {eq_health['oee_component']}%\n"
                response += f"- **Stability Component:** {eq_health['stability_component']}%\n"
                response += f"- **Downtime Component:** {eq_health['downtime_component']}%\n\n"
            
            if latest_telemetry:
                response += "#### 📊 Recent Telemetry Readings:\n"
                seen_metrics = set()
                telemetry_lines = []
                for t in latest_telemetry:
                    if t.metric_name not in seen_metrics:
                        seen_metrics.add(t.metric_name)
                        telemetry_lines.append(f"- **{t.metric_name}:** {t.metric_value:.2f} (Status: `{t.status}`)")
                response += "\n".join(telemetry_lines) + "\n\n"
            
            if alerts:
                response += "#### ⚠️ Recent Alerts:\n"
                for a in alerts:
                    status_str = "Acknowledged" if a.acknowledged else "ACTIVE"
                    response += f"- **[{a.severity.upper()}]** {a.message} *({a.created_at.strftime('%Y-%m-%d %H:%M')}, status: {status_str})*\n"
                response += "\n"
            else:
                response += "#### ✅ Alerts: No active alerts detected for this equipment.\n\n"
                
            if downtimes:
                response += "#### 🛑 Recent Downtimes:\n"
                for d in downtimes:
                    response += f"- **{d.reason_code}** ({d.category}) for **{d.minutes} mins** - *{d.comment or 'No comment'}*\n"
            else:
                response += "#### ✅ Downtimes: No recent downtime events recorded.\n\n"
                
    elif "oee" in query_lower:
        context_used.append("Overall OEE calculations")
        oee_data = get_oee_summary(db)
        if oee_data:
            worst_oee = sorted(oee_data, key=lambda x: x["oee"])
            avg_oee = sum(x["oee"] for x in oee_data) / len(oee_data)
            
            response = f"### 📈 Factory OEE Report (Last 8 Hours)\n\n"
            response += f"Average plant OEE is currently **{avg_oee:.1f}%**. Target is **85.0%**.\n\n"
            response += "| Equipment | Availability | Performance | Quality | OEE |\n"
            response += "| :--- | :--- | :--- | :--- | :--- |\n"
            for o in worst_oee[:5]:
                response += f"| **{o['equipment_id']}** | {o['availability']:.1f}% | {o['performance']:.1f}% | {o['quality']:.1f}% | **{o['oee']:.1f}%** |\n"
            response += "\n*Only showing top 5 lowest OEE machines. Lower availability is usually caused by active downtime; lower performance indicates slow cycle times.*"
        else:
            response = "I couldn't calculate OEE data right now. Make sure the telemetry simulator is running and generating machine events."
            
    elif any(kw in query_lower for kw in ["downtime", "halt", "stop", "stoppage"]):
        context_used.append("Downtime events database")
        downtimes = db.query(models.DowntimeEvent).order_by(models.DowntimeEvent.started_at.desc()).limit(5).all()
        if downtimes:
            response = "### 🛑 Recent Downtime Events (Latest 5)\n\n"
            response += "| Machine | Reason | Category | Duration | Comment |\n"
            response += "| :--- | :--- | :--- | :--- | :--- |\n"
            for d in downtimes:
                response += f"| **{d.equipment_id}** | `{d.reason_code}` | {d.category} | **{d.minutes} mins** | {d.comment or '—'} |\n"
            response += "\nWould you like me to help troubleshoot a specific machine's downtime code?"
        else:
            response = "No recent downtime events have been recorded in the database. All machines are currently running normally."
            
    elif any(kw in query_lower for kw in ["anomaly", "anomalies", "issue", "problem", "outlier"]):
        context_used.append("AI anomaly detection database")
        anoms = detect_anomalies(db, hours=4)
        if anoms:
            response = "### 🔍 Detected Telemetry Anomalies (AI/ML)\n\n"
            response += f"I have detected **{len(anoms)} active anomalies** in the last 4 hours:\n\n"
            response += "| Machine | Metric | Value | Baseline Mean | Severity |\n"
            response += "| :--- | :--- | :--- | :--- | :--- |\n"
            for a in anoms:
                response += f"| **{a['equipment_id']}** | {a['metric']} | `{a['value']}` | {a['mean']} | **{a['severity'].upper()}** |\n"
            response += "\n*These anomalies are identified using an IsolationForest z-score algorithm. They point to abnormal machine cycles or temperature deviations.*"
        else:
            response = "### ✅ AI Anomaly Report\n\nNo telemetry anomalies detected in the last 4 hours. All readings are within normal operational envelopes."
            
    elif any(kw in query_lower for kw in ["alert", "alerts", "warning", "warnings"]):
        context_used.append("Active Alerts database")
        alerts = db.query(models.Alert).filter_by(acknowledged=False).order_by(models.Alert.created_at.desc()).limit(5).all()
        if alerts:
            response = "### ⚠️ Active Unacknowledged Alerts (Latest 5)\n\n"
            for a in alerts:
                response += f"- **{a.equipment_id}** ({a.severity.upper()}): {a.message} *(Created {a.created_at.strftime('%H:%M:%S')})*\n"
            response += "\nYou can acknowledge these alerts in the Command Center dashboard."
        else:
            response = "### ✅ Alerts Status\n\nAll alerts are currently acknowledged or resolved! The factory is running clear."
            
    elif "flash" in query_lower:
        context_used.append("Injection Molding troubleshooting guides - Flash")
        response = """### 🔧 TechMate Expert Guide: Troubleshooting Molding Flash

**Flash** is excess plastic that escapes the mold cavity at the parting line, venting slots, or ejector pins. 

#### Recommended Corrective Actions:
1. **Reduce Injection Pressure/Speed:** High injection pressure or speed can force the mold halves apart.
2. **Increase Clamp Force:** Ensure clamp tonnage matches the projected area of the part and mold. If clamping pressure is set too low (e.g., below 1800 tons on `IMM-01`), increase it.
3. **Optimize Melt and Mold Temperatures:** High melt temperatures reduce plastic viscosity, making it leak easily. Try decreasing mold temperature by 5-10°C.
4. **Inspect parting surfaces:** Check for plastic debris, wear, or damage on the parting line of the mold.
5. **Check Mold Alignment:** Inspect alignment pins and bushings for wear.
"""
    elif any(kw in query_lower for kw in ["short shot", "underfill"]):
        context_used.append("Injection Molding troubleshooting guides - Short Shot")
        response = """### 🔧 TechMate Expert Guide: Troubleshooting Short Shots

A **Short Shot** occurs when the mold cavity is not completely filled, resulting in a partial or incomplete part.

#### Recommended Corrective Actions:
1. **Increase Shot Size / Cushion:** Ensure there is enough material being fed and that a proper cushion (e.g., 5-10mm) is maintained at the end of injection.
2. **Increase Injection Speed/Pressure:** If the plastic freezes before reaching the far end of the mold, increasing injection speed will fill the cavity faster.
3. **Raise Melt or Mold Temperatures:** Increasing temperatures lowers viscosity, allowing the plastic to flow more easily.
4. **Clean/Add Vents:** Blocked venting prevents air from escaping, creating backpressure that blocks flow. Check venting channels.
5. **Verify Gate/Runner Layout:** Ensure gates are not frozen or restricted.
"""
    elif any(kw in query_lower for kw in ["warp", "warpage", "bending"]):
        context_used.append("Injection Molding troubleshooting guides - Warpage")
        response = """### 🔧 TechMate Expert Guide: Troubleshooting Warpage

**Warpage** is unwanted distortion/bending in the part, caused by non-uniform cooling rates and internal stress.

#### Recommended Corrective Actions:
1. **Adjust Cooling Time:** Extend cooling time to ensure the part is fully solidified and rigid before ejecting.
2. **Optimize Mold Temperature:** Ensure temperature difference between core and cavity is balanced.
3. **Reduce Injection and Packing Pressure:** High packing pressures can create high local stress near the gates, leading to warpage.
4. **Check Water Channel Flow:** Verify that chillers (like `CHILLER-01`) are delivering standard flow rate (~50 L/min) and temperature. A clogged cooling line is a common cause of uneven cooling.
"""
    elif any(kw in query_lower for kw in ["burn mark", "burns", "diesel effect"]):
        context_used.append("Injection Molding troubleshooting guides - Burn Marks")
        response = """### 🔧 TechMate Expert Guide: Troubleshooting Burn Marks

**Burn Marks** (diesel effect) are dark spots or gas burns on the part surface, caused by trapped air/gas that compresses, heats up, and burns the plastic.

#### Recommended Corrective Actions:
1. **Decrease Injection Speed:** Lowering injection speed allows trapped air to vent out before compressing and burning.
2. **Improve Venting:** Clean venting slots or add venting in areas where burn marks consistently occur (usually at the end of the flow path).
3. **Reduce Melt/Barrel Temperature:** Lowering the melt temperature prevents resin degradation and gas generation.
4. **Reduce Back Pressure:** Lowering back pressure during plastication helps prevent overheating the melt.
"""
    elif any(kw in query_lower for kw in ["list machines", "list equipment", "all machines", "equipment list"]):
        context_used.append("Equipment list")
        eqs = db.query(models.Equipment).filter_by(active=True).all()
        response = "### 🤖 Factory Equipment List\n\n"
        response += f"There are **{len(eqs)} active machines** registered in the system:\n\n"
        
        by_type = {}
        for eq in eqs:
            by_type.setdefault(eq.equipment_type, []).append(eq.equipment_id)
            
        for eq_type, ids in sorted(by_type.items()):
            response += f"- **{eq_type}:** {', '.join(sorted(ids))}\n"
            
        response += "\nAsk me about a specific machine (e.g. *'What is the health of IMM-01?'*) to see live telemetry, active alerts, and downtime logs."
    else:
        context_used.append("TechMate System Help")
        response = """### 👋 Welcome to **TechMate AI Assistant**!

I am your intelligent factory floor companion, built to help you monitor, analyze, and optimize production lines.

Here is what you can ask me:
1. **Live Machine Diagnostics:** *“What is the health of IMM-01?”* or *“Check status of CHILLER-02”*
2. **OEE Analytics:** *“What is our current OEE?”* or *“Which machines have the lowest performance?”*
3. **Factory Alarms:** *“Show active alerts”* or *“Are there any critical warnings?”*
4. **Telemetry Anomalies:** *“What are the latest anomalies?”* or *“Any outliers in temp?”*
5. **Molding Defect Troubleshooting:** *“How do I fix flash?”*, *“What causes short shots?”*, or *“How to reduce warpage?”*
6. **General List:** *“List all machines”*

How can I help you today? Let's keep the plant running efficiently! 🚀"""

    return {
        "response": response,
        "context_used": context_used
    }
