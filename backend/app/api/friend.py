import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User, FriendProfile, Setting
from app.core.security import get_current_user
from app.voice.tts import get_voice_for_gender, migrate_voice_id
from app.schemas.friend import (
    FriendProfileUpdate, FriendProfileResponse, SettingUpdate, SettingResponse
)

router = APIRouter()

@router.get("/profile", response_model=FriendProfileResponse)
async def get_friend_profile(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(FriendProfile).filter_by(user_id=current_user.id).first()
    if not profile:
        profile = FriendProfile(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            friend_name="Sakhi",
            gender="female",
            voice_id="female_voice",
            personality="friendly"
        )
        db.add(profile)
        db.commit()
        db.refresh(profile)
    else:
        # Migrate legacy voice ID if needed and enforce consistency
        target_voice = migrate_voice_id(profile.voice_id, profile.gender)
        if profile.voice_id != target_voice:
            profile.voice_id = target_voice
            db.commit()
            db.refresh(profile)

    return FriendProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        friend_name=profile.friend_name,
        gender=profile.gender,
        voice_id=profile.voice_id,
        personality=profile.personality
    )

@router.put("/profile", response_model=FriendProfileResponse)
async def update_friend_profile(
    payload: FriendProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    profile = db.query(FriendProfile).filter_by(user_id=current_user.id).first()
    if not profile:
        profile = FriendProfile(
            id=str(uuid.uuid4()),
            user_id=current_user.id,
            friend_name="Sakhi",
            gender="female",
            voice_id="female_voice",
            personality="friendly"
        )
        db.add(profile)

    if payload.friend_name is not None:
        profile.friend_name = payload.friend_name.strip()
    if payload.gender is not None:
        profile.gender = payload.gender

    # Enforce companion gender as the SINGLE SOURCE OF TRUTH
    profile.voice_id = get_voice_for_gender(profile.gender)

    if payload.personality is not None:
        profile.personality = payload.personality

    db.commit()
    db.refresh(profile)

    return FriendProfileResponse(
        id=profile.id,
        user_id=profile.user_id,
        friend_name=profile.friend_name,
        gender=profile.gender,
        voice_id=profile.voice_id,
        personality=profile.personality
    )

@router.get("/settings", response_model=SettingResponse)
async def get_user_settings(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    setting = db.query(Setting).filter_by(user_id=current_user.id).first()
    if not setting:
        setting = Setting(id=str(uuid.uuid4()), user_id=current_user.id)
        db.add(setting)
        db.commit()
        db.refresh(setting)

    return SettingResponse(
        id=setting.id,
        user_id=setting.user_id,
        default_mode=setting.default_mode,
        voice_enabled=setting.voice_enabled,
        always_speak=setting.always_speak,
        language_preference=setting.language_preference
    )

@router.put("/settings", response_model=SettingResponse)
async def update_user_settings(
    payload: SettingUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    setting = db.query(Setting).filter_by(user_id=current_user.id).first()
    if not setting:
        setting = Setting(id=str(uuid.uuid4()), user_id=current_user.id)
        db.add(setting)

    if payload.default_mode is not None:
        setting.default_mode = payload.default_mode
    if payload.voice_enabled is not None:
        setting.voice_enabled = payload.voice_enabled
    if payload.always_speak is not None:
        setting.always_speak = payload.always_speak
    if payload.language_preference is not None:
        setting.language_preference = payload.language_preference

    db.commit()
    db.refresh(setting)

    return SettingResponse(
        id=setting.id,
        user_id=setting.user_id,
        default_mode=setting.default_mode,
        voice_enabled=setting.voice_enabled,
        always_speak=setting.always_speak,
        language_preference=setting.language_preference
    )
