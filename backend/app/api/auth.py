from typing import Optional
import uuid
import random
import secrets
import re
import hashlib
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.orm import Session
from app.database.database import get_db
from app.database.models import User, FriendProfile, Setting, RefreshToken, OTPVerification
from app.core.config import settings
from app.core.security import (
    verify_password, get_password_hash, create_access_token, create_refresh_token,
    decode_token, hash_token, get_current_user
)
from app.schemas.auth import (
    RegisterRequest, LoginRequest, GoogleAuthRequest, PhoneOTPRequest,
    PhoneVerifyRequest, RefreshTokenRequest, TokenResponse
)
from app.services.sms.service import sms_service
from app.core.phone import parse_and_validate_indian_phone
from app.voice.tts import migrate_voice_id

router = APIRouter()

def build_user_response_payload(user: User, db: Session, access_token: str, refresh_token: str) -> dict:
    friend = db.query(FriendProfile).filter_by(user_id=user.id).first()
    settings_obj = db.query(Setting).filter_by(user_id=user.id).first()

    # Determine if onboarding is completed (if friend_name has been chosen or settings modified)
    onboarding_completed = False
    if friend and (friend.friend_name != "Sakhi" or friend.voice_id not in ["female_voice", "female_friendly"]):
        onboarding_completed = True
    elif user.conversations and len(user.conversations) > 0:
        onboarding_completed = True

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "onboarding_completed": onboarding_completed,
        "user": {
            "id": user.id,
            "name": user.name,
            "email": user.email,
            "phone": user.phone,
            "auth_provider": user.auth_provider,
            "created_at": user.created_at.isoformat() if user.created_at else "",
            "onboarding_completed": onboarding_completed
        },
        "friend_profile": {
            "id": friend.id,
            "user_id": friend.user_id,
            "friend_name": friend.friend_name,
            "gender": friend.gender,
            "voice_id": migrate_voice_id(friend.voice_id, friend.gender),
            "personality": friend.personality
        } if friend else None,
        "settings": {
            "id": settings_obj.id,
            "user_id": settings_obj.user_id,
            "default_mode": settings_obj.default_mode,
            "voice_enabled": settings_obj.voice_enabled,
            "always_speak": settings_obj.always_speak,
            "language_preference": settings_obj.language_preference
        } if settings_obj else None
    }

@router.post("/register", response_model=TokenResponse)
async def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    # Check duplicate email
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An account with this email already exists."
        )

    user_id = str(uuid.uuid4())
    new_user = User(
        id=user_id,
        name=payload.name.strip(),
        email=payload.email.lower().strip(),
        phone=payload.phone.strip() if payload.phone else None,
        password_hash=get_password_hash(payload.password),
        auth_provider="email"
    )
    db.add(new_user)

    # Initialize friend profile
    friend = FriendProfile(
        id=str(uuid.uuid4()),
        user_id=user_id,
        friend_name="Sakhi",
        gender="female",
        voice_id="female_voice",
        personality="friendly"
    )
    db.add(friend)

    # Initialize settings
    setting = Setting(
        id=str(uuid.uuid4()),
        user_id=user_id,
        default_mode="talk",
        voice_enabled=True,
        always_speak=False,
        language_preference="auto"
    )
    db.add(setting)

    db.commit()
    db.refresh(new_user)

    access_token = create_access_token({"sub": user_id, "name": new_user.name})
    refresh_token = create_refresh_token({"sub": user_id})

    # Store refresh token
    db_refresh = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user_id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(db_refresh)
    db.commit()

    return build_user_response_payload(new_user, db, access_token, refresh_token)

@router.post("/login", response_model=TokenResponse)
async def login(payload: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == payload.email.lower().strip()).first()
    if not user or not user.password_hash or not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password."
        )

    access_token = create_access_token({"sub": user.id, "name": user.name})
    refresh_token = create_refresh_token({"sub": user.id})

    db_refresh = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(db_refresh)
    db.commit()

    return build_user_response_payload(user, db, access_token, refresh_token)

@router.post("/refresh")
async def refresh_access_token(payload: RefreshTokenRequest, db: Session = Depends(get_db)):
    decoded = decode_token(payload.refresh_token)
    if not decoded or decoded.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token."
        )

    hashed = hash_token(payload.refresh_token)
    db_token = db.query(RefreshToken).filter(
        RefreshToken.token_hash == hashed,
        RefreshToken.revoked_at.is_(None)
    ).first()

    if not db_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Refresh token revoked or not found."
        )

    user = db.query(User).filter(User.id == db_token.user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found.")

    new_access_token = create_access_token({"sub": user.id, "name": user.name})
    return {"access_token": new_access_token, "token_type": "bearer"}

@router.post("/google", response_model=TokenResponse)
async def google_auth(payload: GoogleAuthRequest, db: Session = Depends(get_db)):
    email = (payload.email or "google_user@gmail.com").lower().strip()
    name = payload.name or "Google Friend"

    user = db.query(User).filter(User.email == email).first()
    if not user:
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            name=name,
            email=email,
            auth_provider="google"
        )
        db.add(user)

        friend = FriendProfile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            friend_name="Sakhi",
            gender="female",
            voice_id="female_voice"
        )
        setting = Setting(
            id=str(uuid.uuid4()),
            user_id=user_id
        )
        db.add_all([friend, setting])
        db.commit()
        db.refresh(user)

    access_token = create_access_token({"sub": user.id, "name": user.name})
    refresh_token = create_refresh_token({"sub": user.id})

    db_refresh = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(db_refresh)
    db.commit()

    return build_user_response_payload(user, db, access_token, refresh_token)

@router.post("/phone/request-otp")
async def request_phone_otp(payload: PhoneOTPRequest, db: Session = Depends(get_db)):
    parsed = parse_and_validate_indian_phone(payload.phone)
    if not parsed.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=parsed.error_message or "Please provide a valid 10-digit Indian mobile number."
        )

    normalized_phone = parsed.e164
    now_utc = datetime.now(timezone.utc)

    # Rate-limit OTP requests (cooldown window)
    recent_otp = db.query(OTPVerification).filter(
        OTPVerification.phone == normalized_phone,
        OTPVerification.verified == False
    ).order_by(OTPVerification.created_at.desc()).first()

    if recent_otp and recent_otp.created_at:
        created_at_utc = recent_otp.created_at.replace(tzinfo=timezone.utc) if recent_otp.created_at.tzinfo is None else recent_otp.created_at
        elapsed = (now_utc - created_at_utc).total_seconds()
        if elapsed < settings.OTP_RATE_LIMIT_SECONDS:
            remaining = int(settings.OTP_RATE_LIMIT_SECONDS - elapsed)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Please wait {remaining} seconds before requesting a new OTP."
            )

    # Generate cryptographically secure 6-digit OTP
    raw_otp = f"{secrets.randbelow(900000) + 100000}"
    hashed_otp = hashlib.sha256(raw_otp.encode()).hexdigest()

    # Dispatch real SMS via configured provider (MSG91 / Twilio / Mock)
    sms_success, sms_message = await sms_service.send_otp(normalized_phone, raw_otp)
    if not sms_success:
        if "not configured" in sms_message.lower():
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="SMS service is not configured. Please configure MSG91 credentials."
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_502_BAD_GATEWAY,
                detail=sms_message
            )

    # Invalidate previous unverified OTPs for this phone
    db.query(OTPVerification).filter(
        OTPVerification.phone == normalized_phone,
        OTPVerification.verified == False
    ).delete()

    # Store hashed OTP with configured expiry in MySQL
    otp_record = OTPVerification(
        id=str(uuid.uuid4()),
        phone=normalized_phone,
        otp_hash=hashed_otp,
        expires_at=now_utc + timedelta(minutes=settings.OTP_EXPIRE_MINUTES),
        attempts=0,
        verified=False
    )
    db.add(otp_record)
    db.commit()

    return {
        "success": True,
        "message": f"Verification code sent to {parsed.display}. Valid for {settings.OTP_EXPIRE_MINUTES} minutes."
    }

@router.post("/phone/verify-otp", response_model=TokenResponse)
async def verify_phone_otp(payload: PhoneVerifyRequest, db: Session = Depends(get_db)):
    parsed = parse_and_validate_indian_phone(payload.phone)
    if not parsed.is_valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=parsed.error_message or "Please provide a valid 10-digit Indian mobile number."
        )

    normalized_phone = parsed.e164
    cleaned_otp = payload.otp.strip()
    if not re.match(r'^\d{6}$', cleaned_otp):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please enter a valid 6-digit OTP code."
        )

    hashed_input = hashlib.sha256(cleaned_otp.encode()).hexdigest()

    otp_record = db.query(OTPVerification).filter(
        (OTPVerification.phone == normalized_phone) | (OTPVerification.phone == parsed.core_digits),
        OTPVerification.verified == False
    ).order_by(OTPVerification.created_at.desc()).first()

    if not otp_record:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active OTP found for this phone number. Please request a new code."
        )

    # Check expiration (compare with UTC)
    now_utc = datetime.now(timezone.utc)
    exp = otp_record.expires_at.replace(tzinfo=timezone.utc) if otp_record.expires_at.tzinfo is None else otp_record.expires_at
    if now_utc > exp:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="OTP has expired. Please request a new code."
        )

    if otp_record.attempts >= 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many invalid attempts. Please request a new OTP."
        )

    if otp_record.otp_hash != hashed_input:
        otp_record.attempts += 1
        db.commit()
        remaining_attempts = 5 - otp_record.attempts
        if remaining_attempts <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Too many invalid attempts. Please request a new OTP."
            )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid OTP code. {remaining_attempts} attempt{'s' if remaining_attempts != 1 else ''} remaining."
        )

    otp_record.verified = True
    db.commit()

    # Find or create user with phone
    user = db.query(User).filter(
        (User.phone == normalized_phone) | (User.phone == parsed.core_digits)
    ).first()
    if not user:
        user_id = str(uuid.uuid4())
        user = User(
            id=user_id,
            name=payload.name or "Friend",
            phone=normalized_phone,
            auth_provider="phone"
        )
        db.add(user)

        friend = FriendProfile(
            id=str(uuid.uuid4()),
            user_id=user_id,
            friend_name="Sakhi",
            gender="female",
            voice_id="female_voice"
        )
        setting = Setting(id=str(uuid.uuid4()), user_id=user_id)
        db.add_all([friend, setting])
        db.commit()
        db.refresh(user)
    elif user.phone != normalized_phone:
        user.phone = normalized_phone
        db.commit()

    access_token = create_access_token({"sub": user.id, "name": user.name})
    refresh_token = create_refresh_token({"sub": user.id})

    db_refresh = RefreshToken(
        id=str(uuid.uuid4()),
        user_id=user.id,
        token_hash=hash_token(refresh_token),
        expires_at=datetime.now(timezone.utc) + timedelta(days=30)
    )
    db.add(db_refresh)
    db.commit()

    return build_user_response_payload(user, db, access_token, refresh_token)

@router.post("/logout")
async def logout(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
    refresh_token_payload: Optional[RefreshTokenRequest] = None
):
    """
    Revokes refresh tokens on the server for real secure logout.
    """
    if refresh_token_payload and refresh_token_payload.refresh_token:
        hashed = hash_token(refresh_token_payload.refresh_token)
        db.query(RefreshToken).filter(
            RefreshToken.token_hash == hashed,
            RefreshToken.user_id == current_user.id
        ).update({"revoked_at": datetime.now(timezone.utc)})
    else:
        # Revoke all active refresh tokens for this user
        db.query(RefreshToken).filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.revoked_at.is_(None)
        ).update({"revoked_at": datetime.now(timezone.utc)})

    db.commit()
    return {"success": True, "message": "Logged out successfully."}
