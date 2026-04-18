from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .schemas import TelemetryInput, EquipmentResponse, AlertCreate, AlertResponse, UserCreate, UserResponse, Token
from . import models, auth
from .database import engine, get_db, init_db, check_db_connection, SessionLocal
from datetime import datetime
import json
import asyncio
import os
import random

app = FastAPI(title="Production Control System API", version="1.0")

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

def seed_database():
    db = SessionLocal()
    try:
        admin_user = db.query(models.User).filter(models.User.username == "admin").first()
        if not admin_user:
            print("[INIT] Creating default admin user...")
            hashed_password = auth.get_password_hash("admin123")
            new_admin = models.User(
                username="admin",
                email="admin@example.com",
                password_hash=hashed_password,
                role="admin",
                active=True
            )
            db.add(new_admin)
            
            print("[INIT] Seeding equipment...")
            for device in DEVICES:
                eq = models.Equipment(
                    equipment_id=device["id"],
                    equipment_type=device["type"],
                    description=f"{device['type']} Unit {device['id'].split('-')[-1]}",
                    active=True
                )
                db.add(eq)
                
            db.commit()
            print("[INIT] Default admin and equipment seeded successfully.")
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
        "timestamp": str(datetime.now())
    }

@app.get("/api/v1/equipment")
async def list_equipment(db: Session = Depends(get_db)):
    """List all equipment"""
    equipment = db.query(models.Equipment).filter_by(active=True).all()
    return [
        EquipmentResponse.from_orm(e) for e in equipment
    ]

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
    access_token_expires = auth.timedelta(minutes=auth.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = auth.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

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
        role=user.role
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

@app.get("/users/me", response_model=UserResponse)
async def read_users_me(current_user: models.User = Depends(auth.get_current_active_user)):
    """Get current logged in user profile"""
    return current_user
