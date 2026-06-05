import requests
import json
import subprocess
import time

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_header(title):
    print(f"\n{'='*60}\n{title}\n{'='*60}")

def verify():
    print_header("1. Simulator -> Generating Brute Force Scenario")
    subprocess.run(["venv\\Scripts\\python", "-m", "app.simulators.event_generator", "--scenario", "brute_force", "--count", "1"], capture_output=True)
    
    print_header("2. Detection Engine -> Generating Alerts")
    r = requests.post(f"{BASE_URL}/detection/run")
    print(f"Status: {r.status_code}")
    print(json.dumps(r.json(), indent=2))
    
    print_header("3. Fetching Alerts")
    r = requests.get(f"{BASE_URL}/alerts/?limit=10")
    alerts = r.json()
    if not alerts:
        print("No alerts found!")
        return
        
    brute_force_alert = next((a for a in alerts if a['alert_type'] == 'brute_force'), alerts[0])
    print(f"Target Alert ID: {brute_force_alert['id']} (Type: {brute_force_alert['alert_type']})")
    
    print_header("4. LangGraph Investigation -> Checking Tool Outputs")
    r = requests.post(f"{BASE_URL}/investigations/run/{brute_force_alert['id']}")
    investigation = r.json()
    
    print("----- Raw Tool Outputs -----")
    print(json.dumps(investigation.get("tool_outputs", {}), indent=2))
    
    print("\n----- Final Investigation Response -----")
    print(json.dumps({
        "risk_score": investigation.get("risk_score"),
        "recommended_action": investigation.get("recommended_action"),
        "reasoning_trace": investigation.get("reasoning_trace")
    }, indent=2))

if __name__ == "__main__":
    verify()
