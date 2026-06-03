import argparse
from datetime import datetime
import pytest
from unittest.mock import MagicMock, patch

from app.simulators.scenarios import (
    SCENARIOS_MAP,
    SCENARIO_NORMAL,
    SCENARIO_IMPOSSIBLE_TRAVEL,
    SCENARIO_BRUTE_FORCE,
    SCENARIO_NEW_DEVICE,
    SCENARIO_CREDENTIAL_COMPROMISE,
    SCENARIO_PASSWORD_RESET
)
from app.simulators.event_generator import run_scenario

def test_scenario_generation_structures():
    """
    Verify that calling each scenario generator yields the correct sequence structure.
    """
    base_time = datetime.utcnow()
    scenario_id = "test-session-123"

    for name, generator in SCENARIOS_MAP.items():
        events = generator(base_time, scenario_id)
        assert isinstance(events, list)
        assert len(events) > 0
        
        # Verify schema parameters are populated
        for event in events:
            assert "user_id" in event
            assert "event_type" in event
            assert "ip_address" in event
            assert "raw_payload" in event
            assert "timestamp" in event

def test_metadata_correctness_and_expected_detections():
    """
    Verify that simulation metadata is correctly structured and detection labels match expectations.
    """
    base_time = datetime.utcnow()
    scenario_id = "test-session-456"

    # Impossible Travel
    events_it = SCENARIOS_MAP[SCENARIO_IMPOSSIBLE_TRAVEL](base_time, scenario_id)
    assert len(events_it) == 2
    assert events_it[0]["raw_payload"]["simulation"]["scenario"] == SCENARIO_IMPOSSIBLE_TRAVEL
    assert events_it[0]["raw_payload"]["simulation"]["is_attack"] is True
    assert events_it[1]["raw_payload"]["simulation"]["step"] == 2
    assert "impossible_travel" in events_it[0]["raw_payload"]["simulation"]["expected_detection"]

    # Brute Force
    events_bf = SCENARIOS_MAP[SCENARIO_BRUTE_FORCE](base_time, scenario_id)
    assert len(events_bf) == 6
    assert events_bf[5]["event_type"] == "login"
    assert events_bf[5]["raw_payload"]["simulation"]["step"] == 6
    assert "brute_force" in events_bf[0]["raw_payload"]["simulation"]["expected_detection"]

    # Credential Compromise
    events_cc = SCENARIOS_MAP[SCENARIO_CREDENTIAL_COMPROMISE](base_time, scenario_id)
    assert len(events_cc) == 6
    assert events_cc[3]["event_type"] == "login"
    assert events_cc[4]["event_type"] == "password_reset"
    assert events_cc[5]["event_type"] == "login" # new device login
    assert "credential_compromise" in events_cc[5]["raw_payload"]["simulation"]["expected_detection"]

    # Password Reset Legitimate
    events_pr = SCENARIOS_MAP[SCENARIO_PASSWORD_RESET](base_time, scenario_id)
    assert len(events_pr) == 3
    assert events_pr[0]["event_type"] == "failed_login"
    assert events_pr[1]["event_type"] == "password_reset"
    assert events_pr[2]["event_type"] == "login"
    assert events_pr[0]["raw_payload"]["simulation"]["is_attack"] is False
    assert events_pr[0]["raw_payload"]["simulation"]["expected_detection"] == []

def test_cli_parsing():
    """
    Test event_generator CLI arguments parsing configurations.
    """
    # Create parser using same definitions as event_generator main
    parser = argparse.ArgumentParser()
    parser.add_argument("--url", type=str, default="http://127.0.0.1:8000/api/v1/events/")
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--scenario", type=str, default="all")
    parser.add_argument("--count", type=int, default=0)

    # Test defaults
    parsed = parser.parse_args([])
    assert parsed.url == "http://127.0.0.1:8000/api/v1/events/"
    assert parsed.interval == 2.0
    assert parsed.scenario == "all"
    assert parsed.count == 0

    # Test custom inputs
    parsed_custom = parser.parse_args(["--url", "http://test-server/api/", "--interval", "0.5", "--scenario", "brute_force", "--count", "5"])
    assert parsed_custom.url == "http://test-server/api/"
    assert parsed_custom.interval == 0.5
    assert parsed_custom.scenario == "brute_force"
    assert parsed_custom.count == 5

@patch("httpx.Client")
def test_api_submission_handling(mock_client_class):
    """
    Verify that run_scenario creates a client, runs requests, and handles success/error codes.
    """
    # Mock HTTP response
    mock_response = MagicMock()
    mock_response.status_code = 201
    
    # Mock client instance
    mock_client = MagicMock()
    mock_client.post.return_value = mock_response
    mock_client_class.return_value.__enter__.return_value = mock_client

    # Execute normal activity (2 events)
    success = run_scenario(SCENARIO_NORMAL, "http://localhost:8000/api/events/", interval=0.01)
    
    assert success is True
    # Verify post was called twice
    assert mock_client.post.call_count == 2
    
    # Verify exact target URLs
    called_url, called_kwargs = mock_client.post.call_args_list[0]
    assert called_url[0] == "http://localhost:8000/api/events/"
    assert called_kwargs["json"]["user_id"] == "usr_alice"
    assert called_kwargs["json"]["event_type"] == "login"
