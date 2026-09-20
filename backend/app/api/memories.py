import uuid
import logging
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User, Memory
from app.core.security import get_current_or_guest_user
from app.schemas.memory import MemoryCreate, MemoryItem

logger = logging.getLogger("sakhi_ai.api.memories")

router = APIRouter()

@router.get("", response_model=List[MemoryItem])
async def list_memories(
    current_user: User = Depends(get_current_or_guest_user),
    db: Session = Depends(get_db)
):
    """
    Returns all memories for the authenticated user.
    """
    memories = db.query(Memory).filter_by(
        user_id=current_user.id
    ).order_by(Memory.created_at.desc()).all()

    return [
        MemoryItem(
            id=m.id,
            user_id=m.user_id,
            memory_text=m.memory_text,
            category=m.category,
            created_at=m.created_at.isoformat() if m.created_at else "",
            updated_at=m.updated_at.isoformat() if m.updated_at else None
        )
        for m in memories
    ]

@router.post("", response_model=MemoryItem)
async def create_memory(
    payload: MemoryCreate,
    current_user: User = Depends(get_current_or_guest_user),
    db: Session = Depends(get_db)
):
    memory = Memory(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        memory_text=payload.memory_text.strip(),
        category=payload.category
    )
    db.add(memory)
    db.commit()
    db.refresh(memory)

    return MemoryItem(
        id=memory.id,
        user_id=memory.user_id,
        memory_text=memory.memory_text,
        category=memory.category,
        created_at=memory.created_at.isoformat() if memory.created_at else "",
        updated_at=memory.updated_at.isoformat() if memory.updated_at else None
    )

@router.delete("/{memory_id}")
async def delete_single_memory(
    memory_id: str,
    current_user: User = Depends(get_current_or_guest_user),
    db: Session = Depends(get_db)
):
    """
    Deletes an individual memory. Strict ownership verification!
    """
    memory = db.query(Memory).filter_by(id=memory_id).first()
    if not memory:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Memory not found.")

    if memory.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied.")

    db.delete(memory)
    db.commit()
    return {"success": True, "message": "Memory forgotten successfully."}

@router.delete("")
async def clear_all_memories(
    current_user: User = Depends(get_current_or_guest_user),
    db: Session = Depends(get_db)
):
    """
    Clears all memories for the current user.
    """
    db.query(Memory).filter_by(user_id=current_user.id).delete()
    db.commit()
    return {"success": True, "message": "All memories cleared successfully."}
