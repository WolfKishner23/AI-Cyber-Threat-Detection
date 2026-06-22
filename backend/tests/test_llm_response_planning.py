from unittest.mock import patch, MagicMock
import pytest
import sys
from app.investigation.nodes.response_planning import plan_response
from app.llm.client import LLMClient

@pytest.fixture
def base_state():
    return {
        "alert": {"alert_type": "impossible_travel", "severity": "high"},
        "evidence": {"previous_alerts": {"alert_count": 1}},
        "risk_score": 85,
        "confidence_score": 90,
        "investigation_summary": "Initial summary.",
        "reasoning_trace": ["Step 1", "Step 2"]
    }

def test_response_planning_success(base_state):
    """Verify that a successful LLM call uses the LLM's recommended action."""
    mock_llm_result = {
        "recommended_action": "force_password_reset",
        "reasoning": "High risk score with impossible travel warrants a password reset."
    }
    
    with patch("app.investigation.nodes.response_planning._client.plan_response", return_value=mock_llm_result):
        new_state = plan_response(base_state)
        
        assert new_state["recommended_action"] == "force_password_reset"
        assert "LLM Response Planning Agent: Recommended action 'force_password_reset'." in new_state["reasoning_trace"][-1]
        assert "High risk score with impossible travel warrants a password reset." in new_state["investigation_summary"]

def test_response_planning_fallback_due_to_none(base_state):
    """Verify that returning None from LLMClient triggers heuristic fallback."""
    base_state["risk_score"] = 95
    
    with patch("app.investigation.nodes.response_planning._client.plan_response", return_value=None):
        new_state = plan_response(base_state)
        
        assert new_state["recommended_action"] == "lock_account"
        assert "Response Planning Agent [Heuristic Fallback]: Recommended action 'lock_account'" in new_state["reasoning_trace"][-1]

@patch("app.llm.client.settings")
def test_llmclient_plan_response_missing_api_key(mock_settings):
    """Verify LLMClient returns None if API key is missing."""
    mock_settings.OPENAI_API_KEY = None
    client = LLMClient()
    
    result = client.plan_response({}, "", {}, 50, 50)
    assert result is None

@patch("app.llm.client.settings")
def test_llmclient_plan_response_malformed_json(mock_settings):
    """Verify LLMClient returns None and handles invalid JSON."""
    mock_settings.OPENAI_API_KEY = "test-key"
    mock_settings.OPENAI_MODEL = "gpt-4o-mini"
    client = LLMClient()
    
    # Mock openai.OpenAI
    mock_openai_module = MagicMock()
    mock_openai_class = MagicMock()
    mock_completions = MagicMock()
    mock_completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content="This is not valid JSON"))
    ]
    mock_openai_class.return_value.chat.completions = mock_completions
    mock_openai_module.OpenAI = mock_openai_class
    
    sys.modules["openai"] = mock_openai_module
    try:
        result = client.plan_response({}, "", {}, 50, 50)
        assert result is None
    finally:
        del sys.modules["openai"]

@patch("app.llm.client.settings")
def test_llmclient_plan_response_valid_json(mock_settings):
    """Verify LLMClient parses valid JSON correctly."""
    mock_settings.OPENAI_API_KEY = "test-key"
    mock_settings.OPENAI_MODEL = "gpt-4o-mini"
    client = LLMClient()
    
    valid_json = '{"recommended_action": "notify_user", "reasoning": "User should be aware."}'
    
    mock_openai_module = MagicMock()
    mock_openai_class = MagicMock()
    mock_completions = MagicMock()
    mock_completions.create.return_value.choices = [
        MagicMock(message=MagicMock(content=valid_json))
    ]
    mock_openai_class.return_value.chat.completions = mock_completions
    mock_openai_module.OpenAI = mock_openai_class
    
    sys.modules["openai"] = mock_openai_module
    try:
        result = client.plan_response({}, "", {}, 50, 50)
        assert result is not None
        assert result["recommended_action"] == "notify_user"
        assert result["reasoning"] == "User should be aware."
    finally:
        del sys.modules["openai"]

@patch("app.llm.client.settings")
def test_llmclient_plan_response_api_failure(mock_settings):
    """Verify LLMClient returns None when the API call raises an exception."""
    mock_settings.OPENAI_API_KEY = "test-key"
    mock_settings.OPENAI_MODEL = "gpt-4o-mini"
    client = LLMClient()
    
    def raise_exception(*args, **kwargs):
        raise Exception("API failure")
        
    mock_openai_module = MagicMock()
    mock_openai_class = MagicMock()
    mock_completions = MagicMock()
    mock_completions.create.side_effect = raise_exception
    mock_openai_class.return_value.chat.completions = mock_completions
    mock_openai_module.OpenAI = mock_openai_class
    
    sys.modules["openai"] = mock_openai_module
    try:
        result = client.plan_response({}, "", {}, 50, 50)
        assert result is None
    finally:
        del sys.modules["openai"]
