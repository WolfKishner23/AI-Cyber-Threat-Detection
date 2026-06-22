import argparse
import sys
import time
import logging
from datetime import datetime
import httpx

from app.simulators.scenarios import (
    SCENARIOS_MAP,
    generate_scenario_id,
    SCENARIO_NORMAL,
    SCENARIO_IMPOSSIBLE_TRAVEL,
    SCENARIO_BRUTE_FORCE,
    SCENARIO_NEW_DEVICE,
    SCENARIO_CREDENTIAL_COMPROMISE,
    SCENARIO_PASSWORD_RESET
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("Simulator")

def run_scenario(scenario_name: str, target_url: str, interval: float) -> bool:
    """
    Generate and post the sequence of events belonging to a scenario.
    """
    generator_func = SCENARIOS_MAP.get(scenario_name)
    if not generator_func:
        logger.error(f"Unknown scenario name: '{scenario_name}'")
        return False
        
    scenario_id = generate_scenario_id()
    # Use current time as the baseline for simulated timestamps
    base_time = datetime.utcnow()
    events = generator_func(base_time, scenario_id)
    
    logger.info(f"\n========================================================")
    logger.info(f"Starting Scenario: {scenario_name.upper()}")
    logger.info(f"Scenario ID: {scenario_id}")
    logger.info(f"========================================================")
    
    with httpx.Client(timeout=10.0) as client:
        for event in events:
            step_info = event["raw_payload"]["simulation"]
            step = step_info["step"]
            total_steps = step_info["total_steps"]
            
            # Print exact log format required by Phase 2 requirements
            print(f"\n[{scenario_name.upper()}]")
            print(f"Step {step}/{total_steps}")
            print(f"Event: {event['event_type']}")
            print(f"User: {event['user_id']}")
            print(f"Location: {event.get('location') or 'None'}")
            print(f"IP: {event['ip_address']}")
            print(f"Timestamp: {event['timestamp']}")
            
            try:
                response = client.post(target_url, json=event)
                if response.status_code == 201:
                    print("Event stored successfully.")
                    # Automatically trigger the detection engine for a realistic E2E flow
                    detection_url = target_url.replace("/events/", "/detection/run")
                    det_resp = client.post(detection_url)
                    if det_resp.status_code == 200:
                        alerts = det_resp.json().get('alerts_generated', 0)
                        if alerts > 0:
                            print(f"[{alerts} ALERT(S) GENERATED]")
                else:
                    logger.error(f"Failed to store event: HTTP {response.status_code} - {response.text}")
            except httpx.RequestError as exc:
                logger.error(f"HTTP Connection Error while posting to {target_url}: {exc}")
                print("Failed to store event due to connection issue.")
                
            time.sleep(interval)
            
    logger.info(f"========================================================")
    logger.info(f"Finished Scenario: {scenario_name.upper()}")
    logger.info(f"========================================================\n")
    return True

def main():
    parser = argparse.ArgumentParser(
        description="Scenario-Based Security Event Simulator CLI for the Cyber Threat Platform."
    )
    parser.add_argument(
        "--url",
        type=str,
        default="http://127.0.0.1:8000/api/v1/events/",
        help="FastAPI event creation endpoint URL."
    )
    parser.add_argument(
        "--interval",
        type=float,
        default=2.0,
        help="Delay in seconds between posting sequential events in a scenario."
    )
    parser.add_argument(
        "--scenario",
        type=str,
        default="all",
        choices=["all"] + list(SCENARIOS_MAP.keys()),
        help="Name of the specific scenario to run, or 'all' to cycle through all of them."
    )
    parser.add_argument(
        "--count",
        type=int,
        default=0,
        help="Number of scenarios to run before exiting (0 for infinite loop)."
    )
    
    args = parser.parse_args()
    
    logger.info("Initializing Security Event Simulator...")
    logger.info(f"Target URL: {args.url}")
    logger.info(f"Posting interval: {args.interval}s")
    logger.info(f"Selected scenario: {args.scenario}")
    logger.info(f"Execution count: {args.count if args.count > 0 else 'Infinite'}")
    
    scenarios_to_run = list(SCENARIOS_MAP.keys())
    if args.scenario != "all":
        scenarios_to_run = [args.scenario]
        
    run_count = 0
    try:
        while True:
            for scenario_name in scenarios_to_run:
                success = run_scenario(
                    scenario_name=scenario_name,
                    target_url=args.url,
                    interval=args.interval
                )
                if success:
                    run_count += 1
                    
                if args.count > 0 and run_count >= args.count:
                    logger.info(f"Execution count limit reached ({args.count}). Exiting.")
                    return
                    
                # Pause slightly between distinct scenarios
                time.sleep(max(1.0, args.interval))
                
            if args.scenario != "all" and args.count == 0:
                # If running a single scenario infinitely, we just loop on it.
                continue
                
    except KeyboardInterrupt:
        logger.info("\nSimulator execution interrupted by user. Exiting.")
        sys.exit(0)

if __name__ == "__main__":
    main()
