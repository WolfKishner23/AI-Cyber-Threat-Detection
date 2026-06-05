from app.investigation.state import InvestigationState

def investigate_alert(state: InvestigationState) -> InvestigationState:
    """Analyze alert details, produce initial summary, and append to reasoning trace."""
    alert = state.get("alert", {})
    event = state.get("security_event", {})
    
    alert_type = alert.get("alert_type", "Unknown")
    user_id = event.get("user_id", "Unknown")
    
    summary = f"Initiated investigation for alert type '{alert_type}' on user '{user_id}'."
    trace = state.get("reasoning_trace", [])
    trace.append("Investigation Agent: Analyzed initial alert and event data.")
    
    return {
        "investigation_summary": summary,
        "investigation_status": "in_progress",
        "reasoning_trace": trace
    }
