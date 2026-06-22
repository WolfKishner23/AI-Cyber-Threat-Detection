"""
tests/test_autonomous_investigation.py

Phase 6C tests:
- multi-step reasoning
- tool selection across iterations
- max iteration enforcement
- duplicate tool prevention
- fallback behavior
"""
import pytest
from unittest.mock import MagicMock, patch

from app.investigation.autonomous_agent import AutonomousInvestigationAgent
from app.llm.client import LLMClient
from app.llm.tool_registry import get_available_tools

# Helpers
def _make_alert():
    return {"alert_type": "impossible_travel", "severity": "high", "status": "open"}

def _make_event():
    return {"user_id": "usr_1", "ip_address": "1.1.1.1"}

class TestAutonomousAgent:
    def test_multi_step_reasoning(self):
        client = LLMClient()
        db = MagicMock()
        agent = AutonomousInvestigationAgent(client=client, db=db, max_iterations=5)
        
        # Mock execute_autonomous_step to return a sequence of actions
        client.execute_autonomous_step = MagicMock(side_effect=[
            {"thought": "Need location.", "action": "location_history", "reasoning": "checking location"},
            {"thought": "Need ip info.", "action": "ip_reputation", "reasoning": "checking ip"},
            {"thought": "Done.", "action": "finish", "reasoning": "got everything"}
        ])
        
        with patch("app.investigation.autonomous_agent.get_location_history", return_value={"locations": ["NYC"]}), \
             patch("app.investigation.autonomous_agent.get_ip_reputation", return_value={"risk": 80}):
            
            evidence, summary, tools_used, trace, _ = agent.run(_make_alert(), _make_event(), "", [])
            
        assert tools_used == ["location_history", "ip_reputation"]
        assert "location_history" in evidence
        assert "ip_reputation" in evidence
        assert "Need location." in trace[1]
        assert "Need ip info." in trace[3]
        
    def test_max_iteration_enforcement(self):
        client = LLMClient()
        db = MagicMock()
        # Set max_iterations to 3
        agent = AutonomousInvestigationAgent(client=client, db=db, max_iterations=3)
        
        # Make the LLM never say finish, and always use different tools to not trigger duplicate prevention
        client.execute_autonomous_step = MagicMock(side_effect=[
            {"thought": "T1", "action": "location_history", "reasoning": "R1"},
            {"thought": "T2", "action": "ip_reputation", "reasoning": "R2"},
            {"thought": "T3", "action": "user_history", "reasoning": "R3"},
            {"thought": "T4", "action": "device_history", "reasoning": "R4"} # Should not be reached
        ])
        
        with patch("app.investigation.autonomous_agent.get_location_history"), \
             patch("app.investigation.autonomous_agent.get_ip_reputation"), \
             patch("app.investigation.autonomous_agent.get_user_history"):
            
            evidence, summary, tools_used, trace, _ = agent.run(_make_alert(), _make_event(), "", [])
            
        assert len(tools_used) == 3
        assert "Reached max iterations (3)" in trace[-1]
        assert client.execute_autonomous_step.call_count == 3
        
    def test_duplicate_tool_prevention(self):
        client = LLMClient()
        db = MagicMock()
        agent = AutonomousInvestigationAgent(client=client, db=db, max_iterations=5)
        
        # Request the same tool twice
        client.execute_autonomous_step = MagicMock(side_effect=[
            {"thought": "T1", "action": "location_history", "reasoning": "R1"},
            {"thought": "T2", "action": "location_history", "reasoning": "R2"},
            {"thought": "T3", "action": "finish", "reasoning": "R3"}
        ])
        
        with patch("app.investigation.autonomous_agent.get_location_history"):
            evidence, summary, tools_used, trace, _ = agent.run(_make_alert(), _make_event(), "", [])
            
        # It should halt after the duplicate tool is requested
        assert tools_used == ["location_history"]
        assert "already used" in trace[-1]
        
    def test_fallback_behavior_in_node(self):
        # We test that the evidence_collection node handles an exception in agent.run by falling back to Phase 6B logic
        from app.investigation.nodes.evidence_collection import collect_evidence
        
        state = {
            "security_event": _make_event(),
            "alert": _make_alert(),
            "investigation_summary": "",
            "reasoning_trace": []
        }
        config = {"configurable": {"db": MagicMock()}}
        
        # Force agent to crash, which triggers fallback
        with patch("app.investigation.autonomous_agent.AutonomousInvestigationAgent.run", side_effect=Exception("LLM Down")), \
             patch("app.investigation.nodes.evidence_collection._client.select_tools", return_value={"required_tools": ["user_history"]}), \
             patch("app.investigation.nodes.evidence_collection.get_user_history") as mock_user_history:
                 
            result = collect_evidence(state, config)
            
            assert "Autonomous agent failed (LLM Down). Falling back to static execution." in result["reasoning_trace"][0]
            assert result["tools_used"] == ["user_history"]
            mock_user_history.assert_called_once()

    def test_multi_step_brute_force(self):
        client = LLMClient()
        db = MagicMock()
        agent = AutonomousInvestigationAgent(client=client, db=db, max_iterations=5)
        
        client.execute_autonomous_step = MagicMock(side_effect=[
            {"thought": "T1", "action": "user_history", "reasoning": "R1"},
            {"thought": "T2", "action": "previous_alerts", "reasoning": "R2"},
            {"thought": "T3", "action": "ip_reputation", "reasoning": "R3"},
            {"thought": "T4", "action": "finish", "reasoning": "R4"}
        ])
        
        alert = {"alert_type": "brute_force", "severity": "medium", "status": "open"}
        with patch("app.investigation.autonomous_agent.get_user_history", return_value={"events": []}), \
             patch("app.investigation.autonomous_agent.get_previous_alerts", return_value={"alerts": []}), \
             patch("app.investigation.autonomous_agent.get_ip_reputation", return_value={"risk": 50}):
            
            evidence, summary, tools_used, trace, _ = agent.run(alert, _make_event(), "", [])
            
        assert tools_used == ["user_history", "previous_alerts", "ip_reputation"]
        assert len(tools_used) == 3

    def test_invalid_llm_response(self):
        # We test that invalid JSON in LLM client triggers fallback
        from app.investigation.nodes.evidence_collection import collect_evidence
        
        state = {
            "security_event": _make_event(),
            "alert": _make_alert(),
            "investigation_summary": "",
            "reasoning_trace": []
        }
        config = {"configurable": {"db": MagicMock()}}
        
        with patch("app.llm.client.settings") as mock_settings, \
             patch("app.llm.client.LLMClient._call_openai") as mock_call, \
             patch("app.investigation.nodes.evidence_collection.get_user_history"):
            mock_settings.OPENAI_API_KEY = "sk-key"
            
            # Mock invalid JSON
            mock_call.return_value = "Not a JSON"
            
            # This should not crash, it should fallback
            result = collect_evidence(state, config)
            assert "Autonomous agent failed" in result["reasoning_trace"][0]

    def test_openai_failure_test_no_key(self):
        # Test 5: Disable OPENAI_API_KEY
        from app.investigation.nodes.evidence_collection import collect_evidence
        state = {
            "security_event": _make_event(),
            "alert": _make_alert(),
            "investigation_summary": "",
            "reasoning_trace": []
        }
        config = {"configurable": {"db": MagicMock()}}
        
        with patch("app.llm.client.settings") as mock_settings, \
             patch("app.investigation.nodes.evidence_collection.get_user_history"):
            mock_settings.OPENAI_API_KEY = None
            
            # Should not crash, should fallback
            result = collect_evidence(state, config)
            assert "Autonomous agent failed" in result["reasoning_trace"][0]

    def test_agent_raises_exception_on_llm_failure(self):
        client = LLMClient()
        db = MagicMock()
        agent = AutonomousInvestigationAgent(client=client, db=db)
        
        client.execute_autonomous_step = MagicMock(side_effect=Exception("API Timeout"))
        
        with pytest.raises(Exception, match="API Timeout"):
            agent.run(_make_alert(), _make_event(), "", [])

