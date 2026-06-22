"""
Phase 6B Tool Selection Prompt.
Prompt builder for LLM to intelligently select tools based on alert context.
"""
from typing import Any, Dict
from app.llm.tool_registry import get_available_tools

def build_tool_selection_prompt(alert: Dict[str, Any], investigation_summary: str) -> str:
    """Build a prompt asking the LLM to select required tools."""
    alert_type = alert.get("alert_type", "unknown")
    severity = alert.get("severity", "unknown")
    status = alert.get("status", "unknown")
    
    available_tools = get_available_tools()
    
    prompt = f"""You are a Cybersecurity Evidence Collection AI.
Your task is to select the minimum required tools to investigate the following alert.

ALERT:
- Type: {alert_type}
- Severity: {severity}
- Status: {status}

INVESTIGATION SUMMARY SO FAR:
{investigation_summary or "No summary available yet."}

AVAILABLE TOOLS:
{", ".join(available_tools)}

GUIDANCE:
- impossible_travel: select location_history, user_history, ip_reputation
- new_device: select device_history, previous_alerts
- brute_force or credential_compromise: select user_history, previous_alerts, ip_reputation
- For other alerts, use your best judgment to select the most relevant tools.

Respond with ONLY a valid JSON object, no other text:
{{
  "required_tools": [
    "tool_name_1",
    "tool_name_2"
  ]
}}"""
    return prompt
