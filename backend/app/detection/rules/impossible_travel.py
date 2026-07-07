from typing import List, Dict
from datetime import timedelta
from app.models.security_event import SecurityEvent
from app.schemas.alert import AlertCreate
from app.detection.rules.base import BaseDetectionRule

class ImpossibleTravelRule(BaseDetectionRule):
    @property
    def rule_name(self) -> str:
        return "Impossible Travel"

    @property
    def alert_type(self) -> str:
        return "impossible_travel"

    @property
    def severity(self) -> str:
        return "high"

    def analyze(self, events: List[SecurityEvent]) -> List[AlertCreate]:
        alerts = []
        # Filter for login and bank_account_access events
        logins = [e for e in events if e.event_type in ("login", "bank_account_access")]
        
        # Group by user_id
        user_logins: Dict[str, List[SecurityEvent]] = {}
        for login in logins:
            if login.user_id not in user_logins:
                user_logins[login.user_id] = []
            user_logins[login.user_id].append(login)
            
        for user_id, user_events in user_logins.items():
            # Sort chronologically
            sorted_events = sorted(user_events, key=lambda x: x.timestamp)
            
            for i in range(1, len(sorted_events)):
                prev_event = sorted_events[i-1]
                curr_event = sorted_events[i]
                
                print(f"Comparing {prev_event.id} ({prev_event.location}) to {curr_event.id} ({curr_event.location})")
                
                # Check if locations differ
                if prev_event.location and curr_event.location and prev_event.location != curr_event.location:
                    # Check time difference < 6 hours
                    # Assuming timestamps are timezone-aware and comparable
                    time_diff = curr_event.timestamp - prev_event.timestamp
                    print(f"Time diff: {time_diff}")
                    if timedelta(0) <= time_diff < timedelta(hours=6):
                        print(f"Generating alert for {curr_event.id}")
                        alerts.append(
                            AlertCreate(
                                event_id=curr_event.id,
                                alert_type=self.alert_type,
                                severity=self.severity,
                                status="open"
                            )
                        )
        return alerts
