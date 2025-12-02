# 🏭 Real Machine Integration Guide

## Current State: Simulation vs Production

### What We Have Now (Demo Mode)
The current `edge/gateway.py` **simulates** machine data using Python's `random` library. This is perfect for:
- Demos and presentations
- Testing the dashboard
- Development without physical equipment

### What You Need for Production (Real Machines)
To connect to actual Injection Molding Machines, PLCs, and industrial equipment, you need to replace the simulation logic with **real data acquisition**.

---

## 📡 Industrial Data Acquisition Methods

### Option 1: OPC UA (Recommended for modern PLCs)
**What it is:** Open Platform Communications Unified Architecture - the industry standard for industrial IoT.

**Best for:**
- Siemens PLCs
- Rockwell Automation (Allen-Bradley)
- Beckhoff TwinCAT
- Modern Injection Molding Machines with embedded controllers

**Python Library:** `opcua` or `asyncua`

**Example Implementation:**
```python
from opcua import Client

# Replace gateway.py simulation with this
client = Client("opc.tcp://192.168.1.100:4840")  # PLC IP address
client.connect()

# Read nodes from PLC
imm_data = {
    "cycle_time": client.get_node("ns=2;s=IMM01.CycleTime").get_value(),
    "mold_temp": client.get_node("ns=2;s=IMM01.MoldTemp").get_value(),
    "zone_temps": [client.get_node(f"ns=2;s=IMM01.Zone{i}").get_value() for i in range(1, 49)]
}
```

---

### Option 2: Modbus TCP/RTU (Older PLCs & Legacy Equipment)
**What it is:** A simple master/slave protocol widely used in industrial automation.

**Best for:**
- Older PLCs (Schneider, Mitsubishi)
- Chillers, Temperature Controllers
- Legacy injection molding machines

**Python Library:** `pymodbus`

**Example Implementation:**
```python
from pymodbus.client import ModbusTcpClient

client = ModbusTcpClient('192.168.1.50', port=502)
client.connect()

# Read holding registers from PLC
cycle_time = client.read_holding_registers(address=0, count=1, slave=1).registers[0]
mold_temp = client.read_holding_registers(address=10, count=1, slave=1).registers[0] / 10.0
```

---

### Option 3: MQTT (IoT-First Approach)
**What it is:** Lightweight publish/subscribe messaging protocol.

**Best for:**
- Cloud-connected machines
- Remote monitoring (Factory A → Cloud → Dashboard in Office B)
- Modern "Industry 4.0" equipment with built-in MQTT

**Python Library:** `paho-mqtt`

**Example Implementation:**
```python
import paho.mqtt.client as mqtt

def on_message(client, userdata, msg):
    payload = json.loads(msg.payload)
    # Send payload to your FastAPI ingress
    requests.post("http://localhost:8000/api/v1/telemetry", json=payload)

mqtt_client = mqtt.Client()
mqtt_client.on_message = on_message
mqtt_client.connect("mqtt.factory.local", 1883)
mqtt_client.subscribe("factory/imm/#")
mqtt_client.loop_forever()
```

---

### Option 4: Direct PLC Ethernet (Proprietary Protocols)
**What it is:** Use manufacturer-specific SDKs.

**Examples:**
- **Siemens S7:** `python-snap7` library
- **Allen-Bradley Logix:** `pylogix` library
- **Mitsubishi:** `pymcprotocol`

---

## 🔌 Hardware Connection Setup

### Network Architecture
```
[PLC] ----Ethernet----> [Edge Gateway PC] ----HTTP----> [API Server]
  |                            |                            |
Reads                     Batches Data               Stores in DB
Sensors                   (gateway.py)              (SQLite/PostgreSQL)
```

### Typical Factory Network Setup
1. **Machine Network (OT Network):** PLCs communicate via Modbus/OPC UA
2. **Edge Gateway:** A small PC (Raspberry Pi, Industrial PC) running `gateway.py`
3. **IT Network:** Your FastAPI server and Dashboard

---

## 🛠️ Step-by-Step Real Integration

### Step 1: Identify Your Machine's Protocol
Ask your machine vendor or check the PLC documentation:
- What protocol does the PLC support? (OPC UA, Modbus, Profinet, etc.)
- What is the PLC's IP address?
- Which registers/tags hold the data you need?

### Step 2: Modify `edge/gateway.py`
Replace the simulation loop with real data acquisition:

**Before (Simulation):**
```python
# OLD: Simulated data
data = {
    "cycle_time": random.uniform(28, 35),
    "mold_temp": random.uniform(180, 220)
}
```

**After (Real OPC UA):**
```python
# NEW: Real data from PLC
from opcua import Client

plc = Client("opc.tcp://192.168.1.100:4840")
plc.connect()

data = {
    "cycle_time": plc.get_node("ns=2;s=IMM01.CycleTime").get_value(),
    "mold_temp": plc.get_node("ns=2;s=IMM01.MoldTemp").get_value()
}
```

### Step 3: Test Connection
Run the modified gateway and verify data appears in your dashboard.

### Step 4: Scale to All Machines
Add a configuration file (`machines.yaml`) to define all your PLCs:
```yaml
machines:
  - id: IMM-01
    ip: 192.168.1.100
    protocol: opcua
  - id: IMM-02
    ip: 192.168.1.101
    protocol: modbus
```

---

## 🚀 Quick Start: Connecting Your First Machine

1. **Install the library:**
   ```bash
   pip install opcua  # or pymodbus, or paho-mqtt
   ```

2. **Find your PLC's IP:**
   - Check the HMI screen on the machine
   - Use network scanning tools (e.g., `Advanced IP Scanner`)

3. **Test connection:**
   ```python
   from opcua import Client
   client = Client("opc.tcp://YOUR_PLC_IP:4840")
   client.connect()
   print("Connected!")
   ```

4. **Discover available data tags:**
   ```python
   root = client.get_root_node()
   for child in root.get_children():
       print(child.get_browse_name())
   ```

5. **Map tags to your data model and update `gateway.py`**

---

## 📋 Data You Can Collect from Real Machines

### Injection Molding Machines
- Cycle time, shot weight, injection pressure
- Barrel temperatures (zones 1-8)
- Mold temperatures (48 zones)
- Clamp tonnage, screw position
- Alarms and error codes

### PLCs
- Digital I/O states (machine running, door open)
- Analog values (temperatures, pressures, flow rates)
- Production counters

### SCADA Systems
- Aggregate production data
- Shift reports
- Historical logs

---

## 💡 Pro Tips

1. **Use a Data Historian (Optional):** Tools like InfluxDB can buffer data if your API is down.
2. **Security:** Keep the OT network isolated. Use a firewall between factory floor and IT network.
3. **Edge Computing:** Run the gateway on an industrial PC close to the machines (low latency).
4. **Failover:** If the API is unreachable, store data locally and upload when back online.

---

**Need Help?** Contact your machine vendor for:
- PLC IP addresses and credentials
- Protocol documentation (OPC UA namespaces, Modbus register maps)
- Firewall rules to allow communication
