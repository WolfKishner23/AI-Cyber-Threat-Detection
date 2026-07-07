"""Tests for Phase 3 behavioral login analysis."""
from datetime import datetime, timedelta, timezone

from app.models.customer import Customer, LoginHistory, TrustedDevice
from app.detection.behavioral import analyze_login


def _seed_customer(session, customer_id: str = "CUST1001") -> None:
    session.add(Customer(
        customer_id=customer_id,
        full_name="Aarav Sharma",
        password="Aarav@123",
        email="aarav.sharma@bankdemo.com",
        account_number="123456789012",
    ))
    session.add(TrustedDevice(
        customer_id=customer_id,
        device_id="DEV-AARAV-LAPTOP",
        device_name="Windows Laptop",
        browser="Chrome",
        operating_system="Windows 11",
    ))
    session.commit()


def test_impossible_travel_after_prior_login(session):
    """London login should flag impossible travel when Mumbai was logged in minutes ago."""
    _seed_customer(session)
    mumbai_ts = datetime.now(timezone.utc) - timedelta(minutes=2)
    session.add(LoginHistory(
        customer_id="CUST1001",
        timestamp=mumbai_ts,
        location="Mumbai",
        ip_address="103.21.1.1",
        device_id="DEV-AARAV-LAPTOP",
        browser="Chrome",
        operating_system="Windows 11",
    ))
    session.commit()

    result = analyze_login(
        db=session,
        customer_id="CUST1001",
        location="London",
        device_id="DEV-AARAV-LAPTOP",
        device_name="Windows Laptop",
        timestamp=datetime.now(timezone.utc),
    )

    assert "impossible_travel" in result.anomalies
    assert result.risk_score >= 61
    assert result.risk_level in ("high", "critical")


def test_current_login_excluded_when_already_persisted(session):
    """If LoginHistory was saved before analysis, ignore it and use the prior login."""
    _seed_customer(session)
    now = datetime.now(timezone.utc)
    mumbai_ts = now - timedelta(minutes=2)
    london_ts = now

    session.add(LoginHistory(
        customer_id="CUST1001",
        timestamp=mumbai_ts,
        location="Mumbai",
        ip_address="103.21.1.1",
        device_id="DEV-AARAV-LAPTOP",
        browser="Chrome",
        operating_system="Windows 11",
    ))
    session.add(LoginHistory(
        customer_id="CUST1001",
        timestamp=london_ts,
        location="London",
        ip_address="51.148.1.1",
        device_id="DEV-AARAV-LAPTOP",
        browser="Chrome",
        operating_system="Windows 11",
    ))
    session.commit()

    result = analyze_login(
        db=session,
        customer_id="CUST1001",
        location="London",
        device_id="DEV-AARAV-LAPTOP",
        device_name="Windows Laptop",
        timestamp=london_ts,
    )

    assert "impossible_travel" in result.anomalies
    assert result.risk_score > 30


def test_customer_login_endpoint_impossible_travel(client, session):
    """End-to-end: Mumbai login then London login triggers alert-worthy risk."""
    _seed_customer(session)

    mumbai = client.post("/api/v1/customer/login", json={
        "customer_id": "CUST1001",
        "password": "Aarav@123",
        "location": "Mumbai",
    })
    assert mumbai.status_code == 200
    assert mumbai.json()["risk_score"] == 0

    london = client.post("/api/v1/customer/login", json={
        "customer_id": "CUST1001",
        "password": "Aarav@123",
        "location": "London",
    })
    assert london.status_code == 200
    body = london.json()
    assert body["risk_level"] in ("high", "critical")
    assert "impossible_travel" in body["anomalies"]
    assert body["risk_score"] > 30

    alerts = client.get("/api/v1/alerts/").json()
    assert any(a["alert_type"] == "impossible_travel" for a in alerts)
