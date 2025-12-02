from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from .schemas import TelemetryInput, EquipmentResponse, AlertCreate, AlertResponse, UserCreate, UserResponse, Token
from . import models, auth
from .database import engine, get_db, init_db, check_db_connection
from datetime import datetime
import json
import asyncio
import os
app = FastAPI(title="Production Control System API", version="1.0")
@app.on_event("startup")
async def startup():
    try:
        if check_db_connection():
            models.Base.metadata.create_all(bind=engine)
            print("[OK] Database initialized")
            print("[OK] Database connection successful")
        else:
            print("[WARN] Database not available - running in memory-only mode")
    except Exception as e:
        print(f"[WARN] Database initialization failed: {e}")
        print("[WARN] Running in memory-only mode (data will not persist)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
latest_telemetry = {}
class ConnectionManager:
    def __init__(self):
        self.active_connections: list[WebSocket] = []
    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)
    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)
    async def broadcast(self, message: str):
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                pass
manager = ConnectionManager()
@app.post("/api/v1/telemetry")
async def ingest_telemetry(t: TelemetryInput, db: Session = Depends(get_db)):
    """Ingest telemetry data and store in database"""
    try:
        timestamp = datetime.fromisoformat(t.ts.replace('Z', '+00:00'))
        for metric_name, metric_value in t.metrics.items():
            telemetry_record = models.Telemetry(
                time=timestamp,
                equipment_id=t.device_id,
                metric_name=metric_name,
                metric_value=float(metric_value) if isinstance(metric_value, (int, float)) else None,
                status="normal"
            )
            db.add(telemetry_record)
        db.commit()
        latest_telemetry[t.device_id] = t.dict()
        await manager.broadcast(json.dumps({
            "type": "telemetry",
            "data": t.dict()
        }))
        return {"status": "ok", "device_id": t.device_id, "stored": "database"}
    except Exception as e:
        print(f"Database error: {e}, falling back to memory")
        latest_telemetry[t.device_id] = t.dict()
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
