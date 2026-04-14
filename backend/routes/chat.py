from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

try:
    from backend.dependencies import get_current_user
    from backend.services.ai_service import chat_response
    from backend.services.tracking_service import (
        get_latest_learning_plan,
        list_recent_chat_messages,
        save_chat_message,
    )
except ModuleNotFoundError:
    from dependencies import get_current_user
    from services.ai_service import chat_response
    from services.tracking_service import (
        get_latest_learning_plan,
        list_recent_chat_messages,
        save_chat_message,
    )

router = APIRouter()


class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1)


@router.post("/chat")
def chat(data: ChatRequest, current_user: dict = Depends(get_current_user)):
    latest_plan = get_latest_learning_plan(current_user["id"])
    recent_messages = list_recent_chat_messages(current_user["id"], limit=4)
    response = chat_response(
        data.message,
        role=latest_plan["role"] if latest_plan else "",
        goal=latest_plan["goal"] if latest_plan else "",
        latest_plan_text=latest_plan["plan_text"] if latest_plan else "",
        recent_messages=recent_messages,
    )
    message = save_chat_message(current_user["id"], data.message, response)
    return {"response": response, "message": message}


@router.get("/chat/history")
def chat_history(current_user: dict = Depends(get_current_user)):
    return {"messages": list_recent_chat_messages(current_user["id"])}
