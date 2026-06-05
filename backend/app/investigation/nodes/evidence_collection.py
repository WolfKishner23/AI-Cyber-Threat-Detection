from app.investigation.state import InvestigationState
from sqlalchemy.orm import Session
from langchain_core.runnables.config import RunnableConfig
from app.tools import (
    get_user_history,
    get_device_history,
    get_location_history,
    get_previous_alerts,
    get_incident_history,
    get_ip_reputation
)

def collect_evidence(state: InvestigationState, config: RunnableConfig) -> InvestigationState:
    """Gather contextual evidence using Tools."""
    db: Session = config["configurable"]["db"]
    event_data = state.get("security_event", {})
    user_id = event_data.get("user_id")
    ip_address = event_data.get("ip_address")
    
    trace = state.get("reasoning_trace", [])
    
    # 1. Execute tools
    user_history = get_user_history(db, user_id) if user_id else {}
    device_history = get_device_history(db, user_id) if user_id else {}
    location_history = get_location_history(db, user_id) if user_id else {}
    previous_alerts = get_previous_alerts(db, user_id) if user_id else {}
    incident_history = get_incident_history(db, user_id) if user_id else {}
    ip_rep = get_ip_reputation(ip_address) if ip_address else {}
    
    # 2. Store raw tool outputs
    tool_outputs = {
        "user_history": user_history,
        "device_history": device_history,
        "location_history": location_history,
        "previous_alerts": previous_alerts,
        "incident_history": incident_history,
        "ip_reputation": ip_rep
    }
    
    # 3. Aggregate into Evidence Structure
    evidence = {
        "user_history": user_history,
        "device_history": device_history,
        "location_history": location_history,
        "previous_alerts": previous_alerts,
        "incident_history": incident_history,
        "ip_reputation": ip_rep
    }
    
    if user_id:
        trace.append(f"Evidence Collection Agent: Executed tools for user {user_id}. Gathered {user_history.get('event_count', 0)} recent events and {previous_alerts.get('alert_count', 0)} previous alerts.")
    else:
        trace.append("Evidence Collection Agent: No user_id found. Tools returned empty sets.")
        
    return {
        "evidence": evidence,
        "tool_outputs": tool_outputs,
        "reasoning_trace": trace
    }

