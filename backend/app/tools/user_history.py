from sqlalchemy.orm import Session
from app.models.security_event import SecurityEvent

def get_user_history(db: Session, user_id: str) -> dict:
    """Retrieve the recent event history for a given user."""
    if not user_id:
        return {"recent_events": [], "event_count": 0, "login_history": []}
        
    recent_events = db.query(SecurityEvent).filter(
        SecurityEvent.user_id == user_id
    ).order_by(SecurityEvent.timestamp.desc()).limit(10).all()
    
    login_events = [e for e in recent_events if e.event_type in ["login", "failed_login"]]
    
    return {
        "recent_events": [
            {
                "id": e.id, 
                "type": e.event_type, 
                "timestamp": e.timestamp.isoformat(), 
                "ip": e.ip_address,
                "location": e.location
            } for e in recent_events
        ],
        "event_count": len(recent_events),
        "login_history": [
            {
                "id": e.id,
                "type": e.event_type,
                "timestamp": e.timestamp.isoformat(),
                "ip": e.ip_address
            } for e in login_events
        ]
    }
