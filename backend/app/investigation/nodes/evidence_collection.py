from app.investigation.state import InvestigationState
from sqlalchemy.orm import Session
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from langchain_core.runnables.config import RunnableConfig

def collect_evidence(state: InvestigationState, config: RunnableConfig) -> InvestigationState:
    """Gather contextual evidence from the database."""
    db: Session = config["configurable"]["db"]
    event_data = state.get("security_event", {})
    user_id = event_data.get("user_id")
    current_event_id = event_data.get("id")
    
    evidence = {}
    trace = state.get("reasoning_trace", [])
    
    if user_id:
        # Get last 10 events for user
        recent_events = db.query(SecurityEvent).filter(
            SecurityEvent.user_id == user_id,
            SecurityEvent.id != current_event_id
        ).order_by(SecurityEvent.timestamp.desc()).limit(10).all()
        
        evidence["recent_events"] = [{"id": e.id, "type": e.event_type, "timestamp": e.timestamp.isoformat(), "ip": e.ip_address} for e in recent_events]
        
        # Get previous locations
        locations = db.query(SecurityEvent.location).filter(
            SecurityEvent.user_id == user_id, SecurityEvent.location.isnot(None)
        ).distinct().all()
        evidence["locations"] = [loc[0] for loc in locations]
        
        # Get previous devices
        devices = db.query(SecurityEvent.device_name).filter(
            SecurityEvent.user_id == user_id, SecurityEvent.device_name.isnot(None)
        ).distinct().all()
        evidence["devices"] = [dev[0] for dev in devices]
        
        # Get previous alerts
        previous_alerts = db.query(Alert).join(SecurityEvent).filter(
            SecurityEvent.user_id == user_id,
            Alert.event_id != current_event_id
        ).all()
        evidence["previous_alerts"] = [{"id": a.id, "type": a.alert_type, "severity": a.severity} for a in previous_alerts]
        
        trace.append(f"Evidence Collection Agent: Queried database for user {user_id}. Found {len(recent_events)} recent events and {len(previous_alerts)} previous alerts.")
    else:
        trace.append("Evidence Collection Agent: No user_id found to collect evidence.")
        
    return {
        "evidence": evidence,
        "reasoning_trace": trace
    }
