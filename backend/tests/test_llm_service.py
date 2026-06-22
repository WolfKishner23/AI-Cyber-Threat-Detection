"""Tests for Phase 6A: Deterministic LLM Risk Assessment Service."""
import json
import pytest
from pydantic import ValidationError
from app.llm.schemas import RiskAssessmentResult
from app.llm.service import generate_risk_assessment


# ---------------------------------------------------------------------------
# Schema validation tests
# ---------------------------------------------------------------------------

class TestRiskAssessmentSchema:
    def test_valid_schema(self):
        r = RiskAssessmentResult(
            risk_score=85, confidence_score=90,
            risk_level="critical", recommended_action="lock_account",
            reasoning="Some reasoning."
        )
        assert r.risk_score == 85
        assert r.risk_level == "critical"

    def test_risk_score_min(self):
        r = RiskAssessmentResult(
            risk_score=0, confidence_score=50,
            risk_level="low", recommended_action="no_action", reasoning="R"
        )
        assert r.risk_score == 0

    def test_risk_score_max(self):
        r = RiskAssessmentResult(
            risk_score=100, confidence_score=95,
            risk_level="critical", recommended_action="lock_account", reasoning="R"
        )
        assert r.risk_score == 100

    def test_risk_score_below_min_raises(self):
        with pytest.raises(ValidationError):
            RiskAssessmentResult(
                risk_score=-1, confidence_score=50,
                risk_level="low", recommended_action="no_action", reasoning="R"
            )

    def test_risk_score_above_max_raises(self):
        with pytest.raises(ValidationError):
            RiskAssessmentResult(
                risk_score=101, confidence_score=50,
                risk_level="low", recommended_action="no_action", reasoning="R"
            )

    def test_confidence_below_min_raises(self):
        with pytest.raises(ValidationError):
            RiskAssessmentResult(
                risk_score=50, confidence_score=-1,
                risk_level="low", recommended_action="no_action", reasoning="R"
            )

    def test_confidence_above_max_raises(self):
        with pytest.raises(ValidationError):
            RiskAssessmentResult(
                risk_score=50, confidence_score=101,
                risk_level="medium", recommended_action="monitor", reasoning="R"
            )


# ---------------------------------------------------------------------------
# derive_risk_level tests
# ---------------------------------------------------------------------------

class TestDeriveRiskLevel:
    def test_critical(self):
        assert RiskAssessmentResult.derive_risk_level(100) == "critical"
        assert RiskAssessmentResult.derive_risk_level(85) == "critical"

    def test_high(self):
        assert RiskAssessmentResult.derive_risk_level(84) == "high"
        assert RiskAssessmentResult.derive_risk_level(65) == "high"

    def test_medium(self):
        assert RiskAssessmentResult.derive_risk_level(64) == "medium"
        assert RiskAssessmentResult.derive_risk_level(35) == "medium"

    def test_low(self):
        assert RiskAssessmentResult.derive_risk_level(34) == "low"
        assert RiskAssessmentResult.derive_risk_level(0) == "low"


# ---------------------------------------------------------------------------
# Service function tests
# ---------------------------------------------------------------------------

class TestGenerateRiskAssessment:
    def _evidence(self, alert_count=0, ip_risk=0):
        return {
            "previous_alerts": {"alert_count": alert_count, "alerts": []},
            "ip_reputation": {"risk_score": ip_risk, "reputation": "unknown"},
        }

    def test_brute_force_score_and_action(self):
        r = generate_risk_assessment("brute_force", self._evidence())
        assert r.risk_score >= 85
        assert r.recommended_action == "lock_account"
        assert r.risk_level in ["high", "critical"]

    def test_impossible_travel_score_and_action(self):
        r = generate_risk_assessment("impossible_travel", self._evidence())
        assert r.risk_score >= 65
        assert r.recommended_action == "force_password_reset"

    def test_new_device_score_and_action(self):
        r = generate_risk_assessment("new_device_login", self._evidence())
        assert r.risk_score <= 55
        assert r.recommended_action == "monitor"

    def test_previous_alerts_boost(self):
        r_no_hist = generate_risk_assessment("brute_force", self._evidence(alert_count=0))
        r_history  = generate_risk_assessment("brute_force", self._evidence(alert_count=5))
        assert r_history.risk_score >= r_no_hist.risk_score

    def test_high_ip_risk_boost(self):
        r_low_ip  = generate_risk_assessment("impossible_travel", self._evidence(ip_risk=0))
        r_high_ip = generate_risk_assessment("impossible_travel", self._evidence(ip_risk=80))
        assert r_high_ip.risk_score >= r_low_ip.risk_score

    def test_score_capped_at_100(self):
        # Both boosts on top of a high base score
        r = generate_risk_assessment("successful_brute_force", self._evidence(alert_count=10, ip_risk=90))
        assert r.risk_score <= 100

    def test_unknown_type_returns_default(self):
        r = generate_risk_assessment("some_unknown_type", self._evidence())
        assert 0 <= r.risk_score <= 100
        assert len(r.recommended_action) > 0

    def test_result_is_json_serializable(self):
        r = generate_risk_assessment("brute_force", self._evidence())
        # model_dump() returns plain python dict — should serialize without error
        dumped = json.dumps(r.model_dump())
        assert len(dumped) > 0

    def test_reasoning_is_not_empty(self):
        r = generate_risk_assessment("impossible_travel", self._evidence())
        assert len(r.reasoning) > 20

    def test_all_fields_present(self):
        r = generate_risk_assessment("brute_force", self._evidence())
        assert hasattr(r, "risk_score")
        assert hasattr(r, "confidence_score")
        assert hasattr(r, "risk_level")
        assert hasattr(r, "recommended_action")
        assert hasattr(r, "reasoning")
