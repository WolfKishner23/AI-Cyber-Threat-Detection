import sys
import os
import subprocess
import requests
import json
from datetime import datetime

# Setup path so we can import tools and models
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.database.session import SessionLocal
from app.models.security_event import SecurityEvent
from app.models.alert import Alert
from app.models.detection_run import DetectionRun
from app.simulators.scenarios import SCENARIOS_MAP, generate_scenario_id
from app.tools import (
    get_user_history,
    get_device_history,
    get_location_history,
    get_previous_alerts,
    get_incident_history,
    get_ip_reputation
)

BASE_URL = "http://127.0.0.1:8000/api/v1"

def print_section(title):
    print("\n" + "="*80)
    print(f" {title}")
    print("="*80)

def main():
    print_section("STARTING SYSTEM AUDIT VERIFICATION")
    
    # -------------------------------------------------------------
    # pytest execution
    # -------------------------------------------------------------
    print_section("RUNNING AUTOMATED TESTS (pytest)")
    result = subprocess.run(
        ["venv\\Scripts\\python", "-m", "pytest", "tests/", "-v"],
        capture_output=True,
        text=True
    )
    
    print("Pytest stdout snippet:")
    lines = result.stdout.splitlines()
    for line in lines[-5:]:
        print(line)
        
    passed = 0
    failed = 0
    skipped = 0
    for line in lines:
        if " PASSED " in line:
            passed += 1
        elif " FAILED " in line:
            failed += 1
        elif " SKIPPED " in line:
            skipped += 1
            
    print(f"\nTest Summary Extracted:")
    print(f"- Total Tests Executed: {passed + failed + skipped}")
    print(f"- Passed: {passed}")
    print(f"- Failed: {failed}")
    print(f"- Skipped: {skipped}")

    # -------------------------------------------------------------
    # Phase 1: API Endpoint & Schema Verification
    # -------------------------------------------------------------
    print_section("PHASE 1: API ENDPOINTS & SCHEMA VALIDATION")
    
    # Test valid event creation
    valid_event_payload = {
        "user_id": "usr_audit_test",
        "event_type": "login",
        "location": "Paris, France",
        "ip_address": "195.154.122.33",
        "device_name": "Audit-MacBook",
        "timestamp": datetime.utcnow().isoformat(),
        "raw_payload": {"status": "success", "audit": True}
    }
    
    resp_create = requests.post(f"{BASE_URL}/events/", json=valid_event_payload)
    print(f"POST /api/v1/events/ (Valid Payload): HTTP {resp_create.status_code}")
    if resp_create.status_code == 201:
        created_event = resp_create.json()
        print(f"Created Event ID: {created_event.get('id')}")
        
        # Test GET specific event
        resp_get = requests.get(f"{BASE_URL}/events/{created_event.get('id')}")
        print(f"GET /api/v1/events/{{id}}: HTTP {resp_get.status_code}")
        print(f"Retrieved user_id: {resp_get.json().get('user_id')}")
    else:
        print(f"Failed to create event: {resp_create.text}")
        
    # Test schema validation error (invalid IP address format)
    invalid_event_payload = valid_event_payload.copy()
    invalid_event_payload["ip_address"] = "invalid-ip-format"
    resp_invalid = requests.post(f"{BASE_URL}/events/", json=invalid_event_payload)
    print(f"POST /api/v1/events/ (Invalid IP Payload): HTTP {resp_invalid.status_code} (Expected 422)")
    if resp_invalid.status_code == 422:
        print("Schema validation correctly rejected invalid IP address format.")
    else:
        print(f"Warning: Expected 422 but got {resp_invalid.status_code}. Response: {resp_invalid.text}")

    # -------------------------------------------------------------
    # Phase 2: Simulator Scenarios Verification
    # -------------------------------------------------------------
    print_section("PHASE 2: SIMULATOR SCENARIOS GENERATION & POST")
    
    scenario_counts = {}
    base_time = datetime.utcnow()
    
    for scenario_name, generator_func in SCENARIOS_MAP.items():
        scenario_id = generate_scenario_id()
        events = generator_func(base_time, scenario_id)
        print(f"Generating scenario '{scenario_name}' ({len(events)} events)...")
        
        success_count = 0
        for event in events:
            # Overwrite timestamp so they fit current timeframe
            resp = requests.post(f"{BASE_URL}/events/", json=event)
            if resp.status_code == 201:
                success_count += 1
                
        scenario_counts[scenario_name] = success_count
        print(f"-> Successfully posted {success_count}/{len(events)} events to API.")

    # -------------------------------------------------------------
    # Phase 3: Detection Engine Verification
    # -------------------------------------------------------------
    print_section("PHASE 3: DETECTION ENGINE EXECUTION")
    
    resp_detection = requests.post(f"{BASE_URL}/detection/run")
    print(f"POST /api/v1/detection/run: HTTP {resp_detection.status_code}")
    detection_result = resp_detection.json()
    print("Detection Run Response:")
    print(json.dumps(detection_result, indent=2))
    
    # Retrieve alerts
    resp_alerts = requests.get(f"{BASE_URL}/alerts/?limit=20")
    print(f"GET /api/v1/alerts: HTTP {resp_alerts.status_code}")
    all_alerts = resp_alerts.json()
    print(f"Retrieved {len(all_alerts)} alerts. Showing types & severities:")
    for a in all_alerts[:10]:
        print(f"- ID: {a['id']}, Type: {a['alert_type']}, Severity: {a['severity']}, Status: {a['status']}, Event ID: {a['event_id']}")
        
    # Check duplicate prevention
    print("\nRunning Detection Engine again to test duplicate prevention...")
    resp_detection_dup = requests.post(f"{BASE_URL}/detection/run")
    print(f"POST /api/v1/detection/run (Second run): HTTP {resp_detection_dup.status_code}")
    print(f"Alerts generated on second run: {resp_detection_dup.json().get('alerts_generated')} (Expected: 0)")

    # -------------------------------------------------------------
    # Phase 4 & 5: LangGraph Investigation & Tool Integration Verification
    # -------------------------------------------------------------
    print_section("PHASE 4 & 5: LANGGRAPH INVESTIGATION & TOOL LAYER INTEGRATION")
    
    # Run investigation for a target alert
    if all_alerts:
        # Pick a brute force or impossible travel alert
        target_alert = None
        for a in all_alerts:
            if a["alert_type"] in ["brute_force", "impossible_travel"]:
                target_alert = a
                break
        if not target_alert:
            target_alert = all_alerts[0]
            
        print(f"Target Alert Selected for Investigation: ID {target_alert['id']} ({target_alert['alert_type']})")
        
        # Test specific GET alert endpoint
        resp_get_alert = requests.get(f"{BASE_URL}/alerts/{target_alert['id']}")
        print(f"GET /api/v1/alerts/{{id}}: HTTP {resp_get_alert.status_code}")
        
        # POST to run investigation
        resp_investigate = requests.post(f"{BASE_URL}/investigations/run/{target_alert['id']}")
        print(f"POST /api/v1/investigations/run/{{alert_id}}: HTTP {resp_investigate.status_code}")
        
        if resp_investigate.status_code == 200:
            investigation_result = resp_investigate.json()
            print("\nFinal Investigation Response Schema Verification:")
            print(f"- Alert ID: {investigation_result.get('alert_id')}")
            print(f"- Risk Score: {investigation_result.get('risk_score')}")
            print(f"- Confidence Score: {investigation_result.get('confidence_score')}")
            print(f"- Recommended Action: {investigation_result.get('recommended_action')}")
            print(f"- Summary: {investigation_result.get('investigation_summary')}")
            
            print("\nReasoning Trace:")
            for trace_line in investigation_result.get("reasoning_trace", []):
                print(f"  > {trace_line}")
                
            print("\nTool Outputs (Phase 5):")
            print(json.dumps(investigation_result.get("tool_outputs", {}), indent=2))
        else:
            print(f"Investigation execution failed: {resp_investigate.text}")
    else:
        print("No alerts found, skipping investigation.")

    # -------------------------------------------------------------
    # Tool Functions Direct Invocation Verification
    # -------------------------------------------------------------
    print_section("DIRECT TOOL FUNCTIONS INVOCATION")
    db = SessionLocal()
    try:
        print("Executing get_user_history for 'usr_charlie':")
        print(json.dumps(get_user_history(db, "usr_charlie"), indent=2)[:500] + "...\n")
        
        print("Executing get_device_history for 'usr_charlie':")
        print(json.dumps(get_device_history(db, "usr_charlie"), indent=2))
        
        print("Executing get_location_history for 'usr_charlie':")
        print(json.dumps(get_location_history(db, "usr_charlie"), indent=2))
        
        print("Executing get_previous_alerts for 'usr_charlie':")
        print(json.dumps(get_previous_alerts(db, "usr_charlie"), indent=2)[:500] + "...\n")
        
        print("Executing get_incident_history for 'usr_charlie':")
        print(json.dumps(get_incident_history(db, "usr_charlie"), indent=2))
        
        print("Executing get_ip_reputation for '192.0.2.78':")
        print(json.dumps(get_ip_reputation("192.0.2.78"), indent=2))
    finally:
        db.close()

    # -------------------------------------------------------------
    # Database Record Counts
    # -------------------------------------------------------------
    print_section("DATABASE RECORD COUNTS")
    db = SessionLocal()
    try:
        events_count = db.query(SecurityEvent).count()
        alerts_count = db.query(Alert).count()
        runs_count = db.query(DetectionRun).count()
        print(f"- Total SecurityEvent records: {events_count}")
        print(f"- Total Alert records: {alerts_count}")
        print(f"- Total DetectionRun records: {runs_count}")
    finally:
        db.close()

if __name__ == "__main__":
    main()
