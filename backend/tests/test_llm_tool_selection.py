"""
tests/test_llm_tool_selection.py

Phase 6B tests:
- Correct tool selection from LLM
- Correct tool execution in Evidence Collection Node
- Fallback when API key is missing
- Fallback on invalid JSON
- Fallback on API failure
- Verify evidence population only for selected tools
"""
import json
import pytest
from unittest.mock import MagicMock, patch

from app.llm.client import LLMClient
from app.llm.tool_selection_prompt import build_tool_selection_prompt
from app.llm.tool_registry import get_available_tools

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_alert(alert_type="impossible_travel", severity="high"):
    return {"alert_type": alert_type, "severity": severity, "status": "open"}

def _make_investigation_summary():
    return "Initial alert detected from IP 203.0.113.45."

# ---------------------------------------------------------------------------
# 1. Prompt Builder
# ---------------------------------------------------------------------------

class TestToolSelectionPromptBuilder:
    def test_prompt_contains_alert_info(self):
        p = build_tool_selection_prompt(_make_alert("impossible_travel"), _make_investigation_summary())
        assert "impossible_travel" in p
        assert "203.0.113.45" in p

    def test_prompt_contains_all_tools(self):
        p = build_tool_selection_prompt(_make_alert(), "")
        for tool in get_available_tools():
            assert tool in p

# ---------------------------------------------------------------------------
# 2. LLMClient select_tools logic
# ---------------------------------------------------------------------------

class TestLLMClientToolSelection:
    def _make_openai_response(self, tools_list):
        payload = json.dumps({"required_tools": tools_list})
        mock_choice = MagicMock()
        mock_choice.message.content = payload
        mock_response = MagicMock()
        mock_response.choices = [mock_choice]
        return mock_response

    def test_select_tools_success(self):
        with patch("app.llm.client.settings") as mock_settings, \
             patch("app.llm.client.LLMClient._call_openai_tool_selection") as mock_call:
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.OPENAI_MODEL = "gpt-4o-mini"
            
            mock_call.return_value = {"required_tools": ["location_history", "ip_reputation"]}
                
            client = LLMClient()
            result = client.select_tools(_make_alert(), _make_investigation_summary())
            
        assert "location_history" in result["required_tools"]
        assert "ip_reputation" in result["required_tools"]
        assert "user_history" not in result["required_tools"]

    def test_select_tools_filters_invalid_tools(self):
        """Should only return tools that exist in the registry."""
        with patch("app.llm.client.settings") as mock_settings, \
             patch("app.llm.client.LLMClient._call_openai_tool_selection") as mock_call:
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            mock_settings.OPENAI_MODEL = "gpt-4o-mini"
            
            mock_call.return_value = {"required_tools": ["location_history", "non_existent_tool"]}
                
            client = LLMClient()
            result = client.select_tools(_make_alert(), "")
            
        assert "location_history" in result["required_tools"]
        assert "non_existent_tool" not in result["required_tools"]

    def test_fallback_when_no_api_key(self):
        with patch("app.llm.client.settings") as mock_settings:
            mock_settings.OPENAI_API_KEY = None
            client = LLMClient()
            result = client.select_tools(_make_alert(), "")
            
        # Should return all tools
        assert set(result["required_tools"]) == set(get_available_tools())

    def test_fallback_on_api_error(self):
        with patch("app.llm.client.settings") as mock_settings, \
             patch("app.llm.client.LLMClient._call_openai_tool_selection", side_effect=Exception("API Error")):
            mock_settings.OPENAI_API_KEY = "sk-test-key"
            client = LLMClient()
            result = client.select_tools(_make_alert(), "")
            
        assert set(result["required_tools"]) == set(get_available_tools())

# ---------------------------------------------------------------------------
# 3. Evidence Collection Node Integration
# ---------------------------------------------------------------------------

class TestEvidenceCollectionNode:
    
    @patch("app.investigation.nodes.evidence_collection.AutonomousInvestigationAgent.run", side_effect=Exception("Trigger fallback"))
    @patch("app.investigation.nodes.evidence_collection._client")
    @patch("app.investigation.nodes.evidence_collection.get_user_history", return_value={"event_count": 5})
    @patch("app.investigation.nodes.evidence_collection.get_ip_reputation", return_value={"risk_score": 80})
    @patch("app.investigation.nodes.evidence_collection.get_location_history", return_value={"locations": ["London"]})
    @patch("app.investigation.nodes.evidence_collection.get_device_history", return_value={"devices": ["PC"]})
    @patch("app.investigation.nodes.evidence_collection.get_previous_alerts", return_value={"alert_count": 2})
    @patch("app.investigation.nodes.evidence_collection.get_incident_history", return_value={})
    def test_selective_tool_execution(self, mock_inc, mock_prev, mock_dev, mock_loc, mock_ip, mock_user, mock_client, mock_agent_run):
        from app.investigation.nodes.evidence_collection import collect_evidence
        
        # Setup mock client to only return 2 tools
        mock_client.select_tools.return_value = {"required_tools": ["location_history", "ip_reputation"]}
        
        state = {
            "security_event": {"user_id": "usr_1", "ip_address": "1.1.1.1"},
            "alert": _make_alert(),
            "investigation_summary": "",
            "reasoning_trace": []
        }
        config = {"configurable": {"db": MagicMock()}}
        
        result = collect_evidence(state, config)
        
        # Verify only selected tools were executed
        mock_loc.assert_called_once()
        mock_ip.assert_called_once()
        
        mock_user.assert_not_called()
        mock_dev.assert_not_called()
        mock_prev.assert_not_called()
        
        # Verify evidence object only contains populated data for selected tools
        evidence = result["evidence"]
        assert "London" in evidence["location_history"].get("locations", [])
        assert evidence["ip_reputation"].get("risk_score") == 80
        assert "user_history" not in evidence
        
        # Verify trace logging
        trace = result["reasoning_trace"]
        assert any("LLM selected tools [location_history, ip_reputation]" in t for t in trace)

    @patch("app.investigation.nodes.evidence_collection.AutonomousInvestigationAgent.run", side_effect=Exception("Trigger fallback"))
    @patch("app.investigation.nodes.evidence_collection._client")
    @patch("app.investigation.nodes.evidence_collection.get_user_history", return_value={"event_count": 5})
    @patch("app.investigation.nodes.evidence_collection.get_location_history", return_value={"locations": ["London"]})
    def test_fallback_execution_trace(self, mock_loc, mock_user, mock_client, mock_agent_run):
        from app.investigation.nodes.evidence_collection import collect_evidence
        
        # Setup mock client to return ALL tools (fallback behavior)
        mock_client.select_tools.return_value = {"required_tools": get_available_tools()}
        
        state = {
            "security_event": {"user_id": "usr_1", "ip_address": "1.1.1.1"},
            "alert": _make_alert(),
            "investigation_summary": "",
            "reasoning_trace": []
        }
        config = {"configurable": {"db": MagicMock()}}
        
        # Use MagicMock for missing patch arguments so they don't error out, but we mock enough to test the trace
        with patch("app.investigation.nodes.evidence_collection.get_device_history"), \
             patch("app.investigation.nodes.evidence_collection.get_previous_alerts"), \
             patch("app.investigation.nodes.evidence_collection.get_incident_history"), \
             patch("app.investigation.nodes.evidence_collection.get_ip_reputation"):
            result = collect_evidence(state, config)
        
        trace = result["reasoning_trace"]
        assert any("Fallback mode activated, executing all tools" in t for t in trace)
