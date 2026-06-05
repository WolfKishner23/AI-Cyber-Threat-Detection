from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models.security_event import SecurityEvent

def get_location_history(db: Session, user_id: str) -> dict:
    """Retrieve location usage history for a given user."""
    if not user_id:
        return {"locations": [], "frequencies": {}, "last_seen": {}}
        
    # Get distinct locations and their counts
    location_counts = db.query(
        SecurityEvent.location, 
        func.count(SecurityEvent.id),
        func.max(SecurityEvent.timestamp)
    ).filter(
        SecurityEvent.user_id == user_id, 
        SecurityEvent.location.isnot(None)
    ).group_by(SecurityEvent.location).all()
    
    locations = []
    frequencies = {}
    last_seen = {}
    
    for location, count, last_timestamp in location_counts:
        locations.append(location)
        frequencies[location] = count
        last_seen[location] = last_timestamp.isoformat() if last_timestamp else None
        
    return {
        "locations": locations,
        "frequencies": frequencies,
        "last_seen": last_seen
    }
