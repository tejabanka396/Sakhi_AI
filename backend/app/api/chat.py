import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User
from app.core.security import get_current_or_guest_user
from app.schemas.chat import ChatRequest, ChatResponse
from app.ai.service import chat_service

logger = logging.getLogger("sakhi_ai.api.chat")

router = APIRouter()

@router.post("", response_model=ChatResponse)
async def send_chat_message(
    payload: ChatRequest,
    current_user: User = Depends(get_current_or_guest_user),
    db: Session = Depends(get_db)
):
    """
    Process incoming chat message from user (Voice transcript or typed text).
    Returns AI response, conversation ID, and generated title.
    """
    try:
        result = await chat_service.process_chat(
            db=db,
            user=current_user,
            message_text=payload.message,
            conversation_id=payload.conversation_id,
            input_type=payload.input_type
        )
        return ChatResponse(
            reply=result["reply"],
            display_text=result.get("display_text", result["reply"]),
            speech_text=result.get("speech_text"),
            conversation_id=result["conversation_id"],
            message_id=result["message_id"],
            response_id=result.get("response_id", result["message_id"]),
            voice_id=result.get("voice_id"),
            gender=result.get("gender"),
            title=result.get("title"),
            sender="assistant",
            language=result.get("language", "auto")
        )
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Sakhi couldn't process your message right now. Please try again."
        )
