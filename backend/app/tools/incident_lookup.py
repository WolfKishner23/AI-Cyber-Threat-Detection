from sqlalchemy.orm import Session

def get_incident_history(db: Session, user_id: str) -> dict:
    """Lookup historical incidents (investigations) for a user."""
    # To be integrated with Phase 7 Investigation Memory
    if not user_id:
        return {"incidents": []}
        
    # Return empty list for now
    return {
        "incidents": []
    }
