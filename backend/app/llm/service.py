"""
Risk Assessment Service — Phase 6A (deterministic, no external APIs).

generate_risk_assessment(alert_type, evidence) is the single entry point
used by the risk_assessment LangGraph node.
"""

from typing import Any, Dict
from app.llm.schemas import RiskAssessmentResult


# Scoring table: alert_type -> (base_score, action)
_SCORE_TABLE = {
    "impossible_travel":      (85, "force_password_reset"),
    "brute_force":            (90, "lock_account"),
    "successful_brute_force": (95, "lock_account"),
    "credential_compromise":  (90, "lock_account"),
    "new_device_login":       (40, "monitor"),
    "new_device":             (40, "monitor"),
}

_DEFAULT = (50, "monitor")


def generate_risk_assessment(
    alert_type: str,
    evidence: Dict[str, Any],
) -> RiskAssessmentResult:
    """
    Return a deterministic RiskAssessmentResult.

    Scoring logic:
      1. Look up base_score and action from alert_type.
      2. Add +10 if the user has previous alerts.
      3. Add +5  if the IP reputation score >= 60.
      4. Cap at 100.

    Args:
        alert_type: The alert type string from the alert dict.
        evidence:   The evidence dict from InvestigationState (contains
                    tool output sub-dicts keyed by tool name).
    """
    base_score, action = _SCORE_TABLE.get(alert_type, _DEFAULT)

    # Contextual boosts from evidence
    boost = 0
    previous_alerts = evidence.get("previous_alerts", {})
    alert_count = previous_alerts.get("alert_count", 0)
    if alert_count > 0:
        boost += 10

    ip_rep = evidence.get("ip_reputation", {})
    if ip_rep.get("risk_score", 0) >= 60:
        boost += 5

    final_score = min(100, base_score + boost)
    risk_level = RiskAssessmentResult.derive_risk_level(final_score)
    confidence = 85 if alert_count > 0 else 75

    reasoning = (
        f"Alert type '{alert_type}' has a base risk score of {base_score}. "
        f"User has {alert_count} previous alert(s) on record (+{10 if alert_count > 0 else 0} boost). "
        f"IP reputation risk score: {ip_rep.get('risk_score', 0)} "
        f"(+{5 if ip_rep.get('risk_score', 0) >= 60 else 0} boost). "
        f"Final risk score: {final_score}/100 — level: {risk_level}. "
        f"Recommended action: {action}."
    )

    return RiskAssessmentResult(
        risk_score=final_score,
        confidence_score=confidence,
        risk_level=risk_level,
        recommended_action=action,
        reasoning=reasoning,
    )
