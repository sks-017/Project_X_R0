"""
Database Models for Production Control System
SQLAlchemy ORM models for equipment, telemetry, users, and alerts
"""
from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, ForeignKey, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
Base = declarative_base()
class Equipment(Base):
    """Equipment master table"""
    __tablename__ = 'equipment'
    id = Column(Integer, primary_key=True)
    equipment_id = Column(String(50), unique=True, nullable=False, index=True)
    equipment_type = Column(String(50), nullable=False)
    description = Column(Text)
    location = Column(String(100))
    installation_date = Column(DateTime)
    active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    telemetry = relationship("Telemetry", back_populates="equipment")
    alerts = relationship("Alert", back_populates="equipment")
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
