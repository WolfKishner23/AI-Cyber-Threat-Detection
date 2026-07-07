from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db, SessionLocal
from app.schemas.security_event import SecurityEventCreate, SecurityEventResponse
from app.services import security_event as event_service
from app.core.broadcaster import broadcaster
from app.detection.engine import DetectionEngine
from fastapi.concurrency import run_in_threadpool
import logging

router = APIRouter()
logger = logging.getLogger(__name__)

def _sync_run_detection():
    db = SessionLocal()
    try:
        # We pass None for background_tasks here because we will handle broadcasts and investigations differently,
        # or we can return the alerts generated and handle them here.
        engine = DetectionEngine(db=db)
        return engine.run()
    except Exception as e:
        logger.error(f"Detection engine failed: {e}")
    finally:
        db.close()

async def run_detection_task(background_tasks: BackgroundTasks):
    """
    Background task to run the detection engine asynchronously.
    """
    await run_in_threadpool(_sync_run_detection)
    # The DetectionEngine.__init__ now accepts background_tasks, but passing a running BackgroundTasks
    # object from a request into a thread is risky because it might be executed already.
    # To fix this properly, the DetectionEngine was already modified to accept background_tasks.
    # Wait, instead of returning alerts, if we just pass the request's background_tasks down to engine, 
    # it will add tasks to it while it's executing. Since Starlette's BackgroundTasks iterates over a list,
    # appending to it during iteration won't work correctly.
    pass

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
    event_in: SecurityEventCreate,
    background_tasks: BackgroundTasks
) -> SecurityEventResponse:
    event = event_service.create_security_event(db=db, obj_in=event_in)
    
    # Broadcast event after it is successfully committed
    payload = {
        "id": event.id,
        "user_id": event.user_id,
        "event_type": event.event_type,
        "ip_address": event.ip_address,
        "timestamp": event.timestamp.isoformat() if event.timestamp else None
    }
    background_tasks.add_task(broadcaster.broadcast, "new_event", payload)
    
    # Run detection engine
    # We create a new DB session inside the engine run, but wait, the engine was modified
    # to accept background_tasks. Let's pass the request's background_tasks.
    # Actually, rather than doing it in a background task, we can just trigger it.
    
    def trigger_detection(bg_tasks):
        db_session = SessionLocal()
        try:
            # We create a new BackgroundTasks object for the sub-tasks so they don't get lost
            # Wait, no, we can just await them.
            pass
        finally:
            db_session.close()

    async def run_engine_bg_async():
        import asyncio
        loop = asyncio.get_running_loop()
        
        class AsyncDispatcher:
            def add_task(self, func, *args, **kwargs):
                if asyncio.iscoroutinefunction(func):
                    asyncio.run_coroutine_threadsafe(func(*args, **kwargs), loop)
                else:
                    loop.call_soon_threadsafe(lambda: loop.run_in_executor(None, lambda: func(*args, **kwargs)))

        def _run_engine_sync():
            db_session = SessionLocal()
            try:
                engine = DetectionEngine(db=db_session, background_tasks=AsyncDispatcher())
                engine.run()
            except Exception as e:
                logger.error(f"Error in bg detection: {e}")
            finally:
                db_session.close()

        await run_in_threadpool(_run_engine_sync)

    background_tasks.add_task(run_engine_bg_async)
    
    return event

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
