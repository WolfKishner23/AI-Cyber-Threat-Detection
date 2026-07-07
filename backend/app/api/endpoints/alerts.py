from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.alert import AlertCreate, AlertResponse, AlertSeverity, AlertStatus
from app.services import alert as alert_service
from app.core.broadcaster import broadcaster
from app.services.investigation import run_autonomous_investigation_task

router = APIRouter()

@router.post(
    "/",
    response_model=AlertResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create an alert",
    description="Registers a new alert associated with a valid SecurityEvent."
)
def create_alert(
    *,
    db: Session = Depends(get_db),
    alert_in: AlertCreate,
    background_tasks: BackgroundTasks
) -> AlertResponse:
    try:
        alert = alert_service.create_alert(db=db, obj_in=alert_in)
        
        # Broadcast alert after it is successfully committed
        payload = {
            "id": alert.id,
            "event_id": alert.event_id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "status": alert.status,
            "created_at": alert.created_at.isoformat() if alert.created_at else None
        }
        background_tasks.add_task(broadcaster.broadcast, "new_alert", payload)
        
        # Trigger autonomous investigation for the new alert
        background_tasks.add_task(run_autonomous_investigation_task, alert_id=alert.id)
        
        return alert
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )

@router.get(
    "/",
    response_model=List[AlertResponse],
    summary="List alerts",
    description="Retrieves a list of alerts with optional pagination and filters (by status or severity)."
)
def read_alerts(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of alerts to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of alerts to return"),
    status: Optional[AlertStatus] = Query(None, description="Filter by alert status"),
    severity: Optional[AlertSeverity] = Query(None, description="Filter by alert severity")
) -> List[AlertResponse]:
    return alert_service.get_alerts(
        db=db,
        skip=skip,
        limit=limit,
        status=status,
        severity=severity
    )

@router.get(
    "/{id}",
    response_model=AlertResponse,
    summary="Get alert by ID",
    description="Retrieves the detailed information of a specific alert by its unique database ID."
)
def read_alert_by_id(
    id: int,
    db: Session = Depends(get_db)
) -> AlertResponse:
    alert = alert_service.get_alert_by_id(db=db, alert_id=id)
    if not alert:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Alert with ID {id} not found."
        )
    return alert
