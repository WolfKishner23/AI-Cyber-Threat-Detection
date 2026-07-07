from typing import List
from app.models.security_event import SecurityEvent
from app.schemas.alert import AlertCreate
from app.detection.rules.base import BaseDetectionRule

HIGH_RISK_DEMO_LOCATIONS = {
    "North Sentinel Island",
    "Pyongyang, North Korea",
    "Juba, South Sudan"
}

class HighRiskLocationRule(BaseDetectionRule):
    @property
    def rule_name(self) -> str:
        return "High Risk Location"

    @property
    def alert_type(self) -> str:
        return "malicious_ip"

    @property
    def severity(self) -> str:
        return "critical"

    def analyze(self, events: List[SecurityEvent]) -> List[AlertCreate]:
        alerts = []
        for event in events:
            if event.location in HIGH_RISK_DEMO_LOCATIONS:
                alerts.append(
                    AlertCreate(
                        event_id=event.id,
                        alert_type=self.alert_type,
                        severity=self.severity,
                        status="open"
                    )
                )
        return alerts
