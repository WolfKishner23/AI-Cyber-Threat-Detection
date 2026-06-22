from sqlalchemy.orm import Session
from app.models.investigation import Investigation

def get_incident_history(db: Session, user_id: str) -> dict:
    """Lookup historical incidents (investigations) for a user."""
    if not user_id:
        return {"incidents": []}
        
    investigations = db.query(Investigation).filter(Investigation.customer_id == user_id).order_by(Investigation.created_at.desc()).limit(10).all()
    
    incidents = []
    for inv in investigations:
        incidents.append({
            "investigation_id": inv.id,
            "alert_id": inv.alert_id,
            "risk_score": inv.risk_score,
            "confidence_score": inv.confidence_score,
            "recommended_action": inv.recommended_action,
            "created_at": inv.created_at.isoformat() if inv.created_at else None,
            "summary": inv.investigation_summary
        })

    return {
        "incidents": incidents
    }
