import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User, Conversation, Message
from app.core.security import get_current_or_guest_user
from app.schemas.conversation import (
    ConversationSummary, ConversationDetail, ConversationUpdate, MessageItem
)

logger = logging.getLogger("sakhi_ai.api.conversations")

router = APIRouter()

@router.get("", response_model=List[ConversationSummary])
async def list_conversations(
    current_user: User = Depends(get_current_or_guest_user),
    db: Session = Depends(get_db)
):
    """
    Returns list of conversations owned by the current user.
    """
    conversations = db.query(Conversation).filter_by(
        user_id=current_user.id
    ).order_by(Conversation.updated_at.desc()).all()

    result = []
    for c in conversations:
        msgs = c.messages
        count = len(msgs)
        last_msg = msgs[-1].content[:60] + "..." if (count > 0 and len(msgs[-1].content) > 60) else (msgs[-1].content if count > 0 else None)
        result.append(ConversationSummary(
            id=c.id,
            user_id=c.user_id,
            title=c.title,
            created_at=c.created_at.isoformat() if c.created_at else "",
            updated_at=c.updated_at.isoformat() if c.updated_at else "",
            message_count=count,
            last_message=last_msg
        ))
    return result

@router.get("/{conversation_id}", response_model=ConversationDetail)
async def get_conversation_detail(
    conversation_id: str,
    current_user: User = Depends(get_current_or_guest_user),
    db: Session = Depends(get_db)
):
    """
    Returns conversation and all its messages.
    Strictly verifies ownership: User A cannot read User B's conversation!
    """
    conversation = db.query(Conversation).filter_by(id=conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    if conversation.user_id != current_user.id:
        # Strict user isolation
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view this conversation."
        )

    messages = [
        MessageItem(
            id=m.id,
            conversation_id=m.conversation_id,
            sender=m.sender,
            content=m.content,
            input_type=m.input_type,
            created_at=m.created_at.isoformat() if m.created_at else ""
        )
        for m in conversation.messages
    ]

    return ConversationDetail(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at.isoformat() if conversation.created_at else "",
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
        messages=messages
    )

@router.put("/{conversation_id}", response_model=ConversationSummary)
async def rename_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    current_user: User = Depends(get_current_or_guest_user),
    db: Session = Depends(get_db)
):
    conversation = db.query(Conversation).filter_by(id=conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    conversation.title = payload.title.strip()
    db.commit()
    db.refresh(conversation)

    return ConversationSummary(
        id=conversation.id,
        user_id=conversation.user_id,
        title=conversation.title,
        created_at=conversation.created_at.isoformat() if conversation.created_at else "",
        updated_at=conversation.updated_at.isoformat() if conversation.updated_at else "",
        message_count=len(conversation.messages)
    )

@router.delete("/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_or_guest_user),
    db: Session = Depends(get_db)
):
    """
    Deletes conversation from MySQL, cascading to its messages.
    """
    conversation = db.query(Conversation).filter_by(id=conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")

    if conversation.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    db.delete(conversation)
    db.commit()
    return {"success": True, "message": "Conversation deleted successfully."}
