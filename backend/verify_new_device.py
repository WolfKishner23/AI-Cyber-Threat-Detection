import json
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from app.main import app
from app.simulators.scenarios import get_new_device
from datetime import datetime, timezone

client = TestClient(app)

def test_full_pipeline():
    print("Generating simulated new_device events...")
    events = get_new_device(datetime.now(timezone.utc), "full_pipeline_test")
    
    print("Submitting events to API...")
    event_ids = []
    for e in events:
        response = client.post("/api/v1/events/", json=e)
        response.raise_for_status()
        data = response.json()
        event_ids.append(data["id"])
        print(f"Created Event ID {data['id']}")
        
    print("Running detection engine via API...")
    resp = client.post("/api/v1/detection/run")
    resp.raise_for_status()
    run_stats = resp.json()
    print("Detection Run Stats:", json.dumps(run_stats, indent=2))
    
    print("Retrieving alerts...")
    # There is no list alerts endpoint, we will check db directly or get the alert by ID
    # But wait, there is no /alerts list endpoint, we have to look up the DB
    from app.database.session import SessionLocal
    from app.models.alert import Alert
    
    db = SessionLocal()
    alerts = db.query(Alert).filter(Alert.alert_type == "new_device_login", Alert.event_id.in_(event_ids)).all()
    
    if alerts:
        print("SUCCESS! Found new_device alerts:")
        for a in alerts:
            resp = client.get(f"/api/v1/alerts/{a.id}")
            print(json.dumps(resp.json(), indent=2))
    else:
        print("FAILURE: No new_device alerts found!")
        
    db.close()

if __name__ == "__main__":
    test_full_pipeline()
