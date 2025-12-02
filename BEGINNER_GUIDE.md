# Beginner's Guide to Running the Production Control System

Welcome! This guide will help you run the Production Control System on your computer. The system now includes 6 powerful dashboards for complete factory monitoring.

## Prerequisites
You need to have **Python** installed.

## Step-by-Step Instructions

### Step 1: Open 2 Terminal Windows
1.  Press the `Windows Key` on your keyboard.
2.  Type `PowerShell` or `cmd` and press Enter.
3.  Repeat this 1 more time so you have **2 separate windows** open.

---

### Step 2: Start the "Brain" (The API)
In the **1st Window**, copy and paste these commands:

```powershell
cd C:\Users\91800\.gemini\antigravity\scratch
uvicorn andon_system.ingress-api.app.main:app --reload --port 8000
```
*You should see messages saying "Application startup complete". Keep this window open!*

---

### Step 3: Start the "Machine" (The Simulator)
In the **2nd Window**, copy and paste these commands:

```powershell
cd C:\Users\91800\.gemini\antigravity\scratch
python andon_system/edge/gateway.py
```
*You will see it printing messages about simulated cycles.*

---

### Step 4: Start the Dashboard
In the **same 2nd Window** (after starting the gateway, open a new terminal):

```powershell
cd C:\Users\91800\.gemini\antigravity\scratch\andon_system\dashboard
streamlit run Home.py
```
*This will automatically open your web browser to `http://localhost:8501`.*

---

### Step 5: Explore the Dashboards
The system now has **6 dashboards** accessible from the sidebar:

1. **Home** - Overview and quick stats
2. **📊 Executive Summary** - Production trends, OEE, downtime analysis
3. **🏭 Shop Floor** - All 8 production cells with real-time data
4. **👨‍🏭 Shift Analysis** - Shift comparison and performance
5. **🎯 Quality Dashboard** - Defect tracking and FPY
6. **⚡ Energy Monitoring** - Power consumption and costs
7. **🧵 Invisible Airbag Facility** - Assembly equipment

### Features:
- **Auto-Refresh**: Configure in sidebar (5s, 10s, 30s, 60s intervals)
- **Alerts**: Real-time notifications for out-of-range conditions
- **CSV Export**: Download button on each page
- **Interactive Charts**: Hover, zoom, and pan on all graphs

## Troubleshooting
- **"Command not found"**: Make sure you installed Python and added it to your PATH.
- **"Module not found"**: Run: `pip install fastapi uvicorn websockets streamlit requests plotly openpyxl`
