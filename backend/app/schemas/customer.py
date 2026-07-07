from pydantic import BaseModel
from typing import Any, Optional


class CustomerLogin(BaseModel):
    customer_id: str
    password: str
    location: str


class CustomerLoginResponseV2(BaseModel):
    success: bool
    customer_name: Optional[str] = None
    customer_id: Optional[str] = None
    account_number: Optional[str] = None
    message: Optional[str] = None
    # Phase 3 -- behavioral risk data returned to frontend
    risk_score: int = 0
    risk_level: str = "low"
    anomalies: list[str] = []
