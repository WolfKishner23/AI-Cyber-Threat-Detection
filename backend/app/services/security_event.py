from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.security_event import SecurityEvent
from app.schemas.security_event import SecurityEventCreate, SecurityEventUpdate

def get_security_event_by_id(db: Session, event_id: int) -> Optional[SecurityEvent]:
    """
    Retrieve a SecurityEvent by its ID.
    """
    return db.query(SecurityEvent).filter(SecurityEvent.id == event_id).first()

def get_security_events(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    event_type: Optional[str] = None,
    user_id: Optional[str] = None
) -> List[SecurityEvent]:
    """
    Retrieve multiple SecurityEvents with optional filtering and pagination.
    """
    query = db.query(SecurityEvent)
    
    if event_type:
        query = query.filter(SecurityEvent.event_type == event_type)
    if user_id:
        query = query.filter(SecurityEvent.user_id == user_id)
        
    return query.order_by(SecurityEvent.id.desc()).offset(skip).limit(limit).all()

def create_security_event(db: Session, obj_in: SecurityEventCreate) -> SecurityEvent:
    """
    Create a new SecurityEvent.
    """
    kwargs = {
        "user_id": obj_in.user_id,
        "event_type": obj_in.event_type,
        "location": obj_in.location,
        "ip_address": obj_in.ip_address,
        "device_name": obj_in.device_name,
        "raw_payload": obj_in.raw_payload,
    }
    if obj_in.timestamp is not None:
        kwargs["timestamp"] = obj_in.timestamp

    db_obj = SecurityEvent(**kwargs)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_security_event(
    db: Session,
    db_obj: SecurityEvent,
    obj_in: SecurityEventUpdate
) -> SecurityEvent:
    """
    Update a SecurityEvent's fields.
    """
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(db_obj, field, value)
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
