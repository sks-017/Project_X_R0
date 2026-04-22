"""
Database Models for Production Control System
SQLAlchemy ORM models for equipment, telemetry, users, and alerts
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
Base = declarative_base()

class Company(Base):
    """Tenant/company master."""
    __tablename__ = 'companies'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    plants = relationship("Plant", back_populates="company")

class Plant(Base):
    """Plant master."""
    __tablename__ = 'plants'
    id = Column(Integer, primary_key=True)
    company_id = Column(Integer, ForeignKey('companies.id'), nullable=False)
    name = Column(String(150), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    timezone = Column(String(80), default="Asia/Calcutta")
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    company = relationship("Company", back_populates="plants")
    lines = relationship("Line", back_populates="plant")

class Line(Base):
    """Production line master."""
    __tablename__ = 'lines'
    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id'), nullable=False)
    name = Column(String(150), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    plant = relationship("Plant", back_populates="lines")
    cells = relationship("Cell", back_populates="line")

class Cell(Base):
    """Manufacturing cell master."""
    __tablename__ = 'cells'
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, ForeignKey('lines.id'), nullable=False)
    name = Column(String(150), nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    line = relationship("Line", back_populates="cells")
    equipment = relationship("Equipment", back_populates="cell")

class Process(Base):
    """Process master such as molding, cutting, welding, or chilling."""
    __tablename__ = 'processes'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)
    code = Column(String(50), unique=True, nullable=False)
    description = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class MoldModel(Base):
    """Mold/model master for injection molding and automotive parts."""
    __tablename__ = 'mold_models'
    id = Column(Integer, primary_key=True)
    model_code = Column(String(80), unique=True, nullable=False)
    part_name = Column(String(150), nullable=False)
    customer = Column(String(150))
    standard_cycle_time = Column(Float, nullable=False, default=35.0)
    cavity_count = Column(Integer, default=1)
    shot_count = Column(Integer, default=0)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Equipment(Base):
    """Equipment master table"""
    __tablename__ = 'equipment'
    id = Column(Integer, primary_key=True)
    cell_id = Column(Integer, ForeignKey('cells.id'))
    process_id = Column(Integer, ForeignKey('processes.id'))
    mold_model_id = Column(Integer, ForeignKey('mold_models.id'))
    equipment_id = Column(String(50), unique=True, nullable=False, index=True)
    equipment_type = Column(String(50), nullable=False)
    description = Column(Text)
    location = Column(String(100))
    plc_protocol = Column(String(50), default="simulator")
    plc_address = Column(String(150))
    cycle_time_standard = Column(Float, default=35.0)
    target_per_hour = Column(Integer, default=240)
    installation_date = Column(DateTime)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    cell = relationship("Cell", back_populates="equipment")
    process = relationship("Process")
    mold_model = relationship("MoldModel")
    telemetry = relationship("Telemetry", back_populates="equipment")
    alerts = relationship("Alert", back_populates="equipment")
    downtime_events = relationship("DowntimeEvent", back_populates="equipment")

class ShiftCalendar(Base):
    """Shift calendar and planned downtime setup."""
    __tablename__ = 'shift_calendars'
    id = Column(Integer, primary_key=True)
    plant_id = Column(Integer, ForeignKey('plants.id'), nullable=False)
    shift_name = Column(String(50), nullable=False)
    starts_at = Column(String(5), nullable=False)
    ends_at = Column(String(5), nullable=False)
    planned_downtime_minutes = Column(Integer, default=30)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class TargetStandard(Base):
    """Production targets and cycle-time standards."""
    __tablename__ = 'target_standards'
    id = Column(Integer, primary_key=True)
    equipment_id = Column(String(50), ForeignKey('equipment.equipment_id'), nullable=False)
    shift_name = Column(String(50), nullable=False)
    target_parts = Column(Integer, nullable=False)
    standard_cycle_time = Column(Float, nullable=False)
    quality_target = Column(Float, default=0.98)
    created_at = Column(DateTime, default=datetime.utcnow)

class DowntimeEvent(Base):
    """Downtime reason capture and resolution workflow."""
    __tablename__ = 'downtime_events'
    id = Column(Integer, primary_key=True)
    equipment_id = Column(String(50), ForeignKey('equipment.equipment_id'), nullable=False)
    reason_code = Column(String(80), nullable=False)
    category = Column(String(80), nullable=False)
    started_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    ended_at = Column(DateTime)
    minutes = Column(Float, default=0.0)
    comment = Column(Text)
    acknowledged_by = Column(Integer, ForeignKey('users.id'))
    resolved_by = Column(Integer, ForeignKey('users.id'))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    equipment = relationship("Equipment", back_populates="downtime_events")

class AlertRule(Base):
    """Configurable alert and escalation rule."""
    __tablename__ = 'alert_rules'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)
    metric_name = Column(String(100), nullable=False)
    condition = Column(String(20), nullable=False)
    threshold = Column(Float, nullable=False)
    severity = Column(String(20), default="warning")
    escalation_minutes = Column(Integer, default=5)
    target_role = Column(String(50), default="supervisor")
    channels = Column(JSON, default=list)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class ConnectorConfig(Base):
    """PLC/IIoT connector setup for edge gateways."""
    __tablename__ = 'connector_configs'
    id = Column(Integer, primary_key=True)
    name = Column(String(150), unique=True, nullable=False)
    protocol = Column(String(50), nullable=False)
    endpoint = Column(String(255), nullable=False)
    tag_map = Column(JSON, default=dict)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)

class Telemetry(Base):
    """Time-series telemetry data (will become TimescaleDB hypertable)"""
    __tablename__ = 'telemetry'
    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False, index=True)
    equipment_id = Column(String(50), ForeignKey('equipment.equipment_id'), nullable=False, index=True)
    metric_name = Column(String(100), nullable=False, index=True)
    metric_value = Column(Float)
    unit = Column(String(20))
    status = Column(String(20))
    equipment = relationship("Equipment", back_populates="telemetry")
class User(Base):
    """User accounts for authentication"""
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False)
    active = Column(Boolean, default=True)
    session_timeout_minutes = Column(Integer, default=30)
    created_at = Column(DateTime, default=datetime.utcnow)
    last_login = Column(DateTime)
    alerts_acknowledged = relationship("Alert", back_populates="acknowledged_by_user")
    audit_logs = relationship("AuditLog", back_populates="user")
class Alert(Base):
    """Equipment alerts and warnings"""
    __tablename__ = 'alerts'
    id = Column(Integer, primary_key=True)
    equipment_id = Column(String(50), ForeignKey('equipment.equipment_id'), nullable=False)
    alert_type = Column(String(50), nullable=False)
    severity = Column(String(20), nullable=False)
    message = Column(Text, nullable=False)
    acknowledged = Column(Boolean, default=False)
    acknowledged_by = Column(Integer, ForeignKey('users.id'))
    acknowledged_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    equipment = relationship("Equipment", back_populates="alerts")
    acknowledged_by_user = relationship("User", back_populates="alerts_acknowledged")
class AuditLog(Base):
    """Audit trail for user actions"""
    __tablename__ = 'audit_log'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    action = Column(String(100), nullable=False)
    resource = Column(String(100))
    details = Column(JSON)
    ip_address = Column(String(50))
    created_at = Column(DateTime, default=datetime.utcnow, index=True)
    user = relationship("User", back_populates="audit_logs")
