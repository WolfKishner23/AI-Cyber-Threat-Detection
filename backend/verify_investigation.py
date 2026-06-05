import sys
import os

# Add backend to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.simulators.event_generator import run_scenario
from app.detection.engine import DetectionEngine
from app.investigation.graph import investigation_graph
from app.models.alert import Alert

def verify():
    db: Session = SessionLocal()
    
    print("\n1. Running Detection Engine to generate Alerts...")
    engine = DetectionEngine(db)
    result = engine.run()
    print(f"   Events scanned: {result.events_scanned}")
    print(f"   Alerts generated: {result.alerts_generated}")
    
    print("\n3. Finding an Alert to investigate...")
    alert = db.query(Alert).first()
    if not alert:
        print("No alerts found in database!")
        return
    print(f"   Found Alert ID {alert.id} of type {alert.alert_type}")
    
    print("\n4. Running Investigation Workflow...")
    event = alert.event
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
    config = {"configurable": {"db": db}}
    final_state = investigation_graph.invoke(initial_state, config=config)
    
    print("\n=== Investigation Result ===")
    print(f"Risk Score: {final_state['risk_score']}")
    print(f"Recommended Action: {final_state['recommended_action']}")
    print(f"Summary: {final_state['investigation_summary']}")
    print("\nEvidence Collected:")
    for key, val in final_state['evidence'].items():
        print(f" - {key}: {len(val)} items")
    print("\nReasoning Trace:")
    for t in final_state['reasoning_trace']:
        print(f" > {t}")

if __name__ == "__main__":
    verify()
