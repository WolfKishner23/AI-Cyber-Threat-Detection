import requests
import time
import json
import sqlite3

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_header(title):
    print(f"\n{'='*50}\n{title}\n{'='*50}")

def run_tests():
    import subprocess
    print_header("Automated Testing")
    result = subprocess.run(["venv\\Scripts\\python", "-m", "pytest", "tests/", "-v"], capture_output=True, text=True)
    print(result.stdout)
    if result.stderr:
        print("STDERR:", result.stderr)

def test_api():
    print_header("API Verification")
    
    # POST /api/v1/events
    print("-> POST /api/v1/events/")
    event_payload = {
        "user_id": "audit_user",
        "event_type": "audit_test",
        "ip_address": "10.0.0.1",
        "location": "Audit City",
        "device_name": "Audit_PC"
    }
    r = requests.post(f"{BASE_URL}/events/", json=event_payload)
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2)}")
    
    # GET /api/v1/events
    print("\n-> GET /api/v1/events/")
    r = requests.get(f"{BASE_URL}/events/?limit=2")
    print(f"Status: {r.status_code}")
    print(f"Response (2 items): {json.dumps(r.json(), indent=2)}")

def generate_scenarios():
    print_header("End-to-End: Generating Scenarios")
    import subprocess
    scenarios = ["impossible_travel", "brute_force", "credential_compromise", "new_device", "password_reset_workflow"]
    for s in scenarios:
        print(f"Running scenario: {s}")
        subprocess.run(["venv\\Scripts\\python", "-m", "app.simulators.event_generator", "--scenario", s, "--count", "1"], capture_output=True)
    print("Scenarios generated.")

def trigger_detection():
    print_header("Detection Engine")
    print("-> POST /api/v1/detection/run")
    r = requests.post(f"{BASE_URL}/detection/run")
    print(f"Status: {r.status_code}")
    print(f"Response: {json.dumps(r.json(), indent=2)}")

def verify_alerts_and_investigate():
    print_header("Alerts & LangGraph Verification")
    r = requests.get(f"{BASE_URL}/alerts/?limit=100")
    alerts = r.json()
    print(f"Total alerts fetched: {len(alerts)}")
    
    alert_types = set([a['alert_type'] for a in alerts])
    print(f"Alert types found: {alert_types}")
    
    # Run investigation on one alert of each type
    for alert_type in alert_types:
        alert = next(a for a in alerts if a['alert_type'] == alert_type)
        print(f"\n-> POST /api/v1/investigations/run/{alert['id']} ({alert_type})")
        r_inv = requests.post(f"{BASE_URL}/investigations/run/{alert['id']}")
        print(f"Status: {r_inv.status_code}")
        inv_data = r_inv.json()
        print(f"Risk Score: {inv_data.get('risk_score')}")
        print(f"Recommended Action: {inv_data.get('recommended_action')}")
        print("Reasoning Trace:")
        for t in inv_data.get('reasoning_trace', []):
            print(f"  > {t}")

def check_db_counts():
    print_header("Database Verification")
    conn = sqlite3.connect("cyber_threat_platform.db")
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM securityevent")
    events = cursor.fetchone()[0]
    print(f"SecurityEvent records: {events}")
    
    cursor.execute("SELECT COUNT(*) FROM alert")
    alerts = cursor.fetchone()[0]
    print(f"Alert records: {alerts}")
    
    cursor.execute("SELECT COUNT(*) FROM detectionrun")
    runs = cursor.fetchone()[0]
    print(f"Detection runs: {runs}")
    
    conn.close()

if __name__ == "__main__":
    run_tests()
    test_api()
    generate_scenarios()
    trigger_detection()
    verify_alerts_and_investigate()
    check_db_counts()
