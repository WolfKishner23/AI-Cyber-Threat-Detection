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
    
    # Initialize state (Phase 6: include new fields)
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
        "risk_level": "",
        "llm_reasoning": "",
        "recommended_action": "",
        "investigation_status": "pending",
        "reasoning_trace": []
    }

    config = {"configurable": {"db": session}}
    
    # Execute graph
    final_state = investigation_graph.invoke(initial_state, config=config)
    
    # Phase 4 assertions (preserved)
    assert final_state["recommended_action"] == "lock_account"
    assert final_state["investigation_status"] == "completed"
    assert "brute_force" in final_state["investigation_summary"]
    
    # Phase 5 assertions (preserved)
    assert "user_history" in final_state["evidence"]
    assert "device_history" in final_state["evidence"]
    assert "location_history" in final_state["evidence"]
    assert "previous_alerts" in final_state["evidence"]
    assert "incident_history" in final_state["evidence"]
    assert "ip_reputation" in final_state["evidence"]
    assert "tool_outputs" in final_state
    assert "user_history" in final_state["tool_outputs"]
    
    # Phase 6 assertions (new)
    assert final_state["risk_score"] >= 0
    assert final_state["risk_score"] <= 100
    assert final_state["confidence_score"] >= 0
    assert final_state["confidence_score"] <= 100
    assert final_state["risk_level"] in ["low", "medium", "high", "critical"]
    assert len(final_state["llm_reasoning"]) > 0
    
    # Reasoning trace
    assert len(final_state["reasoning_trace"]) > 0
    assert any("LLM Risk Assessment Agent" in t for t in final_state["reasoning_trace"])

