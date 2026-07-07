"""
Behavioral Analysis Engine  --  Phase 3

Runs immediately after every successful customer login. Compares the
current login context against LoginHistory and TrustedDevices to produce
a weighted risk score and a list of detected anomalies.

The findings are injected into the SecurityEvent's raw_payload so the
existing LangGraph investigation agents automatically receive them as
richer context -- without any changes to the agents themselves.

Anomaly checks
--------------
1. Impossible Travel      -- login from distant city within short window
2. New Device             -- device_id not in TrustedDevice table
3. New Location           -- city/country never seen in LoginHistory
4. Unusual Login Time     -- login hour far outside historical pattern
5. Multiple Failed Logins -- burst of FAILED_LOGIN events recently

Risk scoring weights (configurable)
------------------------------------
Impossible Travel   +50
New Device          +25
New Location        +20
Unusual Login Time  +15
Failed Attempts     +30  (scaled by count)
Trusted Device      -10
Known Location      -10

Final score clamped to 0-100.
"""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy.orm import Session

from app.models.customer import LoginHistory, TrustedDevice
from app.models.security_event import SecurityEvent

logger = logging.getLogger(__name__)

# ── Configurable thresholds ──────────────────────────────────────────────────
IMPOSSIBLE_TRAVEL_HOURS = 6          # max hours between distant-city logins
FAILED_LOGIN_WINDOW_MINUTES = 15     # look-back window for failed attempts
FAILED_LOGIN_THRESHOLD = 3           # minimum failures to flag
UNUSUAL_HOUR_DEVIATION = 3           # hours away from mean to flag

# ── Risk weights ─────────────────────────────────────────────────────────────
W_IMPOSSIBLE_TRAVEL   = 50
W_NEW_DEVICE          = 25
W_NEW_LOCATION        = 20
W_UNUSUAL_TIME        = 15
W_FAILED_ATTEMPTS     = 30
W_TRUSTED_DEVICE      = -10
W_KNOWN_LOCATION      = -10

# ── Approximate lat/lon for travel distance estimation ───────────────────────
CITY_COORDS: dict[str, tuple[float, float]] = {
    "Mumbai":    (19.07, 72.87),
    "Delhi":     (28.61, 77.20),
    "Bangalore": (12.97, 77.59),
    "Hyderabad": (17.38, 78.48),
    "Chennai":   (13.08, 80.27),
    "Pune":      (18.52, 73.85),
    "Kolkata":   (22.57, 88.36),
    "London":    (51.50, -0.12),
    "New York":  (40.71, -74.00),
    "Singapore": ( 1.35, 103.82),
    "Dubai":     (25.20, 55.27),
    # Simulator locations
    "London, UK":         (51.50, -0.12),
    "Tokyo, Japan":       (35.68, 139.69),
    "Berlin, Germany":    (52.52, 13.40),
    "San Francisco, USA": (37.77, -122.42),
    "Chicago, USA":       (41.88, -87.63),
    "Moscow, Russia":     (55.75, 37.61),
}


def _haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Great-circle distance between two points on earth (km)."""
    R = 6371
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1))
         * math.cos(math.radians(lat2))
         * math.sin(dlon / 2) ** 2)
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def _max_speed_kmh() -> float:
    """Max plausible travel speed (commercial aircraft cruising)."""
    return 950.0


# ── Public API ───────────────────────────────────────────────────────────────

class BehavioralFinding:
    """Represents a single anomaly finding."""
    def __init__(self, name: str, weight: int, detail: str):
        self.name = name
        self.weight = weight
        self.detail = detail

    def to_dict(self) -> dict[str, Any]:
        return {"name": self.name, "weight": self.weight, "detail": self.detail}


class BehavioralAnalysisResult:
    """Aggregated result of behavioral analysis."""
    def __init__(self):
        self.findings: list[BehavioralFinding] = []
        self.raw_score: int = 0

    def add(self, finding: BehavioralFinding) -> None:
        self.findings.append(finding)
        self.raw_score += finding.weight

    @property
    def risk_score(self) -> int:
        return max(0, min(100, self.raw_score))

    @property
    def risk_level(self) -> str:
        s = self.risk_score
        if s >= 81:
            return "critical"
        if s >= 61:
            return "high"
        if s >= 31:
            return "medium"
        return "low"

    @property
    def anomalies(self) -> list[str]:
        return [f.name for f in self.findings if f.weight > 0]

    def to_dict(self) -> dict[str, Any]:
        return {
            "risk_score": self.risk_score,
            "risk_level": self.risk_level,
            "anomalies": self.anomalies,
            "findings": [f.to_dict() for f in self.findings],
        }


def _normalize_ts(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt


def _exclude_current_login(
    history: list[LoginHistory],
    *,
    location: str,
    device_id: str,
    timestamp: datetime,
) -> list[LoginHistory]:
    """
    Drop the in-flight login if LoginHistory was persisted before analysis.
    Without this, impossible-travel compares the current city against itself.
    """
    if not history:
        return history

    current_ts = _normalize_ts(timestamp)
    filtered: list[LoginHistory] = []

    for entry in history:
        entry_ts = _normalize_ts(entry.timestamp)
        is_current = (
            entry.location == location
            and entry.device_id == device_id
            and abs((entry_ts - current_ts).total_seconds()) <= 5
        )
        if not is_current:
            filtered.append(entry)

    return filtered


def analyze_login(
    db: Session,
    customer_id: str,
    location: str,
    device_id: str,
    device_name: str,
    timestamp: datetime,
) -> BehavioralAnalysisResult:
    """
    Run all behavioral checks for a login attempt and return an aggregated
    risk result.
    """
    result = BehavioralAnalysisResult()

    history = (
        db.query(LoginHistory)
        .filter(LoginHistory.customer_id == customer_id)
        .order_by(LoginHistory.timestamp.desc())
        .limit(50)
        .all()
    )
    history = _exclude_current_login(
        history,
        location=location,
        device_id=device_id,
        timestamp=timestamp,
    )

    trusted_devices = (
        db.query(TrustedDevice)
        .filter(TrustedDevice.customer_id == customer_id)
        .all()
    )
    trusted_device_ids = {td.device_id for td in trusted_devices}

    # ── 1. Impossible Travel ─────────────────────────────────────────────────
    _check_impossible_travel(result, history, location, timestamp)

    # ── 2. New Device Detection ──────────────────────────────────────────────
    _check_new_device(result, trusted_device_ids, history, device_id, device_name)

    # ── 3. New Location Detection ────────────────────────────────────────────
    _check_new_location(result, history, location)

    # ── High Risk Location Detection ─────────────────────────────────────────
    _check_high_risk_location(result, location)

    # ── 4. Unusual Login Time ────────────────────────────────────────────────
    _check_unusual_time(result, history, timestamp)

    # ── 5. Multiple Failed Logins ────────────────────────────────────────────
    _check_failed_logins(result, db, customer_id, timestamp)

    # ── Bonuses: trusted device / known location ─────────────────────────────
    if device_id in trusted_device_ids:
        result.add(BehavioralFinding(
            "trusted_device", W_TRUSTED_DEVICE,
            f"Device {device_id} is a known trusted device."
        ))

    known_locations = {h.location for h in history if h.location}
    if location in known_locations:
        result.add(BehavioralFinding(
            "known_location", W_KNOWN_LOCATION,
            f"Location '{location}' has been used before."
        ))

    logger.info(
        "Behavioral analysis for %s: score=%d level=%s anomalies=%s",
        customer_id, result.risk_score, result.risk_level, result.anomalies,
    )
    return result


# ── Individual checks ────────────────────────────────────────────────────────

def _check_impossible_travel(
    result: BehavioralAnalysisResult,
    history: list[LoginHistory],
    current_location: str,
    current_time: datetime,
) -> None:
    if not history:
        return

    current_coords = CITY_COORDS.get(current_location)
    if not current_coords:
        return

    last = history[0]  # most recent login
    last_coords = CITY_COORDS.get(last.location)
    if not last_coords:
        return

    if last.location == current_location:
        return  # same city, no travel

    distance_km = _haversine_km(*last_coords, *current_coords)
    # Ensure timezone awareness for subtraction
    last_ts = _normalize_ts(last.timestamp)
    curr_ts = _normalize_ts(current_time)

    hours_elapsed = max((curr_ts - last_ts).total_seconds() / 3600, 0.01)
    required_speed = distance_km / hours_elapsed

    if hours_elapsed < IMPOSSIBLE_TRAVEL_HOURS and required_speed > _max_speed_kmh():
        result.add(BehavioralFinding(
            "impossible_travel", W_IMPOSSIBLE_TRAVEL,
            (f"Login from '{current_location}' only {hours_elapsed:.1f}h after "
             f"'{last.location}' ({distance_km:.0f} km apart, "
             f"would need {required_speed:.0f} km/h).")
        ))


def _check_new_device(
    result: BehavioralAnalysisResult,
    trusted_ids: set[str],
    history: list[LoginHistory],
    device_id: str,
    device_name: str,
) -> None:
    historical_devices = {h.device_id for h in history if h.device_id}
    all_known = trusted_ids | historical_devices

    if device_id not in all_known:
        result.add(BehavioralFinding(
            "new_device", W_NEW_DEVICE,
            f"Device '{device_name}' ({device_id}) has never been seen before."
        ))


def _check_new_location(
    result: BehavioralAnalysisResult,
    history: list[LoginHistory],
    location: str,
) -> None:
    if not history:
        # First ever login -- new location by definition but not alarming
        return
    known_locations = {h.location for h in history if h.location}
    if location not in known_locations:
        result.add(BehavioralFinding(
            "new_location", W_NEW_LOCATION,
            f"Location '{location}' has never been seen in login history."
        ))


def _check_unusual_time(
    result: BehavioralAnalysisResult,
    history: list[LoginHistory],
    current_time: datetime,
) -> None:
    if len(history) < 5:
        # Not enough data to establish a pattern
        return

    hours = [h.timestamp.hour for h in history]
    mean_hour = sum(hours) / len(hours)
    current_hour = current_time.hour

    # Circular distance (e.g. 23h vs 1h = 2h apart, not 22h)
    diff = abs(current_hour - mean_hour)
    circular_diff = min(diff, 24 - diff)

    if circular_diff > UNUSUAL_HOUR_DEVIATION:
        result.add(BehavioralFinding(
            "unusual_time", W_UNUSUAL_TIME,
            (f"Login at {current_hour}:00 UTC is {circular_diff:.0f}h away "
             f"from the usual pattern (mean {mean_hour:.0f}:00 UTC).")
        ))


def _check_failed_logins(
    result: BehavioralAnalysisResult,
    db: Session,
    customer_id: str,
    current_time: datetime,
) -> None:
    window_start = current_time - timedelta(minutes=FAILED_LOGIN_WINDOW_MINUTES)

    recent_failures = (
        db.query(SecurityEvent)
        .filter(
            SecurityEvent.user_id == customer_id,
            SecurityEvent.event_type == "failed_login",
            SecurityEvent.timestamp >= window_start,
        )
        .count()
    )

    if recent_failures >= FAILED_LOGIN_THRESHOLD:
        # Scale weight: base weight if exactly threshold, +5 per extra failure (max 2x)
        scaled_weight = min(W_FAILED_ATTEMPTS * 2,
                            W_FAILED_ATTEMPTS + (recent_failures - FAILED_LOGIN_THRESHOLD) * 5)
        result.add(BehavioralFinding(
            "multiple_failed_logins", scaled_weight,
            (f"{recent_failures} failed login attempts in the last "
             f"{FAILED_LOGIN_WINDOW_MINUTES} minutes.")
        ))

def _check_high_risk_location(
    result: BehavioralAnalysisResult,
    location: str,
) -> None:
    HIGH_RISK_DEMO_LOCATIONS = {
        "North Sentinel Island",
        "Pyongyang, North Korea",
        "Juba, South Sudan"
    }
    if location in HIGH_RISK_DEMO_LOCATIONS:
        result.add(BehavioralFinding(
            "malicious_ip", 100,
            f"Login attempt from a known high-risk demo location: {location}."
        ))
