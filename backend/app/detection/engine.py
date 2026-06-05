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

class DetectionEngine:
    def __init__(self, db: Session):
        self.db = db
        # Initialize all rules
        self.rules: List[BaseDetectionRule] = [
            ImpossibleTravelRule(),
            BruteForceRule(),
            NewDeviceRule(),
        ]
        
    def get_unprocessed_events(self) -> List[SecurityEvent]:
        # Simplistic approach for MVP: fetch all events.
        # In a real system, you'd fetch events created after the last DetectionRun
        return self.db.query(SecurityEvent).all()

    def alert_exists(self, alert_create: AlertCreate) -> bool:
        """Check if an alert for this event and type already exists to avoid duplicates."""
        existing = self.db.query(Alert).filter(
            Alert.event_id == alert_create.event_id,
            Alert.alert_type == alert_create.alert_type
        ).first()
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
                        # Create alert
                        db_alert = Alert(**alert_data.model_dump())
                        self.db.add(db_alert)
                        alerts_generated += 1
            
            # Commit all new alerts
            self.db.commit()

        end_time = datetime.now(timezone.utc)
        
        # Record detection run
        run_record = DetectionRun(
            started_at=start_time,
            completed_at=end_time,
            events_scanned=events_scanned,
            alerts_generated=alerts_generated
        )
        self.db.add(run_record)
        self.db.commit()
        self.db.refresh(run_record)
        
        return DetectionRunResponse.model_validate(run_record)
