from datetime import datetime
from sqlalchemy import DateTime, Integer
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func
from app.database.base_class import Base

class DetectionRun(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    events_scanned: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    alerts_generated: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
