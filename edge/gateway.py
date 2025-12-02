import time
import json
import os
import random
import requests
API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/telemetry")
DEVICES = []
for i in range(1, 9):
    DEVICES.append({"id": f"IMM-{i:02d}", "type": "IMM", "state": "RUNNING"})
for i in range(1, 9):
    DEVICES.append({"id": f"QMC-{i:02d}", "type": "QMC", "state": "PREHEAT"})
for i in range(1, 9):
    DEVICES.append({"id": f"CHILLER-{i:02d}", "type": "CHILLER", "state": "RUNNING"})
for i in range(1, 9):
    DEVICES.append({"id": f"ROBOT-{i:02d}", "type": "ROBOT", "state": "RUNNING"})
for i in range(1, 3):
    DEVICES.append({"id": f"TCM-{i:02d}", "type": "TCM", "state": "RUNNING"})
for i in range(1, 3):
    DEVICES.append({"id": f"VWM-{i:02d}", "type": "VWM", "state": "RUNNING"})
def generate_metrics(device):
    dtype = device["type"]
    device_id = device["id"]
    metrics = {}
    IMM_MODELS = {
        "IMM-01": "AB-X100",
        "IMM-02": "AB-X200", 
        "IMM-03": "AB-Y50",
        "IMM-04": "AB-Z99",
        "IMM-05": "AB-W150",
        "IMM-06": "AB-T300",
        "IMM-07": "AB-M75",
        "IMM-08": "AB-P200"
    }
    AIRBAG_MODELS = {
        "TCM-01": "IAB-CUT-A",
        "TCM-02": "IAB-CUT-B",
        "VWM-01": "IAB-WELD-X",
        "VWM-02": "IAB-WELD-Y"
    }
    if dtype == "IMM":
        metrics = {
            "cycle_time": random.uniform(28, 42),
            "mold_temp": random.normalvariate(60, 2.0),
            "machine_temp": random.normalvariate(45, 1.5),
            "clamping_pressure": random.uniform(1800, 2500),
            "vibration": random.random() * 0.2,
            "zone_temps": [random.uniform(180, 220) for _ in range(48)],
            "mold_model": IMM_MODELS.get(device_id, "UNKNOWN")
        }
    elif dtype == "QMC":
        metrics = {
            "temp": random.normalvariate(200, 5.0),
            "status": "PREHEATING",
            "zone_temps": [random.uniform(180, 220) for _ in range(48)]
        }
    elif dtype == "CHILLER":
        inlet_temp = random.uniform(25, 35)
        outlet_temp = inlet_temp - random.uniform(8, 15)
        metrics = {
            "water_temp": (inlet_temp + outlet_temp) / 2,
            "inlet_temp": inlet_temp,
            "outlet_temp": outlet_temp,
            "flow_rate": random.normalvariate(50, 2.0)
        }
    elif dtype == "ROBOT":
        metrics = {
            "axis_x": random.uniform(0, 1000),
            "axis_y": random.uniform(0, 500),
            "axis_z": random.uniform(0, 800),
            "grip_pressure": random.normalvariate(5, 0.1)
        }
    elif dtype == "TCM":
        metrics = {
            "cut_pressure": random.normalvariate(100, 5.0),
            "cycle_count": random.randint(0, 1000),
            "model": AIRBAG_MODELS.get(device_id, "UNKNOWN")
        }
    elif dtype == "VWM":
        metrics = {
            "weld_freq": random.normalvariate(20000, 100),
            "weld_time": random.normalvariate(2.5, 0.1),
            "model": AIRBAG_MODELS.get(device_id, "UNKNOWN")
        }
    return metrics
def main():
    print(f"Starting Edge Gateway for {len(DEVICES)} devices...")
    print("Batch mode enabled (sending every 5 seconds)")
    while True:
        batch_payload = []
        current_time = time.strftime("%Y-%m-%dT%H:%M:%S")
        for device in DEVICES:
            metrics = generate_metrics(device)
            batch_payload.append({
                "device_id": device["id"],
                "ts": current_time,
                "metrics": metrics,
                "meta": {"type": device["type"]}
            })
        try:
            with requests.Session() as session:
                for item in batch_payload:
                    session.post(API_URL, json=item, timeout=2.0)
            print(f"Sent batch of {len(batch_payload)} records at {current_time}")
        except requests.exceptions.ConnectTimeout:
            print(f"⚠️ Gateway timeout: API at {API_URL} did not respond in 2000ms")
            # TODO: Implement exponential backoff retry strategy for production resilience
        except requests.exceptions.ConnectionError:
            print("❌ Network unreachable. Check API server status or Ethernet connection.")
        except Exception as e:
            print(f"Error sending batch: {e}")
        time.sleep(5)
if __name__ == "__main__":
    main()
