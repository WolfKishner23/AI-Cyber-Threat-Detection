import pytest
import json
from datetime import datetime, timedelta, timezone
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.detection.engine import DetectionEngine

def test_impossible_travel_detection(session):
    now = datetime.now(timezone.utc)
    # Event 1 in New York
    e1 = SecurityEvent(
        user_id="user_it",
        event_type="login",
        location="New York",
        ip_address="1.1.1.1",
        timestamp=now - timedelta(hours=2),
        raw_payload="{}"
    )
    # Event 2 in Tokyo (2 hours later)
    e2 = SecurityEvent(
        user_id="user_it",
        event_type="login",
        location="Tokyo",
        ip_address="2.2.2.2",
        timestamp=now,
        raw_payload="{}"
    )
    session.add(e1)
    session.add(e2)
    session.commit()

    engine = DetectionEngine(session)
    res = engine.run()
    
    alert = session.query(Alert).filter(
        Alert.alert_type == "impossible_travel",
        Alert.event_id == e2.id
    ).first()
    assert alert is not None
    assert alert.severity == "high"

def test_brute_force_detection(session):
    now = datetime.now(timezone.utc)
    for i in range(5):
        e = SecurityEvent(
            user_id="user_bf",
            event_type="failed_login",
            ip_address="127.0.0.1",
            timestamp=now - timedelta(minutes=4-i),
            raw_payload="{}"
        )
        session.add(e)
    
    session.commit()
    
    engine = DetectionEngine(session)
    res = engine.run()
    
    alert = session.query(Alert).filter(Alert.alert_type == "brute_force").first()
    assert alert is not None

def test_new_device_detection(session):
    now = datetime.now(timezone.utc)
    e = SecurityEvent(
        user_id="user_nd",
        event_type="login",
        ip_address="127.0.0.1",
        timestamp=now,
        raw_payload=json.dumps({"is_new_device": True})
    )
    session.add(e)
    session.commit()
    
    engine = DetectionEngine(session)
    res = engine.run()
    
    alert = session.query(Alert).filter(Alert.alert_type == "new_device_login").first()
    assert alert is not None

def test_successful_brute_force_detection(session):
    now = datetime.now(timezone.utc)
    for i in range(5):
        e = SecurityEvent(
            user_id="user_sbf",
            event_type="failed_login",
            ip_address="127.0.0.1",
            timestamp=now - timedelta(minutes=4-i),
            raw_payload="{}"
        )
        session.add(e)
        
    e_success = SecurityEvent(
        user_id="user_sbf",
        event_type="login",
        ip_address="127.0.0.1",
        timestamp=now + timedelta(seconds=10),
        raw_payload="{}"
    )
    session.add(e_success)
    
    session.commit()
    
    engine = DetectionEngine(session)
    engine.run()
    
    alert = session.query(Alert).filter(Alert.alert_type == "successful_brute_force").first()
    assert alert is not None
    assert alert.severity == "high"
