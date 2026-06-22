import requests
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

print("--- Starting E2E Workflow ---")

# 1. Login Event
print("1. Creating Login Event...")
event_payload = {
    "user_id": "usr_e2e_test",
    "event_type": "login",
    "location": "Tokyo, Japan",
    "ip_address": "203.0.113.1",
    "device_name": "E2E-Device",
    "raw_payload": {"is_new_device": True}
}
resp = requests.post(f"{BASE_URL}/events/", json=event_payload)
resp.raise_for_status()
event_id = resp.json()["id"]
print(f"   Created Event ID: {event_id}")

# 2. Run Detection Engine
print("2. Running Detection Engine...")
resp = requests.post(f"{BASE_URL}/detection/run")
resp.raise_for_status()
print(f"   Detection run. Alerts generated: {resp.json().get('alerts_generated')}")

resp = requests.get(f"{BASE_URL}/alerts/")
alerts = resp.json()
our_alerts = [a for a in alerts if a["event_id"] == event_id]

if len(our_alerts) == 0:
    print("   FAILED to generate alert via detection engine!")
    exit(1)

alert_id = our_alerts[0]["id"]
print(f"3. Alert created via detection engine. ID: {alert_id}")

print(f"3. Alert created. ID: {alert_id}")

print("4. Running Investigation...")
resp = requests.post(f"{BASE_URL}/investigations/run/{alert_id}")
resp.raise_for_status()
inv_data = resp.json()
print(f"   Investigation Completed. Risk Score: {inv_data.get('risk_score')}")

print("5. Verifying Persistence...")
resp = requests.get(f"{BASE_URL}/investigations/")
resp.raise_for_status()
inv_list = resp.json()
found = any(inv["alert_id"] == alert_id for inv in inv_list)
if found:
    print("   Investigation was successfully persisted in the database.")
else:
    print("   WARNING: Investigation not found in database.")

print("--- E2E Workflow Completed Successfully ---")
