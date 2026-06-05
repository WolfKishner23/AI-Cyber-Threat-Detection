from app.database.session import SessionLocal
from app.models.security_event import SecurityEvent

db = SessionLocal()
events = db.query(SecurityEvent).all()
if events:
    print(f"Found {len(events)} events.")
    for e in events[:2]:
        print("Type:", type(e.raw_payload))
        print("Content:", e.raw_payload)
else:
    print("No events found in DB.")
db.close()
