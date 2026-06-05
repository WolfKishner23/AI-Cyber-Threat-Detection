import json
import logging
from typing import List
from app.models.security_event import SecurityEvent
from app.schemas.alert import AlertCreate
from app.detection.rules.base import BaseDetectionRule

logger = logging.getLogger(__name__)

class NewDeviceRule(BaseDetectionRule):
    @property
    def rule_name(self) -> str:
        return "New Device Login"

    @property
    def alert_type(self) -> str:
        return "new_device_login"

    @property
    def severity(self) -> str:
        return "low"

    def analyze(self, events: List[SecurityEvent]) -> List[AlertCreate]:
        alerts = []
        for event in events:
            if event.event_type == "login" and event.raw_payload:
                try:
                    payload = json.loads(event.raw_payload) if isinstance(event.raw_payload, str) else event.raw_payload
                    
                    is_new = payload.get("is_new_device")
                    if is_new is True or str(is_new).lower() == "true":
                        logger.info(f"NewDeviceRule: Triggering alert for event ID {event.id} (is_new_device={is_new})")
                        alerts.append(
                            AlertCreate(
                                event_id=event.id,
                                alert_type=self.alert_type,
                                severity=self.severity,
                                status="open"
                            )
                        )
                except (json.JSONDecodeError, AttributeError, TypeError) as e:
                    logger.debug(f"NewDeviceRule: Could not parse payload for event {event.id}: {e}")
                    pass
        return alerts
