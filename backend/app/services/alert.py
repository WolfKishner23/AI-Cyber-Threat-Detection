from typing import List, Optional
from sqlalchemy.orm import Session
from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.schemas.alert import AlertCreate, AlertUpdate

def get_alert_by_id(db: Session, alert_id: int) -> Optional[Alert]:
    """
    Retrieve an Alert by its ID, joining its related SecurityEvent.
    """
    return db.query(Alert).filter(Alert.id == alert_id).first()

def get_alerts(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    status: Optional[str] = None,
    severity: Optional[str] = None
) -> List[Alert]:
    """
    Retrieve multiple Alerts with optional filtering and pagination.
    """
    query = db.query(Alert)
    
    if status:
        query = query.filter(Alert.status == status)
    if severity:
        query = query.filter(Alert.severity == severity)
        
    return query.offset(skip).limit(limit).all()

def create_alert(db: Session, obj_in: AlertCreate) -> Alert:
    """
    Create a new Alert. Ensures that the referenced event_id exists.
    Raises ValueError if event_id is invalid.
    """
    # Verify the associated security event exists
    event_exists = db.query(SecurityEvent).filter(SecurityEvent.id == obj_in.event_id).first()
    if not event_exists:
        raise ValueError(f"Referenced SecurityEvent with ID {obj_in.event_id} does not exist.")

    db_obj = Alert(
        event_id=obj_in.event_id,
        alert_type=obj_in.alert_type,
        severity=obj_in.severity.value if hasattr(obj_in.severity, 'value') else obj_in.severity,
        status=obj_in.status.value if hasattr(obj_in.status, 'value') else obj_in.status,
    )
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj

def update_alert(
    db: Session,
    db_obj: Alert,
    obj_in: AlertUpdate
) -> Alert:
    """
    Update an Alert's status, severity, or type.
    """
    update_data = obj_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field in ("status", "severity") and value is not None:
            # Unwrap enums to string
            setattr(db_obj, field, value.value if hasattr(value, 'value') else value)
        else:
            setattr(db_obj, field, value)
            
    db.add(db_obj)
    db.commit()
    db.refresh(db_obj)
    return db_obj
