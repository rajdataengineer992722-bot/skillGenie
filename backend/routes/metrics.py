from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

try:
    from backend.dependencies import get_current_user
    from backend.services.tracking_service import (
        get_dashboard_metrics,
        get_learning_plan,
        list_learning_plans,
        list_recent_progress_events,
        list_recent_chat_messages,
        update_learning_plan_progress,
    )
except ModuleNotFoundError:
    from dependencies import get_current_user
    from services.tracking_service import (
        get_dashboard_metrics,
        get_learning_plan,
        list_learning_plans,
        list_recent_progress_events,
        list_recent_chat_messages,
        update_learning_plan_progress,
    )


router = APIRouter(tags=["metrics"])


class ProgressUpdateRequest(BaseModel):
    completed_steps: int = Field(..., ge=0)
    hours_spent: int = Field(..., ge=0)


@router.get("/dashboard")
def dashboard(current_user: dict = Depends(get_current_user)):
    return {
        "metrics": get_dashboard_metrics(current_user["id"]),
        "plans": list_learning_plans(current_user["id"]),
        "messages": list_recent_chat_messages(current_user["id"]),
        "activity": list_recent_progress_events(current_user["id"]),
    }


@router.patch("/progress/{plan_id}")
def update_progress(plan_id: int, data: ProgressUpdateRequest, current_user: dict = Depends(get_current_user)):
    plan = update_learning_plan_progress(
        current_user["id"],
        plan_id,
        data.completed_steps,
        data.hours_spent,
    )
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning plan not found")
    return {"plan": plan}


@router.get("/learning-path/{plan_id}")
def get_plan(plan_id: int, current_user: dict = Depends(get_current_user)):
    plan = get_learning_plan(plan_id, current_user["id"])
    if not plan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Learning plan not found")
    return {"plan": plan}
