from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.investigation.graph import investigation_graph
from app.investigation.schemas import InvestigationResponse

router = APIRouter()

@router.post("/run/{alert_id}", response_model=InvestigationResponse)
def run_investigation(alert_id: int, db: Session = Depends(get_db)):
    # 1. Load Alert and SecurityEvent
    alert = db.query(Alert).filter(Alert.id == alert_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Alert not found")
        
    event = alert.event
    if not event:
        raise HTTPException(status_code=404, detail="Security Event not found for this Alert")

    # 2. Initialize State
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

    # 3. Execute LangGraph Workflow
    # We pass the db session in the config so the Evidence Collection Agent can use it
    config = {"configurable": {"db": db}}
    
    final_state = investigation_graph.invoke(initial_state, config=config)
    
    # 4. Map to Response Model
    return InvestigationResponse(
        alert_id=final_state.get("alert_id"),
        risk_score=final_state.get("risk_score", 0),
        confidence_score=final_state.get("confidence_score", 0),
        recommended_action=final_state.get("recommended_action", ""),
        investigation_summary=final_state.get("investigation_summary", ""),
        evidence=final_state.get("evidence", {}),
        reasoning_trace=final_state.get("reasoning_trace", [])
    )
