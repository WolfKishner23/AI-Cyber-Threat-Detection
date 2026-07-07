import uuid
from datetime import datetime, timedelta
from typing import Any, Dict, List

# Scenario Constants
SCENARIO_NORMAL = "normal_activity"
SCENARIO_IMPOSSIBLE_TRAVEL = "impossible_travel"
SCENARIO_BRUTE_FORCE = "brute_force"
SCENARIO_NEW_DEVICE = "new_device"
SCENARIO_CREDENTIAL_COMPROMISE = "credential_compromise"
SCENARIO_PASSWORD_RESET = "password_reset_workflow"
SCENARIO_BANK_ACCOUNT_THEFT = "bank_account_theft"

def generate_scenario_id() -> str:
    return str(uuid.uuid4())

def get_normal_activity(base_time: datetime, scenario_id: str, customer_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scenario A: Normal Employee Activity (Non-Attack)
    Sequence: login -> logout
    Time separation: 8 hours
    """
    total_steps = 2
    events = []
    user_id = customer_profile["customer_id"]

    # 1. Login Event
    events.append({
        "user_id": user_id,
        "event_type": "login",
        "location": "London, UK",
        "ip_address": "198.51.100.10",
        "device_name": "Alice-MacBook",
        "timestamp": base_time.isoformat(),
        "raw_payload": {
            "status": "success",
            "mfa_method": "totp",
            "session_id": str(uuid.uuid4()),
            "simulation": {
                "scenario": SCENARIO_NORMAL,
                "scenario_id": scenario_id,
                "is_attack": False,
                "step": 1,
                "total_steps": total_steps,
                "expected_detection": [],
                "customer_profile": customer_profile,
                "issue_summary": "Normal user authentication."
            }
        }
    })

    # 2. Logout Event
    events.append({
        "user_id": user_id,
        "event_type": "logout",
        "location": "London, UK",
        "ip_address": "198.51.100.10",
        "device_name": "Alice-MacBook",
        "timestamp": (base_time + timedelta(hours=8)).isoformat(),
        "raw_payload": {
            "status": "success",
            "session_id": events[0]["raw_payload"]["session_id"],
            "simulation": {
                "scenario": SCENARIO_NORMAL,
                "scenario_id": scenario_id,
                "is_attack": False,
                "step": 2,
                "total_steps": total_steps,
                "expected_detection": [],
                "customer_profile": customer_profile,
                "issue_summary": "Normal user session termination."
            }
        }
    })

    return events

def get_impossible_travel(base_time: datetime, scenario_id: str, customer_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scenario B: Impossible Travel (Attack)
    Sequence: login from London -> login from Tokyo
    Time separation: 5 minutes
    """
    total_steps = 2
    events = []
    user_id = customer_profile["customer_id"]

    # 1. London Login
    events.append({
        "user_id": user_id,
        "event_type": "login",
        "location": "London, UK",
        "ip_address": "198.51.100.12",
        "device_name": "Bob-Laptop",
        "timestamp": base_time.isoformat(),
        "raw_payload": {
            "status": "success",
            "simulation": {
                "scenario": SCENARIO_IMPOSSIBLE_TRAVEL,
                "scenario_id": scenario_id,
                "is_attack": True,
                "step": 1,
                "total_steps": total_steps,
                "expected_detection": ["impossible_travel"],
                "customer_profile": customer_profile,
                "issue_summary": "Impossible travel velocity detected between London and Tokyo."
            }
        }
    })

    # 2. Tokyo Login (5 minutes later)
    events.append({
        "user_id": user_id,
        "event_type": "login",
        "location": "Tokyo, Japan",
        "ip_address": "203.0.113.45",
        "device_name": "Bob-Laptop",
        "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
        "raw_payload": {
            "status": "success",
            "simulation": {
                "scenario": SCENARIO_IMPOSSIBLE_TRAVEL,
                "scenario_id": scenario_id,
                "is_attack": True,
                "step": 2,
                "total_steps": total_steps,
                "expected_detection": ["impossible_travel"],
                "customer_profile": customer_profile,
                "issue_summary": "Impossible travel velocity detected between London and Tokyo."
            }
        }
    })

    return events

def get_brute_force(base_time: datetime, scenario_id: str, customer_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scenario C: Brute Force Attack (Attack)
    Sequence: 5x failed_login -> 1x successful_login (same user, same IP)
    Time separation: 10 seconds between attempts
    """
    total_steps = 6
    events = []
    user_id = customer_profile["customer_id"]
    ip = "192.0.2.78"
    device = "Unknown-Device"
    location = "Berlin, Germany"

    # 1-5. Failed Logins
    for step in range(1, 6):
        events.append({
            "user_id": user_id,
            "event_type": "failed_login",
            "location": location,
            "ip_address": ip,
            "device_name": device,
            "timestamp": (base_time + timedelta(seconds=10 * (step - 1))).isoformat(),
            "raw_payload": {
                "status": "failed",
                "failure_reason": "invalid_password",
                "attempt_number": step,
                "simulation": {
                    "scenario": SCENARIO_BRUTE_FORCE,
                    "scenario_id": scenario_id,
                    "is_attack": True,
                    "step": step,
                    "total_steps": total_steps,
                    "expected_detection": ["brute_force"],
                "customer_profile": customer_profile,
                "issue_summary": "High frequency of failed authentication attempts."
                }
            }
        })

    # 6. Successful Login (10 seconds after final failure)
    events.append({
        "user_id": user_id,
        "event_type": "login",
        "location": location,
        "ip_address": ip,
        "device_name": device,
        "timestamp": (base_time + timedelta(seconds=10 * 5)).isoformat(),
        "raw_payload": {
            "status": "success",
            "simulation": {
                "scenario": SCENARIO_BRUTE_FORCE,
                "scenario_id": scenario_id,
                "is_attack": True,
                "step": 6,
                "total_steps": total_steps,
                "expected_detection": ["brute_force"],
                "customer_profile": customer_profile,
                "issue_summary": "High frequency of failed authentication attempts followed by success."
            }
        }
    })

    return events

def get_new_device(base_time: datetime, scenario_id: str, customer_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scenario D: New Device Login (Legitimate / Suspect)
    Sequence: login from previously unseen device
    """
    total_steps = 1
    events = []
    user_id = customer_profile["customer_id"]

    events.append({
        "user_id": user_id,
        "event_type": "login",
        "location": "San Francisco, USA",
        "ip_address": "198.51.100.55",
        "device_name": "David-New-Tablet",
        "timestamp": base_time.isoformat(),
        "raw_payload": {
            "status": "success",
            "is_new_device": True,
            "simulation": {
                "scenario": SCENARIO_NEW_DEVICE,
                "scenario_id": scenario_id,
                "is_attack": False,
                "step": 1,
                "total_steps": total_steps,
                "expected_detection": ["new_device"],
                "customer_profile": customer_profile,
                "issue_summary": "Authentication from previously unseen device footprint."
            }
        }
    })

    return events

def get_credential_compromise(base_time: datetime, scenario_id: str, customer_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scenario E: Credential Compromise (Attack)
    Sequence: 3 failed_login -> successful_login -> password_reset -> new_device_login
    """
    total_steps = 6
    events = []
    user_id = customer_profile["customer_id"]
    attacker_ip = "185.190.140.32"
    attacker_location = "Moscow, Russia"
    
    # 1-3. Failed Logins by Attacker
    for step in range(1, 4):
        events.append({
            "user_id": user_id,
            "event_type": "failed_login",
            "location": attacker_location,
            "ip_address": attacker_ip,
            "device_name": "Linux-CLI",
            "timestamp": (base_time + timedelta(seconds=15 * (step - 1))).isoformat(),
            "raw_payload": {
                "status": "failed",
                "failure_reason": "invalid_password",
                "simulation": {
                    "scenario": SCENARIO_CREDENTIAL_COMPROMISE,
                    "scenario_id": scenario_id,
                    "is_attack": True,
                    "step": step,
                    "total_steps": total_steps,
                    "expected_detection": ["credential_compromise"],
                "customer_profile": customer_profile,
                "issue_summary": "Multiple failures across regions followed by password reset."
                }
            }
        })

    # 4. Successful Login by Attacker (2 minutes after failures)
    events.append({
        "user_id": user_id,
        "event_type": "login",
        "location": attacker_location,
        "ip_address": attacker_ip,
        "device_name": "Linux-CLI",
        "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
        "raw_payload": {
            "status": "success",
            "simulation": {
                "scenario": SCENARIO_CREDENTIAL_COMPROMISE,
                "scenario_id": scenario_id,
                "is_attack": True,
                "step": 4,
                "total_steps": total_steps,
                "expected_detection": ["credential_compromise"],
                "customer_profile": customer_profile,
                "issue_summary": "Multiple failures across regions followed by password reset."
            }
        }
    })

    # 5. Password Reset by Attacker (1 minute after success)
    events.append({
        "user_id": user_id,
        "event_type": "password_reset",
        "location": attacker_location,
        "ip_address": attacker_ip,
        "device_name": "Linux-CLI",
        "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
        "raw_payload": {
            "status": "success",
            "action": "password_changed",
            "simulation": {
                "scenario": SCENARIO_CREDENTIAL_COMPROMISE,
                "scenario_id": scenario_id,
                "is_attack": True,
                "step": 5,
                "total_steps": total_steps,
                "expected_detection": ["credential_compromise"],
                "customer_profile": customer_profile,
                "issue_summary": "Multiple failures across regions followed by password reset."
            }
        }
    })

    # 6. New Device Login (30 seconds after reset)
    events.append({
        "user_id": user_id,
        "event_type": "login",
        "location": attacker_location,
        "ip_address": attacker_ip,
        "device_name": "Attacker-Malicious-Browser",
        "timestamp": (base_time + timedelta(minutes=3, seconds=30)).isoformat(),
        "raw_payload": {
            "status": "success",
            "is_new_device": True,
            "simulation": {
                "scenario": SCENARIO_CREDENTIAL_COMPROMISE,
                "scenario_id": scenario_id,
                "is_attack": True,
                "step": 6,
                "total_steps": total_steps,
                "expected_detection": ["credential_compromise"],
                "customer_profile": customer_profile,
                "issue_summary": "Multiple failures across regions followed by password reset."
            }
        }
    })

    return events

def get_password_reset_workflow(base_time: datetime, scenario_id: str, customer_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scenario F: Password Reset Workflow (Legitimate)
    Sequence: failed_login -> password_reset -> successful_login
    """
    total_steps = 3
    events = []
    user_id = customer_profile["customer_id"]
    location = "Chicago, USA"
    ip = "198.51.100.80"
    device = "Frank-Windows-PC"

    # 1. Failed Login (User forgot password)
    events.append({
        "user_id": user_id,
        "event_type": "failed_login",
        "location": location,
        "ip_address": ip,
        "device_name": device,
        "timestamp": base_time.isoformat(),
        "raw_payload": {
            "status": "failed",
            "failure_reason": "invalid_password",
            "simulation": {
                "scenario": SCENARIO_PASSWORD_RESET,
                "scenario_id": scenario_id,
                "is_attack": False,
                "step": 1,
                "total_steps": total_steps,
                "expected_detection": [],
                "customer_profile": customer_profile,
                "issue_summary": "User forgot password and initiated reset workflow."
            }
        }
    })

    # 2. Password Reset (2 minutes later)
    events.append({
        "user_id": user_id,
        "event_type": "password_reset",
        "location": location,
        "ip_address": ip,
        "device_name": device,
        "timestamp": (base_time + timedelta(minutes=2)).isoformat(),
        "raw_payload": {
            "status": "success",
            "action": "password_changed",
            "simulation": {
                "scenario": SCENARIO_PASSWORD_RESET,
                "scenario_id": scenario_id,
                "is_attack": False,
                "step": 2,
                "total_steps": total_steps,
                "expected_detection": [],
                "customer_profile": customer_profile,
                "issue_summary": "User forgot password and initiated reset workflow."
            }
        }
    })

    # 3. Successful Login (1 minute after reset)
    events.append({
        "user_id": user_id,
        "event_type": "login",
        "location": location,
        "ip_address": ip,
        "device_name": device,
        "timestamp": (base_time + timedelta(minutes=3)).isoformat(),
        "raw_payload": {
            "status": "success",
            "simulation": {
                "scenario": SCENARIO_PASSWORD_RESET,
                "scenario_id": scenario_id,
                "is_attack": False,
                "step": 3,
                "total_steps": total_steps,
                "expected_detection": [],
                "customer_profile": customer_profile,
                "issue_summary": "User forgot password and initiated reset workflow."
            }
        }
    })

    return events

def get_bank_account_theft(base_time: datetime, scenario_id: str, customer_profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Scenario G: Bank Account Impossible Travel
    Sequence: bank_account_access from one location -> bank_account_access from London
    Time separation: 5 minutes
    """
    total_steps = 2
    events = []
    user_id = customer_profile["customer_id"]

    # 1. Initial Access
    events.append({
        "user_id": user_id,
        "event_type": "bank_account_access",
        "location": "Paris, France",
        "ip_address": "198.51.100.15",
        "device_name": "User-Phone",
        "target_resource": "Bank Account 123456789",
        "timestamp": base_time.isoformat(),
        "raw_payload": {
            "status": "success",
            "simulation": {
                "scenario": SCENARIO_BANK_ACCOUNT_THEFT,
                "scenario_id": scenario_id,
                "is_attack": True,
                "step": 1,
                "total_steps": total_steps,
                "expected_detection": ["impossible_travel"],
                "customer_profile": customer_profile,
                "issue_summary": "Impossible travel velocity for bank account access detected."
            }
        }
    })

    # 2. London Access (5 minutes later)
    events.append({
        "user_id": user_id,
        "event_type": "bank_account_access",
        "location": "London, UK",
        "ip_address": "203.0.113.48",
        "device_name": "Hacker-Laptop",
        "target_resource": "Bank Account 123456789",
        "timestamp": (base_time + timedelta(minutes=5)).isoformat(),
        "raw_payload": {
            "status": "success",
            "simulation": {
                "scenario": SCENARIO_BANK_ACCOUNT_THEFT,
                "scenario_id": scenario_id,
                "is_attack": True,
                "step": 2,
                "total_steps": total_steps,
                "expected_detection": ["impossible_travel"],
                "customer_profile": customer_profile,
                "issue_summary": "Impossible travel velocity for bank account access detected."
            }
        }
    })

    return events

# Map names to generator functions
SCENARIOS_MAP = {
    SCENARIO_NORMAL: get_normal_activity,
    SCENARIO_IMPOSSIBLE_TRAVEL: get_impossible_travel,
    SCENARIO_BRUTE_FORCE: get_brute_force,
    SCENARIO_NEW_DEVICE: get_new_device,
    SCENARIO_CREDENTIAL_COMPROMISE: get_credential_compromise,
    SCENARIO_PASSWORD_RESET: get_password_reset_workflow,
    SCENARIO_BANK_ACCOUNT_THEFT: get_bank_account_theft
}
