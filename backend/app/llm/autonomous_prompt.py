from typing import Dict, Any, List
import json

def build_autonomous_prompt(
    alert: Dict[str, Any], 
    investigation_summary: str,
    collected_evidence: Dict[str, Any],
    tools_used: List[str]
) -> str:
    """Build the prompt for the Autonomous Investigation Agent."""
    return f"""
You are an autonomous cybersecurity investigation agent. Your goal is to gather enough evidence to determine if the security alert represents a genuine threat.

Current Alert:
{json.dumps(alert, indent=2)}

Investigation Summary (Progress so far):
{investigation_summary or "No summary available yet."}

Tools Used So Far:
{json.dumps(tools_used, indent=2)}

Current Collected Evidence:
{json.dumps(collected_evidence, indent=2)}

You can choose exactly ONE of the following tools to execute next, or you can choose "finish" if you have enough evidence to conclude the investigation. Do NOT use a tool that you have already used.

Available Tools:
- get_user_history
- get_device_history
- get_location_history
- get_previous_alerts
- get_incident_history
- get_ip_reputation
- finish

Output EXACTLY and ONLY valid JSON in the following format:
{{
  "thought": "Your reasoning about what evidence is currently missing and what you should do next.",
  "action": "The name of the tool to use, or 'finish'",
  "reasoning": "A brief explanation of why this action is necessary."
}}
"""
