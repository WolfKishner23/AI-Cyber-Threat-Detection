from app.investigation.state import InvestigationState
from app.llm.client import LLMClient
import logging

logger = logging.getLogger(__name__)

# Module-level client — instantiated once per worker process
_client = LLMClient()

def plan_response(state: InvestigationState) -> InvestigationState:
    """Recommend remediation actions using LLM with heuristic fallback."""
    alert = state.get("alert", {})
    evidence = state.get("evidence", {})
    risk_score = state.get("risk_score", 0)
    confidence_score = state.get("confidence_score", 0)
    summary = state.get("investigation_summary", "")
    trace = list(state.get("reasoning_trace", []))
    
    # Try LLM Response Planning
    llm_result = _client.plan_response(
        alert=alert,
        investigation_summary=summary,
        evidence=evidence,
        risk_score=risk_score,
        confidence_score=confidence_score
    )
    
    if llm_result:
        action = llm_result["recommended_action"]
        reasoning = llm_result["reasoning"]
        trace.append(f"LLM Response Planning Agent: Recommended action '{action}'. Reasoning: {reasoning}")
        summary += f"\n- LLM Response Planning: {reasoning} Recommending action: {action}."
    else:
        # Fallback to heuristic logic
        if risk_score >= 90:
            action = "lock_account"
        elif risk_score >= 70:
            action = "force_password_reset"
        elif risk_score >= 50:
            action = "notify_user"
        else:
            action = "monitor"
            
        trace.append(f"Response Planning Agent [Heuristic Fallback]: Recommended action '{action}' based on risk score {risk_score}.")
        summary += f" The final risk score is {risk_score}, recommending action: {action}."
    
    return {
        "recommended_action": action,
        "investigation_status": "completed",
        "investigation_summary": summary,
        "reasoning_trace": trace
    }

