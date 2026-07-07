from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.detection.engine import DetectionEngine
from app.schemas.detection_run import DetectionRunResponse

router = APIRouter()


@router.post("/run", response_model=DetectionRunResponse)
def trigger_detection(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """
    Run detection engine and broadcast any newly generated alerts.
    """
    engine = DetectionEngine(
        db=db,
        background_tasks=background_tasks,
    )
    return engine.run()