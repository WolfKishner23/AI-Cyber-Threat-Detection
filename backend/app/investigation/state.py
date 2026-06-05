from typing import TypedDict, Dict, Any, List

class InvestigationState(TypedDict):
    alert_id: int
    alert: Dict[str, Any]
    security_event: Dict[str, Any]
    investigation_summary: str
    evidence: Dict[str, Any]
    risk_score: int
    confidence_score: int
    recommended_action: str
    investigation_status: str
    reasoning_trace: List[str]
