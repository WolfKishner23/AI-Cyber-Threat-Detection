import requests
import json
from datetime import datetime, timezone
from app.simulators.scenarios import get_impossible_travel

API_URL = "http://localhost:8001/api/v1/events/"

def simulate():
    print("Generating Impossible Travel scenario...")
    events = get_impossible_travel(
        datetime.now(timezone.utc), 
        "test_impossible_travel_01", 
        {"customer_id": "usr_bob", "name": "Bob", "risk_level": "low"}
    )
    
    for e in events:
        print(f"Posting event: {e['event_type']} from {e['location']}")
        response = requests.post(API_URL, json=e)
        if response.status_code == 201:
            print("Successfully posted event.")
        else:
            print(f"Error: {response.status_code} - {response.text}")

if __name__ == "__main__":
    simulate()
