import pytest
from sqlalchemy.orm import Session
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.tools import (
    get_user_history,
    get_device_history,
    get_location_history,
    get_previous_alerts,
    get_incident_history,
    get_ip_reputation
)

def test_user_history_tool(session: Session):
    event = SecurityEvent(user_id="user1", event_type="login", ip_address="1.1.1.1")
    session.add(event)
    session.commit()
    
    result = get_user_history(session, "user1")
    assert isinstance(result, dict)
    assert result["event_count"] == 1
    assert len(result["recent_events"]) == 1
    assert result["recent_events"][0]["type"] == "login"

def test_device_history_tool(session: Session):
    event = SecurityEvent(user_id="user2", event_type="login", ip_address="1.1.1.1", device_name="MacBook")
    session.add(event)
    session.commit()
    
    result = get_device_history(session, "user2")
    assert isinstance(result, dict)
    assert "MacBook" in result["devices"]
    assert result["frequencies"]["MacBook"] == 1

def test_location_history_tool(session: Session):
    event = SecurityEvent(user_id="user3", event_type="login", ip_address="1.1.1.1", location="Paris")
    session.add(event)
    session.commit()
    
    result = get_location_history(session, "user3")
    assert isinstance(result, dict)
    assert "Paris" in result["locations"]
    assert result["frequencies"]["Paris"] == 1

def test_previous_alerts_tool(session: Session):
    event = SecurityEvent(user_id="user4", event_type="login", ip_address="1.1.1.1", location="Berlin")
    session.add(event)
    session.commit()
    
    alert = Alert(event_id=event.id, alert_type="impossible_travel", severity="high", status="new")
    session.add(alert)
    session.commit()
    
    result = get_previous_alerts(session, "user4")
    assert isinstance(result, dict)
    assert result["alert_count"] == 1
    assert result["severities"]["high"] == 1

def test_incident_lookup_tool(session: Session):
    result = get_incident_history(session, "user5")
    assert isinstance(result, dict)
    assert result["incidents"] == []

def test_ip_reputation_tool():
    # Private IP
    result = get_ip_reputation("10.0.0.1")
    assert result["reputation"] == "trusted"
    
    # Tor IP
    result = get_ip_reputation("198.51.100.12")
    assert result["reputation"] == "malicious"
    
    # Unknown
    result = get_ip_reputation("8.8.8.8")
    assert result["reputation"] == "unknown"
