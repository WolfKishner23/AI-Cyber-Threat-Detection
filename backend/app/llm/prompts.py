"""
prompts.py — JSON-only LLM prompt builder for risk assessment.
"""
import json
from typing import Any, Dict


def build_risk_assessment_prompt(alert: Dict[str, Any], evidence: Dict[str, Any]) -> str:
    alert_type = alert.get("alert_type", "unknown")
    severity   = alert.get("severity", "unknown")
    status     = alert.get("status", "unknown")

    prev_alerts  = evidence.get("previous_alerts", {})
    alert_count  = prev_alerts.get("alert_count", 0)
    severities   = prev_alerts.get("severities", {})

    ip_rep       = evidence.get("ip_reputation", {})
    ip_address   = ip_rep.get("ip", "unknown")
    ip_reputation = ip_rep.get("reputation", "unknown")
    ip_risk      = ip_rep.get("risk_score", 0)

    user_hist    = evidence.get("user_history", {})
    event_count  = user_hist.get("event_count", 0)

    device_hist  = evidence.get("device_history", {})
    devices      = device_hist.get("devices", [])

    loc_hist     = evidence.get("location_history", {})
    locations    = loc_hist.get("locations", [])

    return f"""Analyze this security alert and return a risk assessment as JSON only.

ALERT:
- Type: {alert_type}
- Severity: {severity}
- Status: {status}

EVIDENCE:
- Previous alerts for this user: {alert_count}
- Severity breakdown: {json.dumps(severities)}
- IP address: {ip_address}
- IP reputation: {ip_reputation} (risk score: {ip_risk}/100)
- Recent user events: {event_count}
- Known devices: {devices}
- Known locations: {locations}

SCORING GUIDANCE:
- brute_force / credential_compromise with prior alerts → 85-100
- impossible_travel with prior alerts → 70-90
- new_device from known user and trusted IP → 30-50
- Unknown or benign activity → 0-40

Return ONLY this JSON (no markdown, no extra text):
{{
  "risk_score": <integer 0-100>,
  "confidence_score": <integer 0-100>,
  "reasoning": "<one to two sentence explanation>"
}}"""
