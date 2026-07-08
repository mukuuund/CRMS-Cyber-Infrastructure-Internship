from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from app.ml.predictor import Predictor

router = APIRouter(prefix="/api/predict", tags=["ML Predictions"])

class PriorityPredictionRequest(BaseModel):
    title: str
    description: Optional[str] = None
    issue_type: Optional[str] = None

@router.post("/priority")
def predict_priority(request: PriorityPredictionRequest):
    try:
        predictor = Predictor.get_instance()
        result = predictor.predict(
            title=request.title,
            description=request.description or "",
            issue_type=request.issue_type or ""
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {str(e)}")

from app.core.effort_rules import calculate_effort_rule

class EffortRuleRequest(BaseModel):
    priority: Optional[str] = None
    complexity: Optional[str] = None
    business_value: Optional[str] = None

@router.post("/effort-rule")
def predict_effort_rule(request: EffortRuleRequest):
    return calculate_effort_rule(
        priority=request.priority,
        complexity=request.complexity,
        business_value=request.business_value
    )

