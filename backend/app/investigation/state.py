from typing import TypedDict, Dict, Any, List

class InvestigationState(TypedDict):
    alert_id: int
    alert: Dict[str, Any]
    security_event: Dict[str, Any]
    investigation_summary: str
    evidence: Dict[str, Any]
    risk_score: int
    confidence_score: int
    risk_level: str          # Phase 6: low / medium / high / critical
    llm_reasoning: str       # Phase 6: LLM chain-of-thought reasoning
    recommended_action: str
    investigation_status: str
    reasoning_trace: List[str]
    tool_outputs: Dict[str, Any]
    tools_used: List[str]      # Phase 6C: tools executed by autonomous agent
