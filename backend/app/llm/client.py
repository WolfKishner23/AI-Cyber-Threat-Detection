"""
LLMClient — Phase 6A Risk Assessment Client.

Uses OpenAI if OPENAI_API_KEY is configured.
Falls back to deterministic heuristic scoring automatically if:
  - API key is missing
  - OpenAI request fails
  - JSON parsing fails
  - Any exception occurs

The investigation workflow will NEVER crash.
"""
import json
import logging
from typing import Any, Dict, List

from app.core.config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Heuristic fallback scoring table (preserved from Phase 5)
# ---------------------------------------------------------------------------
_SCORE_TABLE: Dict[str, int] = {
    "impossible_travel":      85,
    "brute_force":            90,
    "successful_brute_force": 95,
    "credential_compromise":  90,
    "new_device_login":       40,
    "new_device":             40,
}
_DEFAULT_SCORE = 50


def _heuristic_assess(alert: Dict[str, Any], evidence: Dict[str, Any]) -> Dict[str, Any]:
    """Deterministic fallback scoring — identical logic to Phase 5."""
    alert_type = alert.get("alert_type", "unknown")
    base_score = _SCORE_TABLE.get(alert_type, _DEFAULT_SCORE)

    boost = 0
    previous_alerts = evidence.get("previous_alerts", {})
    alert_count = previous_alerts.get("alert_count", 0)
    if alert_count > 0:
        boost += 10

    ip_rep = evidence.get("ip_reputation", {})
    if ip_rep.get("risk_score", 0) >= 60:
        boost += 5

    final_score = min(100, base_score + boost)
    confidence = 85 if alert_count > 0 else 75

    reasoning = (
        f"[Heuristic fallback] Alert type '{alert_type}' base score: {base_score}. "
        f"Previous alerts: {alert_count} (+{10 if alert_count > 0 else 0}). "
        f"IP risk score: {ip_rep.get('risk_score', 0)} "
        f"(+{5 if ip_rep.get('risk_score', 0) >= 60 else 0}). "
        f"Final: {final_score}/100."
    )
    return {
        "risk_score": final_score,
        "confidence_score": confidence,
        "reasoning": reasoning,
    }


# ---------------------------------------------------------------------------
# LLMClient
# ---------------------------------------------------------------------------

class LLMClient:
    """
    OpenAI-backed risk assessment client with automatic heuristic fallback.

    Usage:
        client = LLMClient()
        result = client.assess_risk(alert, evidence)
        # result = {"risk_score": int, "confidence_score": int, "reasoning": str}
    """

    def __init__(self) -> None:
        self._api_key: str | None = settings.OPENAI_API_KEY
        self._model: str = settings.OPENAI_MODEL

        if self._api_key:
            logger.info(f"LLMClient initialised with model '{self._model}'.")
        else:
            logger.info(
                "OPENAI_API_KEY not set — LLMClient will use heuristic fallback for all requests."
            )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def assess_risk(
        self,
        alert: Dict[str, Any],
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Assess risk using OpenAI if available, otherwise use heuristic fallback.

        Returns:
            dict with keys: risk_score (int), confidence_score (int), reasoning (str)
        """
        if not self._api_key:
            logger.debug("No API key — using heuristic fallback.")
            return _heuristic_assess(alert, evidence)

        try:
            return self._call_openai(alert, evidence)
        except Exception as exc:
            logger.warning(
                f"OpenAI call failed ({type(exc).__name__}: {exc}). "
                "Falling back to heuristic scoring."
            )
            return _heuristic_assess(alert, evidence)

    # ------------------------------------------------------------------
    # Internal OpenAI call
    # ------------------------------------------------------------------

    def _call_openai(
        self,
        alert: Dict[str, Any],
        evidence: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Call OpenAI chat completions and parse JSON response."""
        from openai import OpenAI  # lazy import — only if key is present
        from app.llm.prompts import build_risk_assessment_prompt

        prompt = build_risk_assessment_prompt(alert=alert, evidence=evidence)

        client = OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity analyst AI. "
                        "Always respond with ONLY valid JSON. No markdown, no extra text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )

        raw = response.choices[0].message.content.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)

        # Validate and clamp ranges
        risk_score = max(0, min(100, int(parsed["risk_score"])))
        confidence_score = max(0, min(100, int(parsed["confidence_score"])))
        reasoning = str(parsed.get("reasoning", "")).strip()

        if not reasoning:
            raise ValueError("LLM returned empty reasoning.")

        logger.info(
            f"OpenAI assessment: risk_score={risk_score}, "
            f"confidence_score={confidence_score}"
        )
        return {
            "risk_score": risk_score,
            "confidence_score": confidence_score,
            "reasoning": reasoning,
        }

    def select_tools(self, alert: Dict[str, Any], investigation_summary: str) -> Dict[str, Any]:
        """
        Select required tools using OpenAI if available, otherwise fallback.
        
        Returns:
            dict with key: required_tools (list of str)
        """
        from app.llm.tool_registry import get_available_tools
        
        available = get_available_tools()
        fallback_response = {"required_tools": available}
        
        if not self._api_key:
            logger.debug("No API key — using heuristic fallback for tool selection.")
            return fallback_response
            
        try:
            result = self._call_openai_tool_selection(alert, investigation_summary)
            required_tools = result.get("required_tools", [])
            # Filter to only known tools
            valid_tools = [t for t in required_tools if t in available]
            return {"required_tools": valid_tools}
        except Exception as exc:
            logger.warning(
                f"OpenAI tool selection failed ({type(exc).__name__}: {exc}). "
                "Falling back to executing all tools."
            )
            return fallback_response
            
    def _call_openai_tool_selection(self, alert: Dict[str, Any], investigation_summary: str) -> Dict[str, Any]:
        """Call OpenAI chat completions and parse JSON response for tool selection."""
        from openai import OpenAI  # lazy import
        from app.llm.tool_selection_prompt import build_tool_selection_prompt

        prompt = build_tool_selection_prompt(alert=alert, investigation_summary=investigation_summary)

        client = OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity evidence collection AI. "
                        "Always respond with ONLY valid JSON. No markdown, no extra text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        
        required_tools = parsed.get("required_tools", [])
        if not isinstance(required_tools, list):
            raise ValueError("LLM returned non-list for required_tools.")
            
        logger.info(f"OpenAI tool selection raw output: {required_tools}")
        return {"required_tools": required_tools}

    def execute_autonomous_step(
        self, 
        alert: Dict[str, Any], 
        investigation_summary: str,
        collected_evidence: Dict[str, Any],
        tools_used: List[str]
    ) -> Dict[str, Any]:
        """
        Execute one step of the ReAct autonomous loop.
        Returns a dict: {"thought": str, "action": str, "reasoning": str}
        Raises an exception if the API key is missing or the request fails, 
        which triggers the Phase 6B fallback in the caller.
        """
        if not self._api_key:
            raise ValueError("No API key available for autonomous step.")

        from openai import OpenAI
        from app.llm.autonomous_prompt import build_autonomous_prompt

        prompt = build_autonomous_prompt(
            alert=alert,
            investigation_summary=investigation_summary,
            collected_evidence=collected_evidence,
            tools_used=tools_used
        )

        client = OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are an autonomous cybersecurity investigation AI. "
                        "Always respond with ONLY valid JSON. No markdown, no extra text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=400,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        
        # Validate schema
        if "thought" not in parsed or "action" not in parsed or "reasoning" not in parsed:
            raise ValueError("LLM returned malformed JSON for autonomous step.")
            
        logger.info(f"Autonomous Step: Action={parsed['action']}")
        return parsed

    def plan_response(
        self,
        alert: Dict[str, Any],
        investigation_summary: str,
        evidence: Dict[str, Any],
        risk_score: int,
        confidence_score: int
    ) -> Dict[str, str] | None:
        """
        Recommend an action using OpenAI if available.
        Returns None if API key missing, failure, or invalid JSON.
        """
        if not self._api_key:
            logger.debug("No API key — cannot plan response with LLM.")
            return None

        try:
            return self._call_openai_plan_response(
                alert, investigation_summary, evidence, risk_score, confidence_score
            )
        except Exception as exc:
            logger.warning(
                f"OpenAI plan response failed ({type(exc).__name__}: {exc}). "
            )
            return None

    def _call_openai_plan_response(
        self,
        alert: Dict[str, Any],
        investigation_summary: str,
        evidence: Dict[str, Any],
        risk_score: int,
        confidence_score: int
    ) -> Dict[str, str]:
        from openai import OpenAI
        from app.llm.prompts import build_response_planning_prompt

        prompt = build_response_planning_prompt(
            alert=alert,
            investigation_summary=investigation_summary,
            evidence=evidence,
            risk_score=risk_score,
            confidence_score=confidence_score
        )

        client = OpenAI(api_key=self._api_key)
        response = client.chat.completions.create(
            model=self._model,
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a cybersecurity response planning AI. "
                        "Always respond with ONLY valid JSON. No markdown, no extra text."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=300,
        )

        raw = response.choices[0].message.content.strip()
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
            raw = raw.strip()

        parsed = json.loads(raw)
        
        # Validate schema
        if "recommended_action" not in parsed or "reasoning" not in parsed:
            raise ValueError("LLM returned malformed JSON for response planning.")
            
        logger.info(f"OpenAI response planning: Action={parsed['recommended_action']}")
        return {
            "recommended_action": str(parsed["recommended_action"]),
            "reasoning": str(parsed["reasoning"])
        }

    def generate_text(self, prompt: str) -> str | None:
        """
        Accepts a prompt and returns text from the model.
        Returns None if OPENAI_API_KEY is missing or the API call fails.
        """
        if not self._api_key:
            return None
            
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self._api_key)
            response = client.chat.completions.create(
                model=self._model,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.choices[0].message.content
        except Exception as exc:
            logger.warning(f"OpenAI generate_text call failed: {exc}")
            return None


