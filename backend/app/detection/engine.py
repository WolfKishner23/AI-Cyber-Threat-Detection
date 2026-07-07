from typing import List
from datetime import datetime, timezone
from sqlalchemy.orm import Session

from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.models.detection_run import DetectionRun

from app.schemas.alert import AlertCreate
from app.schemas.detection_run import DetectionRunResponse

from app.detection.rules.base import BaseDetectionRule
from app.detection.rules.impossible_travel import ImpossibleTravelRule
from app.detection.rules.brute_force import BruteForceRule
from app.detection.rules.new_device import NewDeviceRule
from app.detection.rules.high_risk_location import HighRiskLocationRule


from fastapi import BackgroundTasks
from app.services.investigation import run_autonomous_investigation_task
from app.core.broadcaster import broadcaster

class DetectionEngine:
    def __init__(self, db: Session, background_tasks: BackgroundTasks = None):
        self.db = db
        self.background_tasks = background_tasks

        self.rules: List[BaseDetectionRule] = [
            ImpossibleTravelRule(),
            BruteForceRule(),
            NewDeviceRule(),
            HighRiskLocationRule(),
        ]

    def get_unprocessed_events(self) -> List[SecurityEvent]:
        return self.db.query(SecurityEvent).all()

    def alert_exists(self, alert_create: AlertCreate) -> bool:
        existing = (
            self.db.query(Alert)
            .filter(
                Alert.event_id == alert_create.event_id,
                Alert.alert_type == alert_create.alert_type,
            )
            .first()
        )
        return existing is not None

    def run(self) -> DetectionRunResponse:
        start_time = datetime.now(timezone.utc)

        events = self.get_unprocessed_events()
        events_scanned = len(events)
        alerts_generated = 0

        if events:
            for rule in self.rules:
                new_alerts = rule.analyze(events)

                for alert_data in new_alerts:
                    if not self.alert_exists(alert_data):
                        db_alert = Alert(**alert_data.model_dump())
                        self.db.add(db_alert)
                        self.db.commit()
                        self.db.refresh(db_alert)
                        alerts_generated += 1

                        if self.background_tasks:
                            # 1. Broadcast the new alert
                            # Get the associated event for the broadcast payload
                            event = self.db.query(SecurityEvent).filter(SecurityEvent.id == db_alert.event_id).first()
                            
                            alert_sse = {
                                "id": db_alert.id,
                                "event_id": db_alert.event_id,
                                "alert_type": db_alert.alert_type,
                                "severity": db_alert.severity,
                                "status": db_alert.status,
                                "created_at": db_alert.created_at.isoformat() if db_alert.created_at else None,
                                "event": {
                                    "id": event.id,
                                    "user_id": event.user_id,
                                    "event_type": event.event_type,
                                    "location": event.location,
                                    "ip_address": event.ip_address,
                                    "device_name": event.device_name,
                                    "timestamp": event.timestamp.isoformat() if event.timestamp else None,
                                    "raw_payload": event.raw_payload,
                                } if event else None
                            }
                            self.background_tasks.add_task(broadcaster.broadcast, "new_alert", alert_sse)
                            
                            # 2. Trigger Autonomous Agent Investigation
                            self.background_tasks.add_task(run_autonomous_investigation_task, alert_id=db_alert.id)

            # We can commit all at the end or incrementally. We just committed incrementally above to get db_alert.id

        end_time = datetime.now(timezone.utc)

        run_record = DetectionRun(
            started_at=start_time,
            completed_at=end_time,
            events_scanned=events_scanned,
            alerts_generated=alerts_generated,
        )

        self.db.add(run_record)
        self.db.commit()
        self.db.refresh(run_record)

        return DetectionRunResponse.model_validate(run_record)