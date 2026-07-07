import json
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.session import SessionLocal
from app.simulators.scenarios import get_new_device
from app.detection.engine import DetectionEngine
from app.models.security_event import SecurityEvent

# 1. Start by clearing previous new_device alerts to be sure
db = SessionLocal()
from app.models.alert import Alert
db.query(Alert).filter(Alert.alert_type == "new_device_login").delete()
db.query(SecurityEvent).filter(SecurityEvent.user_id == "usr_david").delete()
db.commit()

# 2. Get scenario
events = get_new_device(datetime.now(timezone.utc), "debug_scenario_2", {"customer_id": "usr_david", "name": "David", "risk_level": "medium"})

# 3. Post to API
for e in events:
    # Simulator posts to /api/v1/events
    print("Posting payload:", json.dumps(e, indent=2))
    # We will just insert it using service so we don't need the server running
    from app.services.security_event import create_security_event
    from app.schemas.security_event import SecurityEventCreate
    create_security_event(db, SecurityEventCreate(**e))

# 4. Run DetectionEngine
engine = DetectionEngine(db)
result = engine.run()

print("Detection run result:", result.model_dump())

# 5. Check if alert was generated
alerts = db.query(Alert).filter(Alert.alert_type == "new_device_login").all()
print("Alerts found:", [a.id for a in alerts])
for a in alerts:
    print(f"- Alert ID {a.id}: {a.alert_type}, severity={a.severity}, event_id={a.event_id}")

db.close()
