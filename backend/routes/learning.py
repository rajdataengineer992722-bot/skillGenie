from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field
import json

try:
    from backend.dependencies import get_current_user
    from backend.services.ai_service import generate_learning_plan
    from backend.services.tracking_service import create_learning_plan, list_learning_plans
except ModuleNotFoundError:
    from dependencies import get_current_user
    from services.ai_service import generate_learning_plan
    from services.tracking_service import create_learning_plan, list_learning_plans

router = APIRouter()


class LearningPlanRequest(BaseModel):
    role: str = Field(..., min_length=2)
    goal: str = Field(..., min_length=2)
    knowledge_level: str = Field(default="beginner", pattern="^(beginner|intermediate|advanced)$")
    department: str = Field(default="", max_length=120)
    business_context: str = Field(default="", max_length=400)
    past_learning: str = Field(default="", max_length=400)


@router.post("/plan")
def create_plan(data: LearningPlanRequest, current_user: dict = Depends(get_current_user)):
    generated = generate_learning_plan(
        data.role,
        data.goal,
        data.knowledge_level,
        department=data.department,
        business_context=data.business_context,
        past_learning=data.past_learning,
    )
    plan_text = generated["plan_text"]
    structured_plan = generated["structured_plan"]
    plan = create_learning_plan(
        current_user["id"],
        data.role,
        data.goal,
        plan_text,
        data.knowledge_level,
        plan_json=json.dumps(structured_plan),
    )
    return {"plan": plan_text, "structured_plan": structured_plan, "plan_record": plan}


@router.post("/learning-path")
def learning_path(data: LearningPlanRequest, current_user: dict = Depends(get_current_user)):
    generated = generate_learning_plan(
        data.role,
        data.goal,
        data.knowledge_level,
        department=data.department,
        business_context=data.business_context,
        past_learning=data.past_learning,
    )
    result = generated["plan_text"]
    structured_plan = generated["structured_plan"]
    plan = create_learning_plan(
        current_user["id"],
        data.role,
        data.goal,
        result,
        data.knowledge_level,
        plan_json=json.dumps(structured_plan),
    )

    return {"plan": result, "structured_plan": structured_plan, "plan_record": plan}


@router.get("/learning-path")
def list_paths(current_user: dict = Depends(get_current_user)):
    return {"plans": list_learning_plans(current_user["id"])}
