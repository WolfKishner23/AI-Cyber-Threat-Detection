from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.detection.engine import DetectionEngine
from app.schemas.detection_run import DetectionRunResponse

router = APIRouter()

@router.post("/run", response_model=DetectionRunResponse)
def trigger_detection(db: Session = Depends(get_db)):
    """
    Manually trigger the detection engine to analyze unprocessed security events
    and generate alerts.
    """
    engine = DetectionEngine(db)
    result = engine.run()
    return result
