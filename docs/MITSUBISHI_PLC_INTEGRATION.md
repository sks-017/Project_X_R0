# 🔧 Mitsubishi R Series PLC Integration Guide

## Overview
Mitsubishi R Series PLCs communicate using the **MC Protocol** (MELSEC Communication Protocol) over Ethernet. This guide shows you how to replace the simulated data in `edge/gateway.py` with real data from your PLCs.

---

## 📦 Required Library

### Install pymcprotocol
```bash
pip install pymcprotocol
```

**Library:** [pymcprotocol](https://github.com/yuyuvn/pymcprotocol)  
**Supported PLCs:** R Series (RJ71, R04, R16, etc.), Q Series, L Series

---

## 🌐 Network Setup

### PLC Configuration
1. **Enable Ethernet Module:** Your R Series PLC should have an Ethernet module (e.g., RJ71EN71)
2. **Set IP Address:** Assign a static IP (e.g., `192.168.1.100`)
3. **Protocol:** Use MC Protocol (Binary mode or ASCII mode)
4. **Port:** Default is `5007` for binary, `5008` for ASCII

### Find Your PLC IP
- Check GX Works3 project settings
- Look at the PLC's Ethernet module label
- Use Mitsubishi's "PLC Scanner" software

---

## 💻 Implementation: Replace gateway.py Simulation

### Step 1: Basic Connection Test
Create a test script to verify connectivity:

```python
from pymcprotocol import Type3E

# Connect to PLC
plc = Type3E()
plc.connect("192.168.1.100", 5007)  # Replace with your PLC IP

# Read a single register (D0)
value = plc.batchread_wordunits(headdevice="D0", readsize=1)
print(f"D0 Value: {value[0]}")

plc.close()
```

### Step 2: Modified gateway.py for Real Data

Replace the simulation loop in `edge/gateway.py`:

```python
import requests
import time
from pymcprotocol import Type3E

# PLC Configuration
PLC_IP = "192.168.1.100"
PLC_PORT = 5007
API_URL = "http://localhost:8000/api/v1/telemetry"

# Connect to Mitsubishi PLC
plc = Type3E()
plc.connect(PLC_IP, PLC_PORT)

print(f"Connected to Mitsubishi R Series PLC at {PLC_IP}")

# Main data collection loop
while True:
    try:
        # Read data from PLC registers
        # Adjust device addresses based on your PLC program
        
        # Example: Read IMM-01 data from D registers
        imm01_data = plc.batchread_wordunits(headdevice="D100", readsize=10)
        
        telemetry = {
            "device_id": "IMM-01",
            "timestamp": time.time(),
            "metrics": {
                "cycle_time": imm01_data[0] / 10.0,      # D100: Cycle time (scaled)
                "mold_temp": imm01_data[1] / 10.0,       # D101: Mold temp
                "injection_pressure": imm01_data[2],     # D102: Pressure
                "clamping_pressure": imm01_data[3],      # D103: Clamp force
                "shot_weight": imm01_data[4] / 100.0,    # D104: Weight
                "mold_model": f"AB-X{imm01_data[5]}",    # D105: Model ID
                "status": "running" if imm01_data[6] == 1 else "idle"  # D106: Status
            }
        }
        
        # Send to API
        response = requests.post(API_URL, json=telemetry, timeout=2.0)
        if response.status_code == 200:
            print(f"✅ Sent telemetry for IMM-01")
        
        time.sleep(5)  # Batch interval
        
    except Exception as e:
        print(f"❌ Error: {e}")
        time.sleep(5)
        # Try reconnecting
        try:
            plc.close()
            plc.connect(PLC_IP, PLC_PORT)
        except:
            pass
```

### Step 3: Reading Multiple Machines

```python
# Configuration for multiple PLCs
MACHINES = [
    {"id": "IMM-01", "ip": "192.168.1.100", "start_reg": "D100"},
    {"id": "IMM-02", "ip": "192.168.1.101", "start_reg": "D100"},
    {"id": "IMM-03", "ip": "192.168.1.102", "start_reg": "D100"},
]

plc_connections = {}

# Connect to all PLCs
for machine in MACHINES:
    plc = Type3E()
    plc.connect(machine["ip"], 5007)
    plc_connections[machine["id"]] = plc

# Read from all machines
while True:
    batch_payload = []
    
    for machine in MACHINES:
        plc = plc_connections[machine["id"]]
        data = plc.batchread_wordunits(headdevice=machine["start_reg"], readsize=10)
        
        batch_payload.append({
            "device_id": machine["id"],
            "timestamp": time.time(),
            "metrics": {
                "cycle_time": data[0] / 10.0,
                "mold_temp": data[1] / 10.0,
                # ... rest of metrics
            }
        })
    
    # Send batch to API
    requests.post(f"{API_URL}/batch", json=batch_payload)
    time.sleep(5)
```

---

## 📋 Mitsubishi Device Address Reference

### Common Device Types in R Series
| Device | Description | Example |
|--------|-------------|---------|
| **D** | Data registers (16-bit) | `D0`, `D100`, `D1000` |
| **W** | Link registers | `W0`, `W100` |
| **R** | File registers | `R0`, `R1000` |
| **M** | Internal relays (bits) | `M0`, `M100` |
| **X** | Input relays | `X0`, `X10` |
| **Y** | Output relays | `Y0`, `Y10` |

### Example PLC Program Mapping
Ask your PLC programmer which addresses store your machine data:

```
D100: IMM-01 Cycle Time (in 0.1 sec units)
D101: IMM-01 Mold Temperature (in 0.1°C units)
D102: IMM-01 Injection Pressure (bar)
D103: IMM-01 Clamp Force (tons)
D104: IMM-01 Shot Weight (in 0.01g units)
D105: IMM-01 Current Model Number
D106: IMM-01 Status (0=idle, 1=running, 2=alarm)
D150: IMM-02 Cycle Time
D151: IMM-02 Mold Temperature
... (repeat for each machine)
```

---

## 🛠️ Reading Temperature Zones (48 Zones)

If your PLC stores all 48 zone temperatures:

```python
# Read 48 consecutive registers starting at D200
zone_temps = plc.batchread_wordunits(headdevice="D200", readsize=48)

# Scale values (if stored as D200=1850 means 185.0°C)
zone_temps_scaled = [temp / 10.0 for temp in zone_temps]

telemetry["metrics"]["zone_temps"] = zone_temps_scaled
```

---

## 🔍 Debugging Tips

### Test Connection
```python
from pymcprotocol import Type3E

plc = Type3E()
try:
    plc.connect("192.168.1.100", 5007)
    print("✅ PLC Connected!")
    
    # Read device D0
    value = plc.batchread_wordunits(headdevice="D0", readsize=1)
    print(f"D0 = {value[0]}")
    
except Exception as e:
    print(f"❌ Connection failed: {e}")
    print("Check: IP address, port, firewall, PLC power")
```

### Common Issues
| Error | Solution |
|-------|----------|
| `Connection refused` | Check PLC IP, ensure Ethernet module is powered |
| `Timeout` | Verify port 5007 is not blocked by firewall |
| `Invalid device` | Double-check device address (e.g., use `D100` not `d100`) |

---

## 📖 Next Steps

1. **Contact your PLC programmer** and ask for:
   - PLC IP address
   - Register map (which D registers store what data)
   - Scaling factors (e.g., D100=350 means 35.0 seconds)

2. **Test the connection** using the test script above

3. **Replace gateway.py** with the real PLC reading code

4. **Verify dashboard** shows live data from machines

---

## 🔗 Resources
- [pymcprotocol GitHub](https://github.com/yuyuvn/pymcprotocol)
- [Mitsubishi MC Protocol Manual](https://www.mitsubishielectric.com/fa/document/manual/)
- Your PLC's GX Works3 project file (contains register layout)
