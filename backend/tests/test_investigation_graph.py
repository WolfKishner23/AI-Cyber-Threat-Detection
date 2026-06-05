import pytest
from app.investigation.graph import investigation_graph
from app.investigation.state import InvestigationState
from sqlalchemy.orm import Session
from app.models.security_event import SecurityEvent
from app.models.alert import Alert

def test_investigation_graph_workflow(session: Session):
    # Setup dummy data in the test DB
    event = SecurityEvent(
        user_id="test_user",
        event_type="login_failed",
        ip_address="192.168.1.1",
        device_name="Desktop-1",
        location="NY"
    )
    session.add(event)
    session.commit()
    session.refresh(event)

    alert = Alert(
        event_id=event.id,
        alert_type="brute_force",
        severity="high",
        status="new"
    )
    session.add(alert)
    session.commit()
    session.refresh(alert)
    
    # Initialize state
    initial_state = {
        "alert_id": alert.id,
        "alert": {
            "id": alert.id,
            "alert_type": alert.alert_type,
            "severity": alert.severity,
            "status": alert.status
        },
        "security_event": {
            "id": event.id,
            "user_id": event.user_id,
            "event_type": event.event_type,
            "location": event.location,
            "ip_address": event.ip_address,
            "device_name": event.device_name
        },
        "investigation_summary": "",
        "evidence": {},
        "risk_score": 0,
        "confidence_score": 0,
        "recommended_action": "",
        "investigation_status": "pending",
        "reasoning_trace": []
    }

    config = {"configurable": {"db": session}}
    
    # Execute graph
    final_state = investigation_graph.invoke(initial_state, config=config)
    
    assert final_state["risk_score"] == 95
    assert final_state["recommended_action"] == "lock_account"
    assert "in_progress" not in final_state["investigation_status"]
    assert final_state["investigation_status"] == "completed"
    assert "brute_force" in final_state["investigation_summary"]
    
    # Check evidence collection
    assert "recent_events" in final_state["evidence"]
    
    # Check reasoning trace
    assert len(final_state["reasoning_trace"]) > 0
