from datetime import datetime
from pydantic import BaseModel, ConfigDict

class DetectionRunBase(BaseModel):
    events_scanned: int = 0
    alerts_generated: int = 0

class DetectionRunCreate(DetectionRunBase):
    started_at: datetime
    completed_at: datetime

class DetectionRunResponse(DetectionRunBase):
    id: int
    started_at: datetime
    completed_at: datetime

    model_config = ConfigDict(from_attributes=True)
