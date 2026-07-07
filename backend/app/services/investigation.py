import logging
from app.database.session import SessionLocal
from app.models.alert import Alert
from app.models.investigation import Investigation
from app.investigation.graph import investigation_graph
from app.core.broadcaster import broadcaster
from fastapi.concurrency import run_in_threadpool
import asyncio

logger = logging.getLogger(__name__)

def _sync_run_investigation(alert_id: int):
    """Synchronous DB and LangGraph operations"""
    db = SessionLocal()
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            logger.error(f"Alert {alert_id} not found for investigation task.")
            return None
            
        event = alert.event
        if not event:
            logger.error(f"Security Event not found for Alert {alert_id}.")
            return None

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

        config = {"configurable": {"db": db}}
        final_state = investigation_graph.invoke(initial_state, config=config)
        
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
        db.refresh(investigation)
        
        return {
            "id": investigation.id,
            "alert_id": investigation.alert_id,
            "customer_id": investigation.customer_id,
            "risk_score": investigation.risk_score,
            "confidence_score": investigation.confidence_score,
            "recommended_action": investigation.recommended_action,
            "reasoning_trace": investigation.reasoning_trace,
            "created_at": investigation.created_at.isoformat() if investigation.created_at else None
        }
    except Exception as e:
        logger.error(f"Error in investigation task for alert {alert_id}: {e}")
        return None
    finally:
        db.close()

async def run_autonomous_investigation_task(alert_id: int):
    """Async wrapper to run the sync function in a threadpool and broadcast the result."""
    payload = await run_in_threadpool(_sync_run_investigation, alert_id)
    if payload:
        await broadcaster.broadcast("investigation_complete", payload)

