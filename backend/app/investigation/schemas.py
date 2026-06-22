from typing import Optional, Dict, Any, List
from pydantic import BaseModel

class InvestigationResponse(BaseModel):
    alert_id: int
    risk_score: int
    confidence_score: int
    risk_level: str = ""           # Phase 6: low / medium / high / critical
    recommended_action: str
    investigation_summary: str
    tools_used: List[str] = []
    evidence: Dict[str, Any]
    tool_outputs: Optional[Dict[str, Any]] = None
    llm_reasoning: str = ""        # Phase 6: LLM chain-of-thought reasoning
    reasoning_trace: List[str]

from datetime import datetime

class InvestigationModel(BaseModel):
    id: int
    alert_id: int
    customer_id: str
    investigation_summary: str
    evidence: Dict[str, Any]
    tool_outputs: Dict[str, Any]
    reasoning_trace: List[str]
    risk_score: int
    confidence_score: int
    recommended_action: str
    created_at: datetime

    class Config:
        from_attributes = True

