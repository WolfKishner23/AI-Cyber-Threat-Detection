from typing import List, Dict
from datetime import timedelta
from app.models.security_event import SecurityEvent
from app.schemas.alert import AlertCreate
from app.detection.rules.base import BaseDetectionRule

class BruteForceRule(BaseDetectionRule):
    @property
    def rule_name(self) -> str:
        return "Brute Force"

    @property
    def alert_type(self) -> str:
        return "brute_force"

    @property
    def severity(self) -> str:
        return "medium"

    def analyze(self, events: List[SecurityEvent]) -> List[AlertCreate]:
        alerts = []
        
        target_events = [e for e in events if e.event_type in ("login", "failed_login")]
        user_events: Dict[str, List[SecurityEvent]] = {}
        for event in target_events:
            if event.user_id not in user_events:
                user_events[event.user_id] = []
            user_events[event.user_id].append(event)
            
        for user_id, u_events in user_events.items():
            sorted_events = sorted(u_events, key=lambda x: x.timestamp)
            
            failed_streak = []
            for event in sorted_events:
                if event.event_type == "failed_login":
                    failed_streak.append(event)
                    # Keep only failures within the last 5 minutes
                    failed_streak = [
                        f for f in failed_streak 
                        if event.timestamp - f.timestamp <= timedelta(minutes=5)
                    ]
                    
                    # Generate alert on exactly the 5th failure to avoid duplicate alerts per streak
                    if len(failed_streak) == 5:
                        alerts.append(
                            AlertCreate(
                                event_id=event.id,
                                alert_type=self.alert_type,
                                severity=self.severity,
                                status="open"
                            )
                        )
                elif event.event_type == "login":
                    # Success immediately following 5+ failures
                    if len(failed_streak) >= 5:
                        alerts.append(
                            AlertCreate(
                                event_id=event.id,
                                alert_type="successful_brute_force",
                                severity="high",  # Escalate severity for successful breach
                                status="open"
                            )
                        )
                    # Reset streak on success
                    failed_streak = []
                    
        return alerts
