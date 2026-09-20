import logging
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User
from app.core.security import get_current_user
from app.schemas.user import UserUpdate, UserResponse

logger = logging.getLogger("sakhi_ai.api.users")

router = APIRouter()

@router.get("/me", response_model=UserResponse)
async def get_my_profile(current_user: User = Depends(get_current_user)):
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        auth_provider=current_user.auth_provider,
        created_at=current_user.created_at.isoformat() if current_user.created_at else "",
        onboarding_completed=True if (current_user.friend_profile and current_user.friend_profile.friend_name != "Sakhi") else False
    )

@router.put("/me", response_model=UserResponse)
async def update_my_profile(
    payload: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if payload.name is not None:
        current_user.name = payload.name.strip()
    if payload.phone is not None:
        current_user.phone = payload.phone.strip()
    if payload.email is not None and payload.email != current_user.email:
        existing = db.query(User).filter(User.email == payload.email, User.id != current_user.id).first()
        if existing:
            raise HTTPException(status_code=400, detail="Email already registered by another user.")
        current_user.email = payload.email

    db.commit()
    db.refresh(current_user)
    return UserResponse(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email,
        phone=current_user.phone,
        auth_provider=current_user.auth_provider,
        created_at=current_user.created_at.isoformat() if current_user.created_at else ""
    )

@router.delete("/me")
async def delete_my_account(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Deletes the current user's account and cascades to all conversations,
    memories, messages, friend profiles, and refresh tokens.
    """
    db.delete(current_user)
    db.commit()
    return {"success": True, "message": "Account and all associated data deleted permanently."}
