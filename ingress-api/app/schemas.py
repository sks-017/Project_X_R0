"""
Pydantic schemas for API request/response validation
"""
from pydantic import BaseModel
from typing import Dict, Any, Optional
from datetime import datetime
class TelemetryInput(BaseModel):
    """Input schema for telemetry data"""
    device_id: str
    ts: str
    metrics: Dict[str, Any]
    meta: Optional[Dict[str, Any]] = None
class EquipmentCreate(BaseModel):
    """Schema for creating equipment"""
    equipment_id: str
    equipment_type: str
    description: Optional[str] = None
    location: Optional[str] = None
class EquipmentResponse(BaseModel):
    """Schema for equipment response"""
    id: int
    equipment_id: str
    equipment_type: str
    description: Optional[str]
    location: Optional[str]
    active: bool
    created_at: datetime
    class Config:
        from_attributes = True
class AlertCreate(BaseModel):
    """Schema for creating alerts"""
    equipment_id: str
    alert_type: str
    severity: str
    message: str
class AlertResponse(BaseModel):
    """Schema for alert response"""
    id: int
    equipment_id: str
    alert_type: str
    severity: str
    message: str
    acknowledged: bool
    created_at: datetime
    class Config:
        from_attributes = True
class UserBase(BaseModel):
    """Base user schema"""
    username: str
    email: str
class UserCreate(UserBase):
    """Schema for creating user"""
    password: str
    role: str = "operator"
class UserLogin(BaseModel):
    """Schema for user login"""
    username: str
    password: str
class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    role: str
    active: bool
    created_at: datetime
    last_login: Optional[datetime]
    class Config:
        from_attributes = True
class Token(BaseModel):
    """Schema for JWT token"""
    access_token: str
    token_type: str
class TokenData(BaseModel):
    """Schema for token payload"""
    username: Optional[str] = None
