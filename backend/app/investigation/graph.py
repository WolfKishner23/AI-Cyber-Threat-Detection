from langgraph.graph import StateGraph, START, END
from app.investigation.state import InvestigationState
from app.investigation.nodes.investigation import investigate_alert
from app.investigation.nodes.evidence_collection import collect_evidence
from app.investigation.nodes.risk_assessment import assess_risk
from app.investigation.nodes.response_planning import plan_response

# Initialize the state graph
workflow = StateGraph(InvestigationState)

# Add nodes
workflow.add_node("investigation", investigate_alert)
workflow.add_node("evidence_collection", collect_evidence)
workflow.add_node("risk_assessment", assess_risk)
workflow.add_node("response_planning", plan_response)

# Define edges
workflow.add_edge(START, "investigation")
workflow.add_edge("investigation", "evidence_collection")
workflow.add_edge("evidence_collection", "risk_assessment")
workflow.add_edge("risk_assessment", "response_planning")
workflow.add_edge("response_planning", END)

# Compile graph
investigation_graph = workflow.compile()
