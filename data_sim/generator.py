import time
import json
import random
import requests
import os

API_URL = os.getenv("API_URL", "http://localhost:8000/api/v1/telemetry")

def generate_telemetry():
    while True:
        payload = {
            'device_id': 'mold-01',
            'ts': time.strftime('%Y-%m-%dT%H:%M:%S'),
            'metrics': {
                'cycle_time': random.normalvariate(12, 0.5),
                'mold_temp': random.normalvariate(60, 0.6),
                'chiller_delta': random.normalvariate(2.5, 0.2),
                'vibration': random.random() * 0.2
            }
        }
        try:
            requests.post(API_URL, json=payload, timeout=2)
            print(f"Generated: {payload['metrics']}")
        except Exception as e:
            print(f"Error: {e}")
        time.sleep(1)

if __name__ == "__main__":
    print("Starting Data Generator...")
    generate_telemetry()
