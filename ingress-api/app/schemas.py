"""
Pydantic schemas for API request and response validation.
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class TelemetryInput(BaseModel):
    """Input schema for telemetry data."""

    device_id: str
    ts: str
    metrics: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None


class EquipmentCreate(BaseModel):
    """Schema for creating equipment."""

    equipment_id: str
    equipment_type: str
    description: Optional[str] = None
    location: Optional[str] = None


class EquipmentResponse(BaseModel):
    """Schema for equipment response."""

    id: int
    equipment_id: str
    equipment_type: str
    description: Optional[str]
    location: Optional[str]
    active: bool
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class MachineSetup(BaseModel):
    """Machine master setup payload."""

    equipment_id: str
    equipment_type: str
    description: Optional[str] = None
    plant: str
    line: str
    cell: str
    process: str
    mold_model: Optional[str] = None
    plc_protocol: str = "simulator"
    plc_address: Optional[str] = None
    cycle_time_standard: float = 35.0
    target_per_hour: int = 240


class ShiftCalendarCreate(BaseModel):
    plant_code: str
    shift_name: str
    starts_at: str
    ends_at: str
    planned_downtime_minutes: int = 30
    active: bool = True


class ShiftCalendarResponse(BaseModel):
    id: int
    plant_code: str
    plant_name: Optional[str] = None
    shift_name: str
    starts_at: str
    ends_at: str
    planned_downtime_minutes: int
    active: bool


class TargetStandardCreate(BaseModel):
    equipment_id: str
    shift_name: str
    target_parts: int
    standard_cycle_time: float
    quality_target: float = 0.98


class TargetStandardResponse(BaseModel):
    id: int
    equipment_id: str
    shift_name: str
    target_parts: int
    standard_cycle_time: float
    quality_target: float


class ConnectorTestRequest(BaseModel):
    name: str
    protocol: str
    endpoint: str
    tag_map: Dict[str, Any] = Field(default_factory=dict)


class ConnectorTestResponse(BaseModel):
    ok: bool
    protocol: str
    endpoint: str
    message: str
    sample: Optional[Dict[str, Any]] = None


class DowntimeCreate(BaseModel):
    equipment_id: str
    reason_code: str
    category: str
    minutes: float
    comment: Optional[str] = None


class OeeResponse(BaseModel):
    equipment_id: str
    availability: float
    performance: float
    quality: float
    oee: float
    loss_tree: Dict[str, float]


class HealthResponse(BaseModel):
    status: str
    checks: Dict[str, Any]
    timestamp: datetime


class DemoLogin(BaseModel):
    role: str = "operator"


class AlertCreate(BaseModel):
    """Schema for creating alerts."""

    equipment_id: str
    alert_type: str
    severity: str
    message: str


class AlertResponse(BaseModel):
    """Schema for alert response."""

    id: int
    equipment_id: str
    alert_type: str
    severity: str
    message: str
    acknowledged: bool
    created_at: datetime

    class Config:
        orm_mode = True
        from_attributes = True


class UserBase(BaseModel):
    """Base user schema."""

    username: str
    email: str


class UserCreate(UserBase):
    """Schema for creating user."""

    password: str
    role: str = "operator"


class UserLogin(BaseModel):
    """Schema for user login."""

    username: str
    password: str


class UserResponse(UserBase):
    """Schema for user response."""

    id: int
    role: str
    active: bool
    created_at: datetime
    last_login: Optional[datetime]

    class Config:
        orm_mode = True
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token."""

    access_token: str
    token_type: str
    expires_in: int = 1800
    role: Optional[str] = None


class TokenData(BaseModel):
    """Schema for token payload."""

    username: Optional[str] = None


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    response: str
    context_used: List[str]
