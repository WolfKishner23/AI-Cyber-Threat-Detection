from app.investigation.state import InvestigationState

def assess_risk(state: InvestigationState) -> InvestigationState:
    """Assess threat severity using collected evidence."""
    alert = state.get("alert", {})
    evidence = state.get("evidence", {})
    trace = state.get("reasoning_trace", [])
    
    alert_type = alert.get("alert_type", "")
    risk_score = 0
    confidence_score = 80  # Heuristic default
    
    previous_alerts = evidence.get("previous_alerts", [])
    
    if alert_type == "brute_force" or alert_type == "credential_compromise":
        risk_score = 95
        trace.append(f"Risk Assessment Agent: Assigned high risk (95) due to {alert_type}.")
    elif alert_type == "impossible_travel":
        risk_score = 75
        trace.append("Risk Assessment Agent: Assigned medium-high risk (75) due to impossible travel.")
    elif alert_type == "new_device":
        risk_score = 35
        trace.append("Risk Assessment Agent: Assigned low-medium risk (35) due to new device login.")
    else:
        risk_score = 50
        trace.append("Risk Assessment Agent: Assigned default risk (50).")
        
    if len(previous_alerts) > 0:
        risk_score = min(100, risk_score + 15)
        trace.append("Risk Assessment Agent: Increased risk score due to previous alerts on this user.")
        
    return {
        "risk_score": risk_score,
        "confidence_score": confidence_score,
        "reasoning_trace": trace
    }
