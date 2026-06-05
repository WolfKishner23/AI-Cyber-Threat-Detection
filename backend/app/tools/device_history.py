from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.security_event import SecurityEvent

def get_device_history(db: Session, user_id: str) -> dict:
    """Retrieve device usage history for a given user."""
    if not user_id:
        return {"devices": [], "frequencies": {}, "last_seen": {}}
        
    # Get distinct devices and their counts
    device_counts = db.query(
        SecurityEvent.device_name, 
        func.count(SecurityEvent.id),
        func.max(SecurityEvent.timestamp)
    ).filter(
        SecurityEvent.user_id == user_id, 
        SecurityEvent.device_name.isnot(None)
    ).group_by(SecurityEvent.device_name).all()
    
    devices = []
    frequencies = {}
    last_seen = {}
    
    for device_name, count, last_timestamp in device_counts:
        devices.append(device_name)
        frequencies[device_name] = count
        last_seen[device_name] = last_timestamp.isoformat() if last_timestamp else None
        
    return {
        "devices": devices,
        "frequencies": frequencies,
        "last_seen": last_seen
    }
