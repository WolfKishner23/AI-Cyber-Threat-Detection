from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class InvestigationResponse(BaseModel):
    alert_id: int
    risk_score: int
    confidence_score: int
    recommended_action: str
    investigation_summary: str
    evidence: Dict[str, Any]
    reasoning_trace: List[str]
