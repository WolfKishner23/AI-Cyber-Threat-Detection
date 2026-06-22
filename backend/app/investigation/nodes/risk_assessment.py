"""
Risk Assessment Agent Node — Phase 6A.

Uses LLMClient.assess_risk() which calls OpenAI when the API key is
configured, and silently falls back to heuristic scoring otherwise.
The graph workflow will NEVER crash.
"""
import logging
from app.investigation.state import InvestigationState
from app.llm.client import LLMClient

logger = logging.getLogger(__name__)

# Module-level client — instantiated once per worker process
_client = LLMClient()


import json

def _get_fallback_action(risk_score: int) -> str:
    if risk_score >= 85:
        return "escalate_to_fraud_team"
    elif risk_score >= 65:
        return "force_password_reset"
    elif risk_score >= 35:
        return "require_mfa"
    else:
        return "monitor_account"

def assess_risk(state: InvestigationState) -> InvestigationState:
    """
    Risk Assessment Agent.

    Calls the OpenAI LLM directly to assess risk. If it fails or returns 
    invalid JSON, falls back to the heuristic scoring.
    Writes risk_score, confidence_score, risk_level, llm_reasoning,
    and recommended_action to the state, and appends to reasoning_trace.
    """
    alert    = state.get("alert", {})
    evidence = state.get("evidence", {})
    trace    = list(state.get("reasoning_trace", []))

    alert_type = alert.get("alert_type", "unknown")
    
    # Safely get evidence fields for prompt
    prev_alerts = evidence.get('previous_alerts', {})
    ip_rep = evidence.get('ip_reputation', {})
    user_hist = evidence.get('user_history', {})
    dev_hist = evidence.get('device_history', {})
    loc_hist = evidence.get('location_history', {})

    prompt = f"""You are an expert fraud analyst investigating suspicious online banking logins. 
Analyze the following security alert and evidence to determine the risk of account takeover or fraud.

Pay special attention to the following risk vectors:
- Impossible travel (logins from distant locations in an impossibly short timeframe)
- Brute-force attacks (repeated failed login attempts followed by success)
- New device logins (especially when combined with other anomalies)
- Suspicious IPs (known bad actors, VPNs, proxies, or high-risk regions)
- Previous fraud history (past alerts or warnings for this user account)

ALERT DETAILS:
- Type: {alert.get('alert_type')}
- Severity: {alert.get('severity')}
- Status: {alert.get('status')}

EVIDENCE COLLECTED:
- Previous fraud history / alerts: {prev_alerts.get('alert_count', 0)}
- IP address: {ip_rep.get('ip')}
- IP reputation risk score (suspicious IPs): {ip_rep.get('risk_score', 0)}/100
- Recent user events (including brute-force attempts): {user_hist.get('event_count', 0)}
- Known devices (identifying new device logins): {dev_hist.get('devices', [])}
- Known locations (identifying impossible travel): {loc_hist.get('locations', [])}
- Customer login history: {user_hist.get('login_history', [])}

SCORING GUIDANCE:
- Brute-force / credential compromise with prior alerts -> 85-100 (Critical Risk)
- Impossible travel with prior alerts -> 70-90 (High Risk)
- New device from known user and trusted IP -> 30-50 (Medium Risk)
- Unknown or benign activity -> 0-40 (Low Risk)

Return ONLY this JSON (no markdown, no extra text):
{{
  "risk_score": <integer 0-100>,
  "confidence_score": <integer 0-100>,
  "reasoning": "<one to two sentence explanation from a fraud analyst perspective>",
  "recommended_action": "<monitor_account|require_mfa|force_password_reset|temporarily_lock_account|escalate_to_fraud_team>"
}}"""

    llm_response = _client.generate_text(prompt)
    result = None

    if llm_response:
        raw = llm_response.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()
            
        try:
            parsed = json.loads(raw)
            parsed_risk = max(0, min(100, int(parsed.get("risk_score", 0))))
            parsed_conf = max(0, min(100, int(parsed.get("confidence_score", 0))))
            parsed_reasoning = str(parsed.get("reasoning", "")).strip()
            parsed_action = str(parsed.get("recommended_action", "")).strip()
            
            if parsed_reasoning and parsed_action:
                result = {
                    "risk_score": parsed_risk,
                    "confidence_score": parsed_conf,
                    "reasoning": parsed_reasoning,
                    "recommended_action": parsed_action
                }
        except Exception as exc:
            logger.warning(f"Failed to parse LLM risk assessment response: {exc}")

    # Fallback if LLM failed or returned invalid data
    if not result:
        fallback = _client.assess_risk(alert=alert, evidence=evidence)
        result = {
            "risk_score": fallback["risk_score"],
            "confidence_score": fallback["confidence_score"],
            "reasoning": fallback["reasoning"],
            "recommended_action": _get_fallback_action(fallback["risk_score"])
        }

    risk_score = result["risk_score"]
    confidence_score = result["confidence_score"]
    reasoning = result["reasoning"]
    recommended_action = result["recommended_action"]

    # Derive risk level from score
    if risk_score >= 85:
        risk_level = "critical"
    elif risk_score >= 65:
        risk_level = "high"
    elif risk_score >= 35:
        risk_level = "medium"
    else:
        risk_level = "low"

    trace.append(
        f"LLM Risk Assessment Agent: alert_type='{alert_type}' "
        f"-> risk_score={risk_score}, risk_level={risk_level}, "
        f"confidence={confidence_score}, action={recommended_action}."
    )
    trace.append(f"LLM Reasoning: {reasoning}")

    return {
        "risk_score":       risk_score,
        "confidence_score": confidence_score,
        "risk_level":       risk_level,
        "llm_reasoning":    reasoning,
        "recommended_action": recommended_action,
        "reasoning_trace":  trace,
    }
