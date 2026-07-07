from sqlalchemy import String, Integer, ForeignKey, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.database.base_class import Base
from datetime import datetime


class Customer(Base):
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(255), index=True, nullable=False, unique=True)
    full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    account_number: Mapped[str] = mapped_column(String(50), nullable=False)


class TrustedDevice(Base):
    """Stores pre-assigned trusted devices for each customer.
    Used during login to pick a realistic device fingerprint."""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(255), ForeignKey("customer.customer_id"), index=True, nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    device_name: Mapped[str] = mapped_column(String(255), nullable=False)
    browser: Mapped[str] = mapped_column(String(100), nullable=False)
    operating_system: Mapped[str] = mapped_column(String(100), nullable=False)


class LoginHistory(Base):
    """Stores every successful login. Forms the basis for Phase 3 anomaly detection."""
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    customer_id: Mapped[str] = mapped_column(String(255), ForeignKey("customer.customer_id"), index=True, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    location: Mapped[str] = mapped_column(String(255), nullable=True)
    ip_address: Mapped[str] = mapped_column(String(45), nullable=False)
    device_id: Mapped[str] = mapped_column(String(255), nullable=False)
    browser: Mapped[str] = mapped_column(String(100), nullable=True)
    operating_system: Mapped[str] = mapped_column(String(100), nullable=True)
