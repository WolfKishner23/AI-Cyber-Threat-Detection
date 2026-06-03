import pytest
from fastapi.testclient import TestClient

def test_read_root(client: TestClient):
    response = client.get("/")
    assert response.status_code == 200
    json_data = response.json()
    assert json_data["status"] == "healthy"
    assert "documentation" in json_data

def test_create_security_event_success(client: TestClient):
    payload = {
        "user_id": "usr_9876",
        "event_type": "suspicious_login",
        "location": "New York, USA",
        "ip_address": "192.168.1.105",
        "device_name": "Rohan-Laptop",
        "raw_payload": {"failure_count": 3, "mfa_prompted": False}
    }
    response = client.post("/api/v1/events/", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["user_id"] == payload["user_id"]
    assert data["event_type"] == payload["event_type"]
    assert data["ip_address"] == payload["ip_address"]
    assert "id" in data
    assert "timestamp" in data

def test_create_security_event_invalid_ip(client: TestClient):
    payload = {
        "user_id": "usr_1234",
        "event_type": "api_anomaly",
        "ip_address": "999.999.999.999", # Invalid IP address format
        "raw_payload": {}
    }
    response = client.post("/api/v1/events/", json=payload)
    assert response.status_code == 422 # Pydantic validation error

def test_get_security_events_and_filtering(client: TestClient):
    # Setup test events
    event1 = {
        "user_id": "usr_alice",
        "event_type": "data_leak",
        "ip_address": "10.0.0.5",
        "raw_payload": {}
    }
    event2 = {
        "user_id": "usr_bob",
        "event_type": "ssh_login",
        "ip_address": "8.8.8.8",
        "raw_payload": {}
    }
    client.post("/api/v1/events/", json=event1)
    client.post("/api/v1/events/", json=event2)

    # Test get all
    response = client.get("/api/v1/events/")
    assert response.status_code == 200
    events = response.json()
    assert len(events) >= 2

    # Test filtering by event_type
    response = client.get("/api/v1/events/?event_type=data_leak")
    assert response.status_code == 200
    filtered_events = response.json()
    assert len(filtered_events) == 1
    assert filtered_events[0]["user_id"] == "usr_alice"

    # Test filtering by user_id
    response = client.get("/api/v1/events/?user_id=usr_bob")
    assert response.status_code == 200
    filtered_events = response.json()
    assert len(filtered_events) == 1
    assert filtered_events[0]["event_type"] == "ssh_login"

def test_get_security_event_by_id(client: TestClient):
    event_payload = {
        "user_id": "usr_charlie",
        "event_type": "privilege_escalation",
        "ip_address": "127.0.0.1",
        "raw_payload": {}
    }
    post_response = client.post("/api/v1/events/", json=event_payload)
    event_id = post_response.json()["id"]

    # Retrieve by ID
    response = client.get(f"/api/v1/events/{event_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["user_id"] == "usr_charlie"

    # Retrieve non-existing ID
    response = client.get("/api/v1/events/99999")
    assert response.status_code == 404

def test_create_alert_success(client: TestClient):
    # First, create a security event
    event_payload = {
        "user_id": "usr_admin",
        "event_type": "malware_execution",
        "ip_address": "192.168.1.1",
        "raw_payload": {}
    }
    event_response = client.post("/api/v1/events/", json=event_payload)
    event_id = event_response.json()["id"]

    # Create alert referencing this event
    alert_payload = {
        "event_id": event_id,
        "alert_type": "high_severity_malware",
        "severity": "critical",
        "status": "open"
    }
    alert_response = client.post("/api/v1/alerts/", json=alert_payload)
    assert alert_response.status_code == 201
    alert_data = alert_response.json()
    assert alert_data["event_id"] == event_id
    assert alert_data["severity"] == "critical"
    assert alert_data["status"] == "open"
    assert alert_data["event"]["user_id"] == "usr_admin" # Lazy relationship loading verified

def test_create_alert_invalid_event_id(client: TestClient):
    alert_payload = {
        "event_id": 1234567, # Non-existent event ID
        "alert_type": "unlinked_alert",
        "severity": "low",
        "status": "open"
    }
    response = client.post("/api/v1/alerts/", json=alert_payload)
    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]

def test_get_alerts_filtering_and_retrieval(client: TestClient):
    # Setup database records
    ev_resp = client.post("/api/v1/events/", json={
        "user_id": "system",
        "event_type": "cron_job",
        "ip_address": "127.0.0.1",
        "raw_payload": {}
    })
    ev_id = ev_resp.json()["id"]

    # Add multiple alerts
    client.post("/api/v1/alerts/", json={
        "event_id": ev_id,
        "alert_type": "warning_threshold",
        "severity": "medium",
        "status": "investigating"
    })
    client.post("/api/v1/alerts/", json={
        "event_id": ev_id,
        "alert_type": "critical_breach",
        "severity": "critical",
        "status": "open"
    })

    # Test get all alerts
    response = client.get("/api/v1/alerts/")
    assert response.status_code == 200
    alerts = response.json()
    assert len(alerts) >= 2

    # Test filter by severity
    response = client.get("/api/v1/alerts/?severity=critical")
    assert response.status_code == 200
    critical_alerts = response.json()
    assert any(a["alert_type"] == "critical_breach" for a in critical_alerts)
    assert all(a["severity"] == "critical" for a in critical_alerts)

    # Test filter by status
    response = client.get("/api/v1/alerts/?status=investigating")
    assert response.status_code == 200
    investigating_alerts = response.json()
    assert all(a["status"] == "investigating" for a in investigating_alerts)
