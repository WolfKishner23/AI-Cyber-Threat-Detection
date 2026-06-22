"""
LLM Provider abstraction layer.

Architecture:
    BaseLLMProvider (abstract interface)
        ├── MockLLMProvider      (deterministic, used in tests and default)
        ├── OpenAIProvider       (Phase 6+ real integration)
        └── OllamaProvider       (Phase 6+ local model integration)

The provider selected is controlled via the ACTIVE_PROVIDER setting in
app/core/config.py (or passed directly in tests). Graph nodes never
import a specific provider — they always go through generate_risk_assessment().
"""

from __future__ import annotations

import json
import logging
from abc import ABC, abstractmethod
from typing import Any, Dict

from app.llm.schemas import RiskAssessmentResult

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Abstract Base
# ---------------------------------------------------------------------------

class BaseLLMProvider(ABC):
    """Abstract interface every LLM backend must implement."""

    @abstractmethod
    def complete(self, prompt: str) -> str:
        """Send prompt, return raw text response from the model."""
        ...

    def parse_response(self, raw: str) -> Dict[str, Any]:
        """Extract and parse the JSON block from the model response."""
        # Strip markdown fences if present
        text = raw.strip()
        if text.startswith("```"):
            text = text.split("```")[1]
            if text.startswith("json"):
                text = text[4:]
        return json.loads(text.strip())


# ---------------------------------------------------------------------------
# MockLLMProvider  (deterministic — no external calls)
# ---------------------------------------------------------------------------

class MockLLMProvider(BaseLLMProvider):
    """
    Deterministic mock provider used in tests and as the Phase 6 default.

    Scoring rules mirror the old heuristics so existing test assertions
    remain stable, but the output is now fully structured and
    reasoning is generated from a template.
    """

    # Action thresholds
    _THRESHOLDS = {
        "brute_force":          {"score": 90, "action": "lock_account"},
        "successful_brute_force": {"score": 95, "action": "lock_account"},
        "credential_compromise": {"score": 90, "action": "lock_account"},
        "impossible_travel":    {"score": 75, "action": "force_password_reset"},
        "new_device_login":     {"score": 35, "action": "monitor"},
        "new_device":           {"score": 35, "action": "monitor"},
    }

    def complete(self, prompt: str) -> str:
        """
        Derive a deterministic structured response from the prompt content.
        This avoids any external API calls while producing realistic outputs.
        """
        # Parse key details out of the prompt (simple keyword scan)
        alert_type = self._extract_field(prompt, "Alert Type:")
        previous_alert_count = self._extract_int(prompt, "Total Previous Alerts:")
        ip_risk = self._extract_int(prompt, "Risk Score:")  # IP reputation score

        threshold = self._THRESHOLDS.get(alert_type, {"score": 50, "action": "monitor"})
        base_score = threshold["score"]
        action = threshold["action"]

        # Boost score based on history
        score_boost = 0
        if previous_alert_count > 0:
            score_boost += 10
        if ip_risk >= 60:
            score_boost += 5

        final_score = min(100, base_score + score_boost)
        risk_level = RiskAssessmentResult.derive_risk_level(final_score)
        confidence = 82 if previous_alert_count > 0 else 75

        reasoning = (
            f"The alert type '{alert_type}' is a strong indicator of malicious activity. "
            f"The user has {previous_alert_count} previous alerts on record, suggesting a "
            f"repeated pattern of suspicious behaviour. "
            f"The originating IP has a risk score of {ip_risk}/100 "
            f"({'suspicious' if ip_risk >= 60 else 'unknown/low risk'}). "
            f"Combining alert severity, recurrence, and IP reputation yields a final "
            f"risk score of {final_score}/100 ({risk_level}). "
            f"The recommended action is '{action}'."
        )

        result = {
            "risk_score": final_score,
            "confidence_score": confidence,
            "risk_level": risk_level,
            "recommended_action": action,
            "reasoning": reasoning,
        }
        return json.dumps(result)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _extract_field(text: str, label: str) -> str:
        for line in text.splitlines():
            if label in line:
                return line.split(label, 1)[-1].strip()
        return "unknown"

    @staticmethod
    def _extract_int(text: str, label: str) -> int:
        for line in text.splitlines():
            if label in line:
                try:
                    return int(line.split(label, 1)[-1].strip())
                except ValueError:
                    return 0
        return 0
