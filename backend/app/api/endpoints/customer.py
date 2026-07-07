"""
Customer Authentication Endpoint  --  Phase 2 + Phase 3

POST /api/v1/customer/login

Phase 2:  Validates credentials, generates metadata, creates SecurityEvent,
          broadcasts via SSE, triggers Detection Engine.
Phase 3:  Runs Behavioral Analysis after successful login, enriches the
          SecurityEvent raw_payload with risk findings, and creates an Alert
          when the risk score exceeds threshold.
"""

import uuid
import random
import httpx
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy.orm.attributes import flag_modified

from app.database.session import get_db
from app.models.customer import Customer, TrustedDevice, LoginHistory
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.schemas.customer import CustomerLogin, CustomerLoginResponseV2
from app.schemas.security_event import SecurityEventCreate
from app.services.security_event import create_security_event
from app.core.broadcaster import broadcaster
from app.detection.behavioral import analyze_login
from app.services.investigation import run_autonomous_investigation_task

logger = logging.getLogger(__name__)

router = APIRouter()

# ── In-memory state for Brute Force Counter ─────────────────────────────────
FAILED_ATTEMPTS: dict[str, int] = {}
MAX_FAILED_ATTEMPTS = 3

# ── Risk threshold for alert generation ──────────────────────────────────────
ALERT_RISK_THRESHOLD = 30   # Create alert when score > 30

# ── Location -> realistic public IP prefix mapping ──────────────────────────
LOCATION_IP_RANGES: dict[str, list[str]] = {
    "Mumbai":    ["103.21", "103.26", "103.47", "103.85"],
    "Delhi":     ["49.36",  "49.43",  "49.205", "49.249"],
    "Bangalore": ["14.139", "14.140", "14.142", "14.143"],
    "Hyderabad": ["27.97",  "27.98",  "27.254", "117.200"],
    "Chennai":   ["59.90",  "59.144", "103.4",  "106.208"],
    "Pune":      ["1.22",   "1.23",   "49.204", "110.225"],
    "Kolkata":   ["103.248","115.110","122.162","157.33"],
    "London":    ["51.148", "51.149", "51.36",  "51.68"],
    "New York":  ["44.192", "44.201", "44.208", "44.214"],
    "Singapore": ["43.218", "43.229", "43.249", "103.246"],
    "Dubai":     ["86.96",  "86.97",  "194.29", "80.249"],
    "North Sentinel Island":  ["192.0"],
    "Pyongyang, North Korea": ["175.45"],
    "Juba, South Sudan":      ["197.232"],
}
DEFAULT_IP_PREFIX = "10.0"


def _generate_ip(location: str) -> str:
    prefixes = LOCATION_IP_RANGES.get(location, [DEFAULT_IP_PREFIX])
    prefix = random.choice(prefixes)
    return f"{prefix}.{random.randint(1, 254)}.{random.randint(1, 254)}"


def _build_customer_profile(customer: Customer) -> dict:
    return {
        "customer_id": customer.customer_id,
        "full_name": customer.full_name,
        "email": customer.email,
        "account_number": customer.account_number,
    }


def _risk_to_severity(risk_level: str) -> str:
    """Map behavioral risk_level to Alert severity enum value."""
    return {
        "critical": "critical",
        "high": "high",
        "medium": "medium",
        "low": "low",
    }.get(risk_level, "medium")


def _anomalies_to_alert_type(anomalies: list[str]) -> str:
    """Build a descriptive alert_type from the list of anomaly names."""
    if not anomalies:
        return "behavioral_risk"
    # Use the highest-weight anomaly as the primary alert type
    priority = [
        "impossible_travel",
        "multiple_failed_logins",
        "new_device",
        "new_location",
        "unusual_time",
    ]
    for p in priority:
        if p in anomalies:
            return p
    return anomalies[0]


@router.post(
    "/login",
    response_model=CustomerLoginResponseV2,
    response_model_exclude_unset=False,
    response_model_exclude_defaults=False,
    response_model_exclude_none=False,
    summary="Customer Login",
    description=(
        "Authenticates a banking customer, generates a SecurityEvent, runs "
        "behavioral analysis to detect anomalies, and creates alerts when "
        "the risk score exceeds the configured threshold."
    ),
)
async def customer_login(
    payload: CustomerLogin,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
) -> CustomerLoginResponseV2:

    # ── 1. Look up customer ──────────────────────────────────────────────────
    customer = (
        db.query(Customer)
        .filter(Customer.customer_id == payload.customer_id)
        .first()
    )

    # ── 2. Generate metadata ─────────────────────────────────────────────────
    ip_address = _generate_ip(payload.location)
    timestamp  = datetime.now(timezone.utc)
    session_id = str(uuid.uuid4())

    trusted_devices = (
        db.query(TrustedDevice)
        .filter(TrustedDevice.customer_id == payload.customer_id)
        .all()
        if customer else []
    )
    if trusted_devices:
        device = random.choice(trusted_devices)
        device_id        = device.device_id
        device_name      = device.device_name
        browser          = device.browser
        operating_system = device.operating_system
    else:
        device_id        = f"DEV-UNKNOWN-{uuid.uuid4().hex[:8].upper()}"
        device_name      = "Web Browser"
        browser          = "Chrome"
        operating_system = "Windows 11"

    customer_profile = _build_customer_profile(customer) if customer else {
        "customer_id": payload.customer_id,
        "full_name": "Unknown",
    }

    # ── 3. Authenticate ──────────────────────────────────────────────────────
    auth_success = customer is not None and customer.password == payload.password

    if auth_success and payload.customer_id in FAILED_ATTEMPTS:
        del FAILED_ATTEMPTS[payload.customer_id]

    # ── 4. Build raw_payload ─────────────────────────────────────────────────
    raw_payload: dict = {
        "status": "success" if auth_success else "failed",
        "session_id": session_id,
        "device_id": device_id,
        "browser": browser,
        "operating_system": operating_system,
        "source": "customer_login",
        "simulation": {
            "scenario": "real_customer_login",
            "scenario_id": session_id,
            "is_attack": False,
            "customer_profile": customer_profile,
        },
    }
    if not auth_success:
        raw_payload["failure_reason"] = (
            "invalid_password" if customer else "user_not_found"
        )

    # ── 5. Create SecurityEvent ──────────────────────────────────────────────
    event_type = "login" if auth_success else "failed_login"
    event_in = SecurityEventCreate(
        user_id=payload.customer_id,
        event_type=event_type,
        location=payload.location,
        ip_address=ip_address,
        device_name=device_name,
        timestamp=timestamp,
        raw_payload=raw_payload,
    )
    db_event: SecurityEvent = create_security_event(db=db, obj_in=event_in)

    # ── 6. Behavioral Analysis (Phase 3) ─────────────────────────────────────
    risk_score = 0
    risk_level = "low"
    anomalies: list[str] = []

    if auth_success and customer:
        # Run behavioral analysis against history (which does NOT include current yet)
        analysis = analyze_login(
            db=db,
            customer_id=customer.customer_id,
            location=payload.location,
            device_id=device_id,
            device_name=device_name,
            timestamp=timestamp,
        )
        risk_score = analysis.risk_score
        risk_level = analysis.risk_level
        anomalies  = analysis.anomalies

        # Save LoginHistory AFTER behavioral analysis
        history = LoginHistory(
            customer_id=customer.customer_id,
            timestamp=timestamp,
            location=payload.location,
            ip_address=ip_address,
            device_id=device_id,
            browser=browser,
            operating_system=operating_system,
        )
        db.add(history)
        db.commit()

        # Enrich the SecurityEvent raw_payload with behavioral findings
        enriched = dict(db_event.raw_payload)
        enriched["behavioral_analysis"] = analysis.to_dict()
        db_event.raw_payload = enriched
        flag_modified(db_event, "raw_payload")
        db.add(db_event)
        db.commit()
        db.refresh(db_event)

        # ── 6b. Create Alert if risk exceeds threshold ───────────────────────
        if risk_score > ALERT_RISK_THRESHOLD and anomalies:
            alert_type = _anomalies_to_alert_type(anomalies)
            severity = _risk_to_severity(risk_level)

            # Avoid duplicate: check if alert for this event+type exists
            existing = (
                db.query(Alert)
                .filter(Alert.event_id == db_event.id,
                        Alert.alert_type == alert_type)
                .first()
            )
            if not existing:
                new_alert = Alert(
                    event_id=db_event.id,
                    alert_type=alert_type,
                    severity=severity,
                    status="open",
                )
                db.add(new_alert)
                db.commit()
                db.refresh(new_alert)
                logger.info(
                    "Behavioral alert created: id=%d type=%s severity=%s score=%d",
                    new_alert.id, alert_type, severity, risk_score,
                )
                # Broadcast the new alert via SSE
                alert_sse = {
                    "id": new_alert.id,
                    "event_id": new_alert.event_id,
                    "alert_type": new_alert.alert_type,
                    "severity": new_alert.severity,
                    "status": new_alert.status,
                    "created_at": new_alert.created_at.isoformat() if new_alert.created_at else None,
                    "event": {
                        "id": db_event.id,
                        "user_id": db_event.user_id,
                        "event_type": db_event.event_type,
                        "location": db_event.location,
                        "ip_address": db_event.ip_address,
                        "device_name": db_event.device_name,
                        "timestamp": db_event.timestamp.isoformat(),
                        "raw_payload": db_event.raw_payload,
                    }
                }
                background_tasks.add_task(
                    broadcaster.broadcast, "new_alert", alert_sse
                )
                
                # Trigger Autonomous Agent Investigation for the behavioral alert
                background_tasks.add_task(run_autonomous_investigation_task, alert_id=new_alert.id)

    # ── 7. Broadcast event via SSE ───────────────────────────────────────────
    sse_payload = {
        "id": db_event.id,
        "user_id": db_event.user_id,
        "event_type": db_event.event_type,
        "ip_address": db_event.ip_address,
        "timestamp": db_event.timestamp.isoformat(),
    }
    background_tasks.add_task(broadcaster.broadcast, "new_event", sse_payload)

    # ── 8. Trigger the Detection Engine (fire-and-forget) ────────────────────
    background_tasks.add_task(_trigger_detection_engine)

    # ── 9. Return result ─────────────────────────────────────────────────────
    if not auth_success:
        failed_count = FAILED_ATTEMPTS.get(payload.customer_id, 0) + 1
        FAILED_ATTEMPTS[payload.customer_id] = failed_count
        attempts_remaining = max(0, MAX_FAILED_ATTEMPTS - failed_count)

        if attempts_remaining == 0:
            # Create brute force alert
            existing_alert = db.query(Alert).filter(
                Alert.event_id == db_event.id,
                Alert.alert_type == "brute_force"
            ).first()
            
            if not existing_alert:
                new_alert = Alert(
                    event_id=db_event.id,
                    alert_type="brute_force",
                    severity="critical",
                    status="open",
                )
                db.add(new_alert)
                db.commit()
                db.refresh(new_alert)
                
                # Broadcast via SSE
                alert_sse = {
                    "id": new_alert.id,
                    "event_id": new_alert.event_id,
                    "alert_type": new_alert.alert_type,
                    "severity": new_alert.severity,
                    "status": new_alert.status,
                    "created_at": new_alert.created_at.isoformat() if new_alert.created_at else None,
                    "event": {
                        "id": db_event.id,
                        "user_id": db_event.user_id,
                        "event_type": db_event.event_type,
                        "location": db_event.location,
                        "ip_address": db_event.ip_address,
                        "device_name": db_event.device_name,
                        "timestamp": db_event.timestamp.isoformat(),
                        "raw_payload": db_event.raw_payload,
                    }
                }
                background_tasks.add_task(broadcaster.broadcast, "new_alert", alert_sse)
                
                # Trigger Investigation
                background_tasks.add_task(run_autonomous_investigation_task, alert_id=new_alert.id)

        return JSONResponse(
            status_code=status.HTTP_401_UNAUTHORIZED,
            content={
                "detail": {
                    "success": False,
                    "message": "Invalid Customer ID or Password",
                    "attempts_remaining": attempts_remaining
                }
            },
            background=background_tasks
        )

    return CustomerLoginResponseV2(
        success=True,
        customer_name=customer.full_name,
        customer_id=customer.customer_id,
        account_number=customer.account_number,
        risk_score=risk_score,
        risk_level=risk_level,
        anomalies=anomalies,
    )


async def _trigger_detection_engine() -> None:
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            await client.post("http://127.0.0.1:8001/api/v1/detection/run")
    except Exception:
        pass
