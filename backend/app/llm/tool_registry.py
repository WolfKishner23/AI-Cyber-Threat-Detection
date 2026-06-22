"""
Phase 6B Tool Registry.
Registers all available tools that the LLM can select from.
"""

AVAILABLE_TOOLS = [
    "user_history",
    "device_history",
    "location_history",
    "previous_alerts",
    "incident_history",
    "ip_reputation"
]

def get_available_tools():
    """Return the list of tools available for the LLM to select."""
    return AVAILABLE_TOOLS
