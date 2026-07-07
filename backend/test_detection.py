import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.detection.rules.impossible_travel import ImpossibleTravelRule

engine = create_engine("sqlite:///./cyber_threat_platform.db")
Session = sessionmaker(bind=engine)
db = Session()

events = db.query(SecurityEvent).all()
print(f"Total events: {len(events)}")

rule = ImpossibleTravelRule()
alerts = rule.analyze(events)
print(f"Alerts generated: {len(alerts)}")
for a in alerts:
    print(a)
