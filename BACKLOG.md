# Acron Automated Feature Backlog

This backlog is used by the daily feature agent to implement new enhancements and features sequentially.

---

## 📋 Feature Backlog List

### 1. Digital Twin 2.5D/3D SVG Floor Plan
- **Description:** Implement a visual factory floor plan page showing machine tiles in their relative physical positions.
- **Backend:** Add a floor layout API `/api/v1/factory/layout` returning coordinates and state mapping.
- **Frontend:** Create `FloorPlan.jsx` rendering interactive SVG layouts of Molding Line A & B. Highlight machine nodes in green, amber, or red depending on their live health status.

### 2. Bayesian Fault Prediction Engine
- **Description:** Create a predictive maintenance page calculating specific equipment failure modes.
- **Backend:** Implement `ingress-api/app/ml/fault_prediction.py` calculating conditional probabilities using Bayes' Theorem (prior failure rates * current telemetry z-scores). Expose via `/api/v1/ai/predictions`.
- **Frontend:** Add a predictive maintenance panel in AI Insights or a new tab showing risk levels for heater bands, valves, and clamping jaws.

### 3. Energy Intensity Analytics (OEE/Power ratio)
- **Description:** Add energy telemetry tracking and efficiency calculation.
- **Backend:** Update the telemetry simulator to generate power readings (kW, voltage, power factor). Create `/api/v1/analytics/energy` returning energy-per-part ratio.
- **Frontend:** Add energy charts showing power consumption trends and identifying energy-hogging cycles.

### 4. Shift Performance Reports
- **Description:** Allow managers to analyze OEE performance grouped by shift (Shift A: 06:00-14:00, Shift B: 14:00-22:00, Shift C: 22:00-06:00).
- **Backend:** Create `/api/v1/analytics/shifts` endpoint calculating shift OEE aggregations.
- **Frontend:** Add shift selector and comparison charts in the Analytics tab.

### 5. Custom Alert Notification Rules
- **Description:** Allow supervisors to set up alerts and escalation protocols in settings.
- **Backend:** Implement alert rules CRUD under `/api/v1/alerts/rules`.
- **Frontend:** Build a rule builder in the Settings page to add rules (e.g., "If `clamping_pressure` > `2400` for `IMM-02` send Critical alert").
