from sqlalchemy.orm import Session
from app.models.security_event import SecurityEvent
from app.models.alert import Alert

def get_previous_alerts(db: Session, user_id: str) -> dict:
    """Retrieve previous alerts associated with a user."""
    if not user_id:
        return {"alerts": [], "alert_count": 0, "severities": {"low": 0, "medium": 0, "high": 0, "critical": 0}}
        
    previous_alerts = db.query(Alert).join(SecurityEvent).filter(
        SecurityEvent.user_id == user_id
    ).all()
    
    severities = {"low": 0, "medium": 0, "high": 0, "critical": 0}
    alerts_list = []
    
    for alert in previous_alerts:
        severity = alert.severity.lower() if alert.severity else "medium"
        if severity in severities:
            severities[severity] += 1
        else:
            # default fallback if strange severity
            severities["medium"] += 1
            
        alerts_list.append({
            "id": alert.id,
            "type": alert.alert_type,
            "severity": alert.severity,
            "status": alert.status
        })
        
    return {
        "alerts": alerts_list,
        "alert_count": len(alerts_list),
        "severities": severities
    }
