# Architecture

## High-Level Overview
```
[PLC/Sensor] -> [Edge Gateway] -> (MQTT/HTTP) -> [Ingress API] -> [TimescaleDB]
                                                      |
                                                      v
                                                 [Dashboard] (WebSocket)
```

## Data Flow
1. **Telemetry**: Edge devices read sensors and push JSON payloads to the Ingress API.
2. **Ingestion**: API validates data and broadcasts it via WebSockets.
3. **Storage**: Data is stored in TimescaleDB for historical analysis.
4. **Visualization**: React Dashboard subscribes to WebSockets and updates the UI in real-time.
