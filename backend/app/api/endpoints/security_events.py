from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.security_event import SecurityEventCreate, SecurityEventResponse
from app.services import security_event as event_service

router = APIRouter()

@router.post(
    "/",
    response_model=SecurityEventResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a security event",
    description="Registers a new security event with user context, IP address, and raw payload data."
)
def create_event(
    *,
    db: Session = Depends(get_db),
    event_in: SecurityEventCreate
) -> SecurityEventResponse:
    return event_service.create_security_event(db=db, obj_in=event_in)

@router.get(
    "/",
    response_model=List[SecurityEventResponse],
    summary="List security events",
    description="Retrieves a list of security events with optional pagination and filters (by user_id or event_type)."
)
def read_events(
    db: Session = Depends(get_db),
    skip: int = Query(0, ge=0, description="Number of events to skip for pagination"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of events to return"),
    event_type: Optional[str] = Query(None, description="Filter by event type"),
    user_id: Optional[str] = Query(None, description="Filter by associated user ID")
) -> List[SecurityEventResponse]:
    return event_service.get_security_events(
        db=db,
        skip=skip,
        limit=limit,
        event_type=event_type,
        user_id=user_id
    )

@router.get(
    "/{id}",
    response_model=SecurityEventResponse,
    summary="Get security event by ID",
    description="Retrieves the detailed information of a specific security event by its unique database ID."
)
def read_event_by_id(
    id: int,
    db: Session = Depends(get_db)
) -> SecurityEventResponse:
    event = event_service.get_security_event_by_id(db=db, event_id=id)
    if not event:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Security event with ID {id} not found."
        )
    return event
