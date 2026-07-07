import ipaddress
from datetime import datetime
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field, field_validator

class SecurityEventBase(BaseModel):
    user_id: str = Field(..., max_length=255, description="Unique identifier of the user associated with the event")
    event_type: str = Field(..., max_length=100, description="Type of security event (e.g., login_failed, data_exfiltration)")
    location: Optional[str] = Field(None, max_length=255, description="Geographic location of the event origin")
    ip_address: str = Field(..., max_length=45, description="IP address (IPv4 or IPv6)")
    device_name: Optional[str] = Field(None, max_length=255, description="Name/hostname of the device involved")
    target_resource: Optional[str] = Field(None, max_length=255, description="Resource being accessed (e.g., bank account number)")
    timestamp: Optional[datetime] = Field(None, description="Optional custom timestamp; defaults to current time if omitted")
    raw_payload: Dict[str, Any] = Field(default_factory=dict, description="Arbitrary raw JSON payload detailing the event")

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: str) -> str:
        # Strip whitespaces and validate IP address
        ip_str = v.strip()
        try:
            ipaddress.ip_address(ip_str)
        except ValueError:
            raise ValueError(f"Invalid IP address format: '{v}'")
        return ip_str

class SecurityEventCreate(SecurityEventBase):
    pass

class SecurityEventUpdate(BaseModel):
    user_id: Optional[str] = Field(None, max_length=255)
    event_type: Optional[str] = Field(None, max_length=100)
    location: Optional[str] = Field(None, max_length=255)
    ip_address: Optional[str] = Field(None, max_length=45)
    device_name: Optional[str] = Field(None, max_length=255)
    target_resource: Optional[str] = Field(None, max_length=255)
    raw_payload: Optional[Dict[str, Any]] = None

    @field_validator("ip_address")
    @classmethod
    def validate_ip_address(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            ip_str = v.strip()
            try:
                ipaddress.ip_address(ip_str)
            except ValueError:
                raise ValueError(f"Invalid IP address format: '{v}'")
            return ip_str
        return v

class SecurityEventResponse(SecurityEventBase):
    id: int
    timestamp: datetime

    model_config = {
        "from_attributes": True
    }
