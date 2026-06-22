from pydantic import BaseModel, Field


class RiskAssessmentResult(BaseModel):
    """Structured output from the risk assessment service."""

    risk_score: int = Field(..., ge=0, le=100)
    confidence_score: int = Field(..., ge=0, le=100)
    risk_level: str  # low | medium | high | critical
    recommended_action: str
    reasoning: str

    @staticmethod
    def derive_risk_level(score: int) -> str:
        if score >= 85:
            return "critical"
        elif score >= 65:
            return "high"
        elif score >= 35:
            return "medium"
        else:
            return "low"
