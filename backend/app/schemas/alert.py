from datetime import datetime
from enum import Enum
from typing import Optional
from pydantic import BaseModel, Field
from app.schemas.security_event import SecurityEventResponse

class AlertSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class AlertStatus(str, Enum):
    OPEN = "open"
    INVESTIGATING = "investigating"
    RESOLVED = "resolved"
    FALSE_POSITIVE = "false_positive"

class AlertBase(BaseModel):
    alert_type: str = Field(..., max_length=100, description="Type of alert triggered (e.g., suspicious_login, brute_force_detected)")
    severity: AlertSeverity = Field(..., description="Severity level of the alert")
    status: AlertStatus = Field(default=AlertStatus.OPEN, description="Current investigation status of the alert")

class AlertCreate(AlertBase):
    event_id: int = Field(..., description="ID of the SecurityEvent that triggered this alert")

class AlertUpdate(BaseModel):
    alert_type: Optional[str] = Field(None, max_length=100)
    severity: Optional[AlertSeverity] = None
    status: Optional[AlertStatus] = None

class AlertResponse(AlertBase):
    id: int
    event_id: int
    created_at: datetime
    
    # Optional nested security event payload to allow deep investigation
    event: Optional[SecurityEventResponse] = None

    model_config = {
        "from_attributes": True
    }
