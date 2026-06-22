from app.investigation.state import InvestigationState
from sqlalchemy.orm import Session
from langchain_core.runnables.config import RunnableConfig
from app.tools import (
    get_user_history,
    get_device_history,
    get_location_history,
    get_previous_alerts,
    get_incident_history,
    get_ip_reputation
)
from app.llm.client import LLMClient
from app.llm.tool_registry import get_available_tools
from app.investigation.autonomous_agent import AutonomousInvestigationAgent

# Instantiate client once per worker
_client = LLMClient()

def collect_evidence(state: InvestigationState, config: RunnableConfig) -> InvestigationState:
    """Gather contextual evidence using Autonomous Investigation Agent (Phase 6C), with Phase 6B fallback."""
    db: Session = config["configurable"]["db"]
    event_data = state.get("security_event", {})
    alert_data = state.get("alert", {})
    investigation_summary = state.get("investigation_summary", "")
    trace = list(state.get("reasoning_trace", []))
    
    agent = AutonomousInvestigationAgent(client=_client, db=db, max_iterations=5)
    
    try:
        # Phase 6C: Attempt Autonomous ReAct Loop
        evidence, summary, tools_used, trace, tool_outputs = agent.run(
            alert=alert_data,
            security_event=event_data,
            initial_summary=investigation_summary,
            initial_trace=trace
        )
        return {
            "evidence": evidence,
            "investigation_summary": summary,
            "tools_used": tools_used,
            "tool_outputs": tool_outputs,
            "reasoning_trace": trace
        }
    except Exception as exc:
        # Phase 6B: Fallback mode if autonomous agent fails (e.g., missing API key, JSON error)
        trace.append(f"Evidence Collection Agent: Autonomous agent failed ({exc}). Falling back to static execution.")
        
        user_id = event_data.get("user_id")
        ip_address = event_data.get("ip_address")
        
        tool_selection_result = _client.select_tools(alert_data, investigation_summary)
        required_tools = tool_selection_result.get("required_tools", [])
        
        all_tools = get_available_tools()
        if set(required_tools) == set(all_tools):
            trace.append("Evidence Collection Agent: Fallback mode activated, executing all tools.")
        else:
            trace.append(f"Evidence Collection Agent: LLM selected tools [{', '.join(required_tools)}]")
            
        evidence = {}
        tool_outputs = {}
        tools_used = []
        
        if user_id:
            if "user_history" in required_tools:
                evidence["user_history"] = get_user_history(db, user_id)
                tools_used.append("user_history")
            if "device_history" in required_tools:
                evidence["device_history"] = get_device_history(db, user_id)
                tools_used.append("device_history")
            if "location_history" in required_tools:
                evidence["location_history"] = get_location_history(db, user_id)
                tools_used.append("location_history")
            if "previous_alerts" in required_tools:
                evidence["previous_alerts"] = get_previous_alerts(db, user_id)
                tools_used.append("previous_alerts")
            if "incident_history" in required_tools:
                evidence["incident_history"] = get_incident_history(db, user_id)
                tools_used.append("incident_history")
                
        if ip_address and "ip_reputation" in required_tools:
            evidence["ip_reputation"] = get_ip_reputation(ip_address)
            tools_used.append("ip_reputation")
            
        tool_outputs = dict(evidence)
        
        if user_id:
            trace.append(f"Evidence Collection Agent: Executed selected tools for user {user_id}. Gathered {evidence.get('user_history', {}).get('event_count', 0)} recent events and {evidence.get('previous_alerts', {}).get('alert_count', 0)} previous alerts.")
        else:
            trace.append("Evidence Collection Agent: No user_id found. Tools returned empty sets.")
            
        return {
            "evidence": evidence,
            "tool_outputs": tool_outputs,
            "tools_used": tools_used,
            "reasoning_trace": trace
        }
