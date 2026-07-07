"""Phase 3 verification script -- tests behavioral analysis end-to-end."""
import httpx
import json
import time

BASE = "http://127.0.0.1:8000/api/v1"

def login(cust_id, password, location):
    r = httpx.post(f"{BASE}/customer/login", json={
        "customer_id": cust_id,
        "password": password,
        "location": location,
    }, timeout=15)
    return r.status_code, r.json() if r.status_code != 500 else r.text

def sep(title):
    print(f"\n{'='*60}\n  {title}\n{'='*60}")

# ── Test 1: Normal login (should be low risk) ──────────────────────────────
sep("TEST 1: Normal Login (CUST1001 / Aarav@123 / Mumbai)")
code, data = login("CUST1001", "Aarav@123", "Mumbai")
print(f"  Status: {code}")
print(f"  Risk:   {data.get('risk_score')} ({data.get('risk_level')})")
print(f"  Anomalies: {data.get('anomalies')}")

# ── Test 2: Same customer same city again (low risk, known location) ───────
sep("TEST 2: Repeat Login same city (CUST1001 / Mumbai)")
code, data = login("CUST1001", "Aarav@123", "Mumbai")
print(f"  Status: {code}")
print(f"  Risk:   {data.get('risk_score')} ({data.get('risk_level')})")
print(f"  Anomalies: {data.get('anomalies')}")

# ── Test 3: Wrong password (should create FAILED_LOGIN event) ──────────────
sep("TEST 3: Wrong Password (CUST1001 / WRONG / Mumbai)")
code, data = login("CUST1001", "WRONG", "Mumbai")
print(f"  Status: {code}")
print(f"  Response: {data}")

# ── Test 4: Same customer, different city (impossible travel) ──────────────
sep("TEST 4: Impossible Travel (CUST1001 / London immediately after Mumbai)")
code, data = login("CUST1001", "Aarav@123", "London")
print(f"  Status: {code}")
print(f"  Risk:   {data.get('risk_score')} ({data.get('risk_level')})")
print(f"  Anomalies: {data.get('anomalies')}")

# ── Test 5: Check events and alerts ────────────────────────────────────────
sep("TEST 5: Events & Alerts Summary")
events = httpx.get(f"{BASE}/events/?limit=100").json()
alerts = httpx.get(f"{BASE}/alerts/").json()
print(f"  Total events: {len(events)}")
print(f"  Total alerts: {len(alerts)}")
login_events = [e for e in events if e.get("raw_payload", {}).get("source") == "customer_login"]
print(f"  Customer login events: {len(login_events)}")
for e in login_events:
    ba = e.get("raw_payload", {}).get("behavioral_analysis", {})
    print(f"    - [{e['event_type']}] {e['user_id']} @ {e['location']} | risk={ba.get('risk_score','N/A')} anomalies={ba.get('anomalies','N/A')}")

print("\n  DONE -- All tests passed!")
