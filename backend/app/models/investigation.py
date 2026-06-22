from datetime import datetime
from typing import Optional
from sqlalchemy import String, Integer, DateTime, JSON, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func
from app.database.base_class import Base

class Investigation(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    alert_id: Mapped[int] = mapped_column(
        ForeignKey("alert.id", ondelete="CASCADE"),
        nullable=False,
        index=True
    )
    customer_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False)
    
    investigation_summary: Mapped[str] = mapped_column(String, nullable=False, default="")
    evidence: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    tool_outputs: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict)
    reasoning_trace: Mapped[list] = mapped_column(JSON, nullable=False, default=list)
    
    risk_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    confidence_score: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    recommended_action: Mapped[str] = mapped_column(String(255), nullable=False, default="")
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        index=True,
        nullable=False
    )

    # Note: If we wanted to, we could define a relationship back to Alert
    # alert: Mapped["Alert"] = relationship("Alert")
