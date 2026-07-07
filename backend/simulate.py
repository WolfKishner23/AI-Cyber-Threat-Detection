import argparse
import requests
import json
from datetime import datetime, timezone
from app.simulators.scenarios import (
    get_normal_activity,
    get_impossible_travel,
    get_brute_force,
    get_new_device,
    get_credential_compromise,
    get_password_reset_workflow
)

API_URL = "http://localhost:8001/api/v1/events/"

SCENARIOS = {
    "normal": get_normal_activity,
    "impossible_travel": get_impossible_travel,
    "brute_force": get_brute_force,
    "new_device": get_new_device,
    "credential_compromise": get_credential_compromise,
    "password_reset": get_password_reset_workflow
}

# Add malicious IP logic wrapper
def get_malicious_ip(*args, **kwargs):
    events = get_new_device(*args, **kwargs)
    events[0]['ip_address'] = "198.51.100.12"  # Flagged as malicious in IP Rep
    events[0]['device_name'] = "Tor-Browser"
    return events

SCENARIOS["malicious_ip"] = get_malicious_ip

def simulate(scenario_name: str):
    if scenario_name not in SCENARIOS:
        print(f"Error: Unknown scenario '{scenario_name}'")
        print(f"Available scenarios: {', '.join(SCENARIOS.keys())}")
        return

    print(f"Generating {scenario_name} scenario...")
    generator_func = SCENARIOS[scenario_name]
    
    # Map scenarios to different professional customer profiles
    customer_profiles = {
        "normal": {"customer_id": "CUST-1002-AL", "full_name": "Alice Liddell", "account_number": "8102938475", "risk_level": "low"},
        "impossible_travel": {"customer_id": "CUST-5591-RO", "full_name": "Robert Oppenheimer", "account_number": "9485001923", "risk_level": "medium"},
        "brute_force": {"customer_id": "CUST-3821-ED", "full_name": "Edward Snowden", "account_number": "4820194852", "risk_level": "high"},
        "new_device": {"customer_id": "CUST-9921-DT", "full_name": "David Turing", "account_number": "1002948572", "risk_level": "low"},
        "credential_compromise": {"customer_id": "CUST-4829-MT", "full_name": "Margaret Thatcher", "account_number": "8810294857", "risk_level": "critical"},
        "password_reset": {"customer_id": "CUST-1029-FW", "full_name": "Frank Wright", "account_number": "5501928475", "risk_level": "low"},
        "malicious_ip": {"customer_id": "CUST-8812-JB", "full_name": "James Bond", "account_number": "0070070070", "risk_level": "critical"},
    }
    
    events = generator_func(
        datetime.now(timezone.utc), 
        f"test_{scenario_name}_01", 
        customer_profiles[scenario_name]
    )
    
    for e in events:
        print(f"Posting event: {e['event_type']} from {e['location']} (IP: {e['ip_address']})")
        response = requests.post(API_URL, json=e)
        if response.status_code == 201:
            print("  Successfully posted event.")
        else:
            print(f"  Error: {response.status_code} - {response.text}")
    print("Done!")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate various security events")
    parser.add_argument("scenario", type=str, choices=SCENARIOS.keys(), 
                        help="The type of scenario to simulate")
    
    args = parser.parse_args()
    simulate(args.scenario)
