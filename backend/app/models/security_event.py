from datetime import datetime
from typing import List, Optional
from sqlalchemy import String, DateTime, JSON
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class SecurityEvent(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    user_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    event_type: Mapped[str] = mapped_column(String(100), index=True, nullable=False)
    location: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), index=True, nullable=False)
    device_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    target_resource: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    
    # We use server_default=func.now() so database server handles time,
    # and default=datetime.utcnow for application level fallback.
    timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False
    )
    
    # Stores raw, unstructured event data (JSON)
    raw_payload: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)

    # One-to-many relationship with Alert
    # When a SecurityEvent is deleted, cascade-delete all its related alerts
    alerts: Mapped[List["Alert"]] = relationship(
        "Alert",
        back_populates="event",
        cascade="all, delete-orphan"
    )
