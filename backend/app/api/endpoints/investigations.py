from typing import List
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.models.alert import Alert
from app.models.security_event import SecurityEvent
from app.models.investigation import Investigation
from app.investigation.graph import investigation_graph
from app.investigation.schemas import InvestigationResponse, InvestigationModel
from app.core.broadcaster import broadcaster

router = APIRouter()

@router.post("/run/{alert_id}", response_model=InvestigationResponse)
def run_investigation(
    alert_id: int, 
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
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
        "risk_level": "",
        "llm_reasoning": "",
        "recommended_action": "",
        "investigation_status": "pending",
        "reasoning_trace": [],
        "tools_used": []
    }

    # 3. Execute LangGraph Workflow
    config = {"configurable": {"db": db}}
    final_state = investigation_graph.invoke(initial_state, config=config)
    
    # Save the completed investigation to the database
    investigation = Investigation(
        alert_id=final_state.get("alert_id"),
        customer_id=event.user_id,
        investigation_summary=final_state.get("investigation_summary", ""),
        evidence=final_state.get("evidence", {}),
        tool_outputs=final_state.get("tool_outputs", {}),
        reasoning_trace=final_state.get("reasoning_trace", []),
        risk_score=final_state.get("risk_score", 0),
        confidence_score=final_state.get("confidence_score", 0),
        recommended_action=final_state.get("recommended_action", "")
    )
    db.add(investigation)
    db.commit()
    
    payload = {
        "id": investigation.id,
        "alert_id": investigation.alert_id,
        "customer_id": investigation.customer_id,
        "risk_score": investigation.risk_score,
        "confidence_score": investigation.confidence_score,
        "recommended_action": investigation.recommended_action,
        "reasoning_trace": investigation.reasoning_trace,
        "created_at": investigation.created_at.isoformat() if investigation.created_at else None
    }
    background_tasks.add_task(broadcaster.broadcast, "investigation_complete", payload)
    
    # 4. Map to Response Model
    return InvestigationResponse(
        alert_id=final_state.get("alert_id"),
        risk_score=final_state.get("risk_score", 0),
        confidence_score=final_state.get("confidence_score", 0),
        risk_level=final_state.get("risk_level", ""),
        recommended_action=final_state.get("recommended_action", ""),
        investigation_summary=final_state.get("investigation_summary", ""),
        evidence=final_state.get("evidence", {}),
        tool_outputs=final_state.get("tool_outputs", {}),
        llm_reasoning=final_state.get("llm_reasoning", ""),
        reasoning_trace=final_state.get("reasoning_trace", []),
        tools_used=final_state.get("tools_used", [])
    )

@router.get("/", response_model=List[InvestigationModel])
def list_investigations(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    investigations = db.query(Investigation).order_by(Investigation.created_at.desc()).offset(skip).limit(limit).all()
    return investigations

@router.get("/{investigation_id}", response_model=InvestigationModel)
def get_investigation(investigation_id: int, db: Session = Depends(get_db)):
    investigation = db.query(Investigation).filter(Investigation.id == investigation_id).first()
    if not investigation:
        raise HTTPException(status_code=404, detail="Investigation not found")
    return investigation

@router.get("/customer/{customer_id}", response_model=List[InvestigationModel])
def list_customer_investigations(customer_id: str, db: Session = Depends(get_db)):
    investigations = db.query(Investigation).filter(Investigation.customer_id == customer_id).order_by(Investigation.created_at.desc()).all()
    return investigations
