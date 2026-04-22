from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .schemas import (
    TelemetryInput,
    EquipmentResponse,
    AlertCreate,
    AlertResponse,
    UserCreate,
    UserResponse,
    Token,
    DemoLogin,
    DowntimeCreate,
    MachineSetup,
    OeeResponse,
)
from . import models, auth
from .database import engine, get_db, init_db, check_db_connection, SessionLocal
from datetime import datetime, timedelta
import json
import asyncio
import os
import random

APP_NAME = "GE Pulse"
BRAND_OWNER = "S7 Inc"
TAGLINE = "Factory rhythm, clear."
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
SIMULATOR_ENABLED = os.getenv("SIMULATOR_ENABLED", "true").lower() == "true"
DEMO_ROLES = ["admin", "manager", "supervisor", "maintenance", "operator"]

app = FastAPI(title=f"{APP_NAME} API", version="1.0")

DEVICES = []
for i in range(1, 9): DEVICES.append({"id": f"IMM-{i:02d}", "type": "IMM"})
for i in range(1, 9): DEVICES.append({"id": f"QMC-{i:02d}", "type": "QMC"})
for i in range(1, 9): DEVICES.append({"id": f"CHILLER-{i:02d}", "type": "CHILLER"})
for i in range(1, 9): DEVICES.append({"id": f"ROBOT-{i:02d}", "type": "ROBOT"})
for i in range(1, 3): DEVICES.append({"id": f"TCM-{i:02d}", "type": "TCM"})
for i in range(1, 3): DEVICES.append({"id": f"VWM-{i:02d}", "type": "VWM"})

def generate_metrics(device):
    dtype = device["type"]
    device_id = device["id"]
    metrics = {}
    IMM_MODELS = {"IMM-01": "AB-X100", "IMM-02": "AB-X200", "IMM-03": "AB-Y50", "IMM-04": "AB-Z99", "IMM-05": "AB-W150", "IMM-06": "AB-T300", "IMM-07": "AB-M75", "IMM-08": "AB-P200"}
    PROCESS_MODELS = {"TCM-01": "IAB-CUT-A", "TCM-02": "IAB-CUT-B", "VWM-01": "IAB-WELD-X", "VWM-02": "IAB-WELD-Y"}
    if dtype == "IMM":
        metrics = {"cycle_time": random.uniform(28, 42), "mold_temp": random.normalvariate(60, 2.0), "machine_temp": random.normalvariate(45, 1.5), "clamping_pressure": random.uniform(1800, 2500), "vibration": random.random() * 0.2, "zone_temps": [random.uniform(180, 220) for _ in range(48)], "mold_model": IMM_MODELS.get(device_id, "UNKNOWN")}
    elif dtype == "QMC":
        metrics = {"temp": random.normalvariate(200, 5.0), "status": "PREHEATING", "zone_temps": [random.uniform(180, 220) for _ in range(48)]}
    elif dtype == "CHILLER":
        inlet_temp = random.uniform(25, 35)
        outlet_temp = inlet_temp - random.uniform(8, 15)
        metrics = {"water_temp": (inlet_temp + outlet_temp) / 2, "inlet_temp": inlet_temp, "outlet_temp": outlet_temp, "flow_rate": random.normalvariate(50, 2.0)}
    elif dtype == "ROBOT":
        metrics = {"axis_x": random.uniform(0, 1000), "axis_y": random.uniform(0, 500), "axis_z": random.uniform(0, 800), "grip_pressure": random.normalvariate(5, 0.1)}
    elif dtype == "TCM":
        metrics = {"cut_pressure": random.normalvariate(100, 5.0), "cycle_count": random.randint(0, 1000), "model": PROCESS_MODELS.get(device_id, "UNKNOWN")}
    elif dtype == "VWM":
        metrics = {"weld_freq": random.normalvariate(20000, 100), "weld_time": random.normalvariate(2.5, 0.1), "model": PROCESS_MODELS.get(device_id, "UNKNOWN")}
    return metrics

latest_telemetry = {}

class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass

manager = ConnectionManager()

async def background_simulator_loop():
    while True:
        try:
            current_time = datetime.utcnow().isoformat() + "Z"
            db = SessionLocal()
            for device in DEVICES:
                metrics = generate_metrics(device)
                
                payload = {
                    "device_id": device["id"],
                    "ts": current_time,
                    "metrics": metrics,
                    "meta": {"type": device["type"]}
                }
                
                latest_telemetry[device["id"]] = payload
                
                await manager.broadcast(json.dumps({
                    "type": "telemetry",
                    "data": payload
                }))
                
                timestamp = datetime.utcnow()
                for metric_name, metric_value in metrics.items():
                    if isinstance(metric_value, list):
                        continue
                    if isinstance(metric_value, (int, float)):
                        telemetry_record = models.Telemetry(
                            time=timestamp,
                            equipment_id=device["id"],
                            metric_name=metric_name,
                            metric_value=float(metric_value),
                            status="normal"
                        )
                        db.add(telemetry_record)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Simulator error: {e}")
        await asyncio.sleep(5.0)

def _get_or_create(db, model, defaults=None, **filters):
    instance = db.query(model).filter_by(**filters).first()
    if instance:
        return instance
    params = dict(filters)
    params.update(defaults or {})
    instance = model(**params)
    db.add(instance)
    db.flush()
    return instance

def seed_database(reset: bool = False):
    db = SessionLocal()
    try:
        if reset:
            db.query(models.DowntimeEvent).delete()
            db.query(models.TargetStandard).delete()
            db.query(models.ShiftCalendar).delete()
            db.query(models.AlertRule).delete()
            db.query(models.ConnectorConfig).delete()
            db.query(models.Telemetry).delete()
            db.query(models.Alert).delete()
            db.query(models.Equipment).delete()
            db.query(models.MoldModel).delete()
            db.query(models.Process).delete()
            db.query(models.Cell).delete()
            db.query(models.Line).delete()
            db.query(models.Plant).delete()
            db.query(models.Company).delete()
            db.commit()

        company = _get_or_create(db, models.Company, name="S7 Inc")
        plant = _get_or_create(
            db,
            models.Plant,
            company_id=company.id,
            code="S7-PUNE-01",
            defaults={"name": "Pune Automotive Components Plant"},
        )
        line_a = _get_or_create(db, models.Line, plant_id=plant.id, code="LINE-A", defaults={"name": "Molding Line A"})
        line_b = _get_or_create(db, models.Line, plant_id=plant.id, code="LINE-B", defaults={"name": "Bumper Line B"})
        molding = _get_or_create(db, models.Process, code="IMM", defaults={"name": "Injection Molding"})
        qmc = _get_or_create(db, models.Process, code="QMC", defaults={"name": "Quick Mold Change"})
        chilling = _get_or_create(db, models.Process, code="CHILLER", defaults={"name": "Cooling"})
        robot = _get_or_create(db, models.Process, code="ROBOT", defaults={"name": "Take-out Robot"})
        cutting = _get_or_create(db, models.Process, code="TCM", defaults={"name": "Trimming/Cutting"})
        welding = _get_or_create(db, models.Process, code="VWM", defaults={"name": "Vibration Welding"})

        mold_models = {}
        for device_id, model_code in {
            "IMM-01": "AB-X100", "IMM-02": "AB-X200", "IMM-03": "AB-Y50", "IMM-04": "AB-Z99",
            "IMM-05": "AB-W150", "IMM-06": "AB-T300", "IMM-07": "AB-M75", "IMM-08": "AB-P200",
        }.items():
            mold_models[device_id] = _get_or_create(
                db,
                models.MoldModel,
                model_code=model_code,
                defaults={"part_name": f"Automotive bumper component {model_code}", "standard_cycle_time": 35.0, "cavity_count": 1},
            )

        demo_admin_password = os.getenv("DEMO_ADMIN_PASSWORD", "admin123")
        for role in DEMO_ROLES:
            username = "admin" if role == "admin" else role
            demo_user = db.query(models.User).filter(models.User.username == username).first()
            if not demo_user:
                demo_user = models.User(username=username, email=f"{username}@demo.gepulse.local", password_hash="", role=role)
                db.add(demo_user)
            demo_user.email = "admin@example.com" if role == "admin" else f"{username}@demo.gepulse.local"
            demo_user.password_hash = auth.get_password_hash(demo_admin_password)
            demo_user.role = role
            demo_user.active = True
            demo_user.session_timeout_minutes = auth.ACCESS_TOKEN_EXPIRE_MINUTES

        print("[INIT] Seeding equipment...")
        for device in DEVICES:
            cell_number = device["id"].split("-")[-1] if "-" in device["id"] else "01"
            line = line_a if int(cell_number) <= 4 else line_b
            cell = _get_or_create(
                db,
                models.Cell,
                line_id=line.id,
                code=f"CELL-{cell_number}",
                defaults={"name": f"Cell {cell_number}"},
            )
            process = {
                "IMM": molding,
                "QMC": qmc,
                "CHILLER": chilling,
                "ROBOT": robot,
                "TCM": cutting,
                "VWM": welding,
            }.get(device["type"], molding)
            equipment = db.query(models.Equipment).filter(
                models.Equipment.equipment_id == device["id"]
            ).first()
            if equipment:
                equipment.equipment_type = device["type"]
                equipment.description = f"{device['type']} Unit {device['id'].split('-')[-1]}"
                equipment.active = True
            else:
                eq = models.Equipment(
                    equipment_id=device["id"],
                    equipment_type=device["type"],
                    description=f"{device['type']} Unit {device['id'].split('-')[-1]}",
                    active=True
                )
                db.add(eq)
                equipment = eq
            equipment.cell_id = cell.id
            equipment.process_id = process.id
            equipment.mold_model_id = mold_models.get(device["id"]).id if device["id"] in mold_models else None
            equipment.plc_protocol = "mitsubishi_mc" if device["type"] == "IMM" else "simulator"
            equipment.plc_address = f"192.168.10.{10 + len(device['id'])}"
            equipment.cycle_time_standard = 35.0 if device["type"] == "IMM" else 30.0
            equipment.target_per_hour = 240 if device["type"] == "IMM" else 180

        for shift_name, starts_at, ends_at in [("A", "06:00", "14:00"), ("B", "14:00", "22:00"), ("C", "22:00", "06:00")]:
            _get_or_create(
                db,
                models.ShiftCalendar,
                plant_id=plant.id,
                shift_name=shift_name,
                defaults={"starts_at": starts_at, "ends_at": ends_at, "planned_downtime_minutes": 30},
            )

        for rule_name, metric_name, condition, threshold, severity, minutes, role in [
            ("Cycle delay", "cycle_time", "gt", 42, "warning", 5, "supervisor"),
            ("Temperature deviation", "mold_temp", "gt", 70, "critical", 15, "maintenance"),
            ("High vibration", "vibration", "gt", 0.18, "critical", 30, "manager"),
            ("Low OEE", "oee", "lt", 75, "warning", 30, "manager"),
        ]:
            _get_or_create(
                db,
                models.AlertRule,
                name=rule_name,
                defaults={
                    "metric_name": metric_name,
                    "condition": condition,
                    "threshold": threshold,
                    "severity": severity,
                    "escalation_minutes": minutes,
                    "target_role": role,
                    "channels": ["email", "teams"],
                },
            )

        for protocol, endpoint in [
            ("mitsubishi_mc", "192.168.10.20:5007"),
            ("modbus_tcp", "192.168.10.21:502"),
            ("opc_ua", "opc.tcp://192.168.10.22:4840"),
            ("mqtt", "mqtt://broker.local:1883/ge-pulse"),
        ]:
            _get_or_create(
                db,
                models.ConnectorConfig,
                name=f"demo-{protocol}",
                defaults={"protocol": protocol, "endpoint": endpoint, "tag_map": {"cycle_time": "D100", "status": "D101"}},
            )

        db.commit()
        print("[INIT] Demo users, factory master, and equipment seeded successfully.")
    except Exception as e:
        print(f"Failed to seed DB: {e}")
    finally:
        db.close()

@app.on_event("startup")
async def startup():
    try:
        if check_db_connection():
            models.Base.metadata.create_all(bind=engine)
            print("[OK] Database initialized")
            seed_database()
            print("[OK] Database connection successful")
        else:
            print("[WARN] Database not available - running in memory-only mode")
    except Exception as e:
        print(f"[WARN] Database initialization failed: {e}")
        print("[WARN] Running in memory-only mode (data will not persist)")
    
    if SIMULATOR_ENABLED:
        asyncio.create_task(background_simulator_loop())
        print("[OK] Internal Telemetry Simulator started")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/api/v1/telemetry")
async def ingest_telemetry(t: TelemetryInput, db: Session = Depends(get_db)):
    """Ingest telemetry data and store in database"""
    try:
        timestamp = datetime.fromisoformat(t.ts.replace('Z', '+00:00'))
        for metric_name, metric_value in t.metrics.items():
            if isinstance(metric_value, list):
                continue
            telemetry_record = models.Telemetry(
                time=timestamp,
                equipment_id=t.device_id,
                metric_name=metric_name,
                metric_value=float(metric_value) if isinstance(metric_value, (int, float)) else None,
                status="normal"
            )
            db.add(telemetry_record)
        db.commit()
        latest_telemetry[t.device_id] = t.model_dump() if hasattr(t, 'model_dump') else t.dict()
        await manager.broadcast(json.dumps({
            "type": "telemetry",
            "data": latest_telemetry[t.device_id]
        }))
        return {"status": "ok", "device_id": t.device_id, "stored": "database"}
    except Exception as e:
        print(f"Database error: {e}, falling back to memory")
        latest_telemetry[t.device_id] = t.model_dump() if hasattr(t, 'model_dump') else t.dict()
        return {"status": "ok", "device_id": t.device_id, "stored": "memory"}

@app.get("/api/v1/telemetry/latest")
async def get_latest_telemetry(db: Session = Depends(get_db)):
    """Get latest telemetry for all equipment"""
    try:
        if check_db_connection():
            from sqlalchemy import func
            latest_data = {}
            equipment_list = db.query(models.Equipment).filter_by(active=True).all()
            for equipment in equipment_list:
                metrics_query = db.query(
                    models.Telemetry.metric_name,
                    models.Telemetry.metric_value,
                    func.max(models.Telemetry.time).label('time')
                ).filter(
                    models.Telemetry.equipment_id == equipment.equipment_id
                ).group_by(
                    models.Telemetry.metric_name,
                    models.Telemetry.metric_value
                ).all()
                if metrics_query:
                    metrics_dict = {m.metric_name: m.metric_value for m in metrics_query}
                    latest_data[equipment.equipment_id] = {
                        "device_id": equipment.equipment_id,
                        "ts": str(metrics_query[0].time) if metrics_query else str(datetime.now()),
                        "metrics": metrics_dict,
                        "meta": {"type": equipment.equipment_type}
                    }
            latest_data.update(latest_telemetry)
            return latest_data
    except Exception as e:
        print(f"Database query error: {e}")
    return latest_telemetry

@app.get("/api/v1/telemetry/history/{equipment_id}")
async def get_telemetry_history(
    equipment_id: str,
    hours: int = 24,
    db: Session = Depends(get_db)
):
    """Get historical telemetry for specific equipment"""
    from datetime import timedelta
    from sqlalchemy import and_
    cutoff_time = datetime.now() - timedelta(hours=hours)
    history = db.query(models.Telemetry).filter(
        and_(
            models.Telemetry.equipment_id == equipment_id,
            models.Telemetry.time >= cutoff_time
        )
    ).order_by(models.Telemetry.time.desc()).limit(10000).all()
    return {
        "equipment_id": equipment_id,
        "records": len(history),
        "data": [
            {
                "time": str(h.time),
                "metric": h.metric_name,
                "value": h.metric_value
            } for h in history
        ]
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "database": "connected" if db_status else "disconnected",
        "api": "up",
        "brand": {"name": APP_NAME, "owner": BRAND_OWNER, "tagline": TAGLINE},
        "simulator": "running" if SIMULATOR_ENABLED else "disabled",
        "timestamp": str(datetime.now())
    }

@app.get("/api/v1/health")
async def platform_health():
    """Health checks for API, dashboard dependency, database, and simulator."""
    db_status = check_db_connection()
    return {
        "status": "healthy" if db_status else "degraded",
        "checks": {
            "api": {"status": "up"},
            "database": {"status": "connected" if db_status else "disconnected"},
            "dashboard": {"status": "ready", "api_url": os.getenv("PUBLIC_API_URL", "local")},
            "simulator": {"status": "running" if SIMULATOR_ENABLED else "disabled", "latest_devices": len(latest_telemetry)},
        },
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/health/dashboard")
async def dashboard_health():
    return {"status": "ready", "api": "reachable", "timestamp": datetime.utcnow().isoformat() + "Z"}

@app.get("/api/v1/health/simulator")
async def simulator_health():
    return {
        "status": "running" if SIMULATOR_ENABLED else "disabled",
        "device_count": len(DEVICES),
        "latest_devices": len(latest_telemetry),
        "timestamp": datetime.utcnow().isoformat() + "Z",
    }

@app.get("/api/v1/equipment")
async def list_equipment(db: Session = Depends(get_db)):
    """List all equipment"""
    equipment = db.query(models.Equipment).filter_by(active=True).all()
    return [
        EquipmentResponse.from_orm(e) for e in equipment
    ]

@app.get("/api/v1/factory/machines")
async def list_machine_master(db: Session = Depends(get_db)):
    """List machine master data with plant/line/cell/process/mold context."""
    equipment = db.query(models.Equipment).filter_by(active=True).all()
    result = []
    for item in equipment:
        result.append({
            "equipment_id": item.equipment_id,
            "equipment_type": item.equipment_type,
            "description": item.description,
            "plant": item.cell.line.plant.name if item.cell and item.cell.line and item.cell.line.plant else None,
            "line": item.cell.line.name if item.cell and item.cell.line else None,
            "cell": item.cell.name if item.cell else None,
            "process": item.process.name if item.process else None,
            "mold_model": item.mold_model.model_code if item.mold_model else None,
            "plc_protocol": item.plc_protocol,
            "plc_address": item.plc_address,
            "cycle_time_standard": item.cycle_time_standard,
            "target_per_hour": item.target_per_hour,
        })
    return result

@app.post("/api/v1/factory/machines")
async def upsert_machine_master(
    payload: MachineSetup,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("admin", "manager")),
):
    company = _get_or_create(db, models.Company, name=BRAND_OWNER)
    plant = _get_or_create(db, models.Plant, company_id=company.id, code=payload.plant.upper().replace(" ", "-"), defaults={"name": payload.plant})
    line = _get_or_create(db, models.Line, plant_id=plant.id, code=payload.line.upper().replace(" ", "-"), defaults={"name": payload.line})
    cell = _get_or_create(db, models.Cell, line_id=line.id, code=payload.cell.upper().replace(" ", "-"), defaults={"name": payload.cell})
    process = _get_or_create(db, models.Process, code=payload.process.upper().replace(" ", "-"), defaults={"name": payload.process})
    mold = None
    if payload.mold_model:
        mold = _get_or_create(
            db,
            models.MoldModel,
            model_code=payload.mold_model,
            defaults={"part_name": payload.mold_model, "standard_cycle_time": payload.cycle_time_standard},
        )
    equipment = db.query(models.Equipment).filter_by(equipment_id=payload.equipment_id).first()
    if not equipment:
        equipment = models.Equipment(equipment_id=payload.equipment_id, equipment_type=payload.equipment_type)
        db.add(equipment)
    equipment.equipment_type = payload.equipment_type
    equipment.description = payload.description
    equipment.cell_id = cell.id
    equipment.process_id = process.id
    equipment.mold_model_id = mold.id if mold else None
    equipment.plc_protocol = payload.plc_protocol
    equipment.plc_address = payload.plc_address
    equipment.cycle_time_standard = payload.cycle_time_standard
    equipment.target_per_hour = payload.target_per_hour
    equipment.active = True
    db.commit()
    return {"status": "ok", "equipment_id": equipment.equipment_id}

@app.get("/api/v1/oee", response_model=list[OeeResponse])
async def calculate_oee(hours: int = 8, db: Session = Depends(get_db)):
    """Calculate Availability x Performance x Quality and a basic loss tree."""
    cutoff = datetime.utcnow() - timedelta(hours=hours)
    equipment = db.query(models.Equipment).filter_by(active=True).all()
    response = []
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
        planned_minutes = max(hours * 60 - 30, 1)
        availability = max(0.0, min(1.0, (planned_minutes - downtime_minutes) / planned_minutes))
        cycle_values = [t.metric_value for t in telemetry if t.metric_name == "cycle_time" and t.metric_value]
        avg_cycle = sum(cycle_values) / len(cycle_values) if cycle_values else item.cycle_time_standard
        performance = max(0.0, min(1.0, item.cycle_time_standard / avg_cycle if avg_cycle else 1.0))
        quality = 0.98
        oee = availability * performance * quality
        response.append({
            "equipment_id": item.equipment_id,
            "availability": round(availability * 100, 2),
            "performance": round(performance * 100, 2),
            "quality": round(quality * 100, 2),
            "oee": round(oee * 100, 2),
            "loss_tree": {
                "downtime_minutes": round(downtime_minutes, 2),
                "performance_loss_percent": round((1 - performance) * 100, 2),
                "quality_loss_percent": round((1 - quality) * 100, 2),
            },
        })
    return response

@app.post("/api/v1/downtime")
async def create_downtime(
    payload: DowntimeCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("admin", "manager", "supervisor", "maintenance", "operator")),
):
    equipment = db.query(models.Equipment).filter_by(equipment_id=payload.equipment_id).first()
    if not equipment:
        raise HTTPException(status_code=404, detail="Equipment not found")
    event = models.DowntimeEvent(
        equipment_id=payload.equipment_id,
        reason_code=payload.reason_code,
        category=payload.category,
        minutes=payload.minutes,
        comment=payload.comment,
        acknowledged_by=current_user.id,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    return {"status": "ok", "id": event.id}

@app.get("/api/v1/downtime/reasons")
async def downtime_reasons():
    return [
        {"code": "MACHINE_STOP", "category": "machine stop", "label": "Machine stop"},
        {"code": "MATERIAL_SHORTAGE", "category": "material shortage", "label": "Material shortage"},
        {"code": "QUALITY_ISSUE", "category": "quality issue", "label": "Quality issue"},
        {"code": "CHANGEOVER", "category": "changeover", "label": "Changeover"},
        {"code": "MAINTENANCE", "category": "maintenance", "label": "Maintenance"},
    ]

@app.get("/api/v1/connectors")
async def list_connectors(db: Session = Depends(get_db)):
    connectors = db.query(models.ConnectorConfig).filter_by(active=True).all()
    return [
        {"name": c.name, "protocol": c.protocol, "endpoint": c.endpoint, "tag_map": c.tag_map}
        for c in connectors
    ]

@app.post("/api/v1/demo/reset")
async def reset_demo_data(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.require_roles("admin", "manager")),
):
    seed_database(reset=True)
    latest_telemetry.clear()
    return {"status": "ok", "message": "Demo factory data reset"}

@app.websocket("/ws/andons")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await websocket.send_text(f"Received: {data}")
    except WebSocketDisconnect:
        manager.disconnect(websocket)

@app.post("/token", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """Login endpoint to get JWT token"""
    user = db.query(models.User).filter(models.User.username == form_data.username).first()
    if not user or not auth.verify_password(form_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    timeout_minutes = user.session_timeout_minutes or auth.ACCESS_TOKEN_EXPIRE_MINUTES
    access_token_expires = auth.timedelta(minutes=timeout_minutes)
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=access_token_expires
    )
    user.last_login = datetime.utcnow()
    db.commit()
    return {"access_token": access_token, "token_type": "bearer", "expires_in": timeout_minutes * 60, "role": user.role}

@app.post("/api/v1/auth/demo-login", response_model=Token)
async def demo_login(payload: DemoLogin, db: Session = Depends(get_db)):
    """Create a demo session for a selected role without exposing passwords in the UI."""
    if not DEMO_MODE:
        raise HTTPException(status_code=404, detail="Demo mode is disabled")
    role = auth.normalize_role(payload.role)
    username = "admin" if role == "admin" else role
    user = db.query(models.User).filter(models.User.username == username).first()
    if not user:
        seed_database(reset=False)
        user = db.query(models.User).filter(models.User.username == username).first()
    timeout_minutes = user.session_timeout_minutes or auth.ACCESS_TOKEN_EXPIRE_MINUTES
    access_token = auth.create_access_token(
        data={"sub": user.username, "role": user.role}, expires_delta=auth.timedelta(minutes=timeout_minutes)
    )
    user.last_login = datetime.utcnow()
    db.commit()
    return {"access_token": access_token, "token_type": "bearer", "expires_in": timeout_minutes * 60, "role": user.role}

@app.post("/register", response_model=UserResponse)
async def register_user(user: UserCreate, db: Session = Depends(get_db)):
    """Register a new user"""
    db_user = db.query(models.User).filter(models.User.username == user.username).first()
    if db_user:
        raise HTTPException(status_code=400, detail="Username already registered")
    hashed_password = auth.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        password_hash=hashed_password,
        role=auth.normalize_role(user.role)
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    """Get current logged in user profile"""
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "role": current_user.role,
        "active": current_user.active,
        "created_at": current_user.created_at,
        "last_login": current_user.last_login,
    }
