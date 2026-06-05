from app.investigation.state import InvestigationState

def plan_response(state: InvestigationState) -> InvestigationState:
    """Recommend remediation actions based on risk score."""
    risk_score = state.get("risk_score", 0)
    trace = state.get("reasoning_trace", [])
    
    if risk_score >= 90:
        action = "lock_account"
    elif risk_score >= 70:
        action = "force_password_reset"
    elif risk_score >= 50:
        action = "notify_user"
    else:
        action = "monitor"
        
    trace.append(f"Response Planning Agent: Recommended action '{action}' based on risk score {risk_score}.")
    
    summary = state.get("investigation_summary", "")
    summary += f" The final risk score is {risk_score}, recommending action: {action}."
    
    return {
        "recommended_action": action,
        "investigation_status": "completed",
        "investigation_summary": summary,
        "reasoning_trace": trace
    }
