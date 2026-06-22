from typing import Dict, Any, Tuple, List
from sqlalchemy.orm import Session
from app.llm.client import LLMClient
from app.llm.tool_registry import get_available_tools
from app.tools import (
    get_user_history,
    get_device_history,
    get_location_history,
    get_previous_alerts,
    get_incident_history,
    get_ip_reputation
)
import logging

logger = logging.getLogger(__name__)

class AutonomousInvestigationAgent:
    def __init__(self, client: LLMClient, db: Session, max_iterations: int = 5):
        self._client = client
        self._db = db
        self._max_iterations = max_iterations
        self._available_tools = get_available_tools()

    def run(
        self,
        alert: Dict[str, Any],
        security_event: Dict[str, Any],
        initial_summary: str,
        initial_trace: List[str]
    ) -> Tuple[Dict[str, Any], str, List[str], List[str], Dict[str, Any]]:
        """
        Runs the ReAct autonomous loop.
        Returns: (collected_evidence, investigation_summary, tools_used, reasoning_trace, tool_outputs)
        """
        evidence: Dict[str, Any] = {}
        tool_outputs: Dict[str, Any] = {}
        tools_used: List[str] = []
        reasoning_trace = list(initial_trace)
        investigation_summary = initial_summary
        
        user_id = security_event.get("user_id")
        ip_address = security_event.get("ip_address")
        
        reasoning_trace.append("Autonomous Agent: Starting investigation loop.")
        
        for iteration in range(self._max_iterations):
            try:
                # 1. Thought & Select Tool
                step_result = self._client.execute_autonomous_step(
                    alert=alert,
                    investigation_summary=investigation_summary,
                    collected_evidence=evidence,
                    tools_used=tools_used
                )
                
                thought = step_result.get("thought", "")
                action = step_result.get("action", "")
                reasoning = step_result.get("reasoning", "")
                
                reasoning_trace.append(f"Autonomous Agent Iteration {iteration+1} Thought: {thought}")
                
                # 2. Check Finish Condition
                if action == "finish" or action not in self._available_tools:
                    if action == "finish":
                        reasoning_trace.append(f"Autonomous Agent: Finished. Reasoning: {reasoning}")
                    else:
                        reasoning_trace.append(f"Autonomous Agent: Invalid action '{action}'. Finishing.")
                    break
                    
                # Prevent duplicates
                if action in tools_used:
                    reasoning_trace.append(f"Autonomous Agent: Tool '{action}' already used. Finishing.")
                    break
                    
                reasoning_trace.append(f"Autonomous Agent: Executing tool '{action}'. Reasoning: {reasoning}")
                
                # 3. Execute Tool
                result = {}
                if action == "user_history" and user_id:
                    result = get_user_history(self._db, user_id)
                elif action == "device_history" and user_id:
                    result = get_device_history(self._db, user_id)
                elif action == "location_history" and user_id:
                    result = get_location_history(self._db, user_id)
                elif action == "previous_alerts" and user_id:
                    result = get_previous_alerts(self._db, user_id)
                elif action == "incident_history" and user_id:
                    result = get_incident_history(self._db, user_id)
                elif action == "ip_reputation" and ip_address:
                    result = get_ip_reputation(ip_address)
                    
                # 4. Observe Result
                evidence[action] = result
                tool_outputs[action] = result
                tools_used.append(action)
                
                # 5. Update Hypothesis / Summary
                investigation_summary += f"\n- Tool '{action}' completed."
                
            except Exception as exc:
                logger.error(f"Autonomous loop failed: {exc}")
                raise exc # Raise to trigger Phase 6B fallback
                
        else:
            reasoning_trace.append(f"Autonomous Agent: Reached max iterations ({self._max_iterations}). Finishing.")
            
        return evidence, investigation_summary, tools_used, reasoning_trace, tool_outputs
