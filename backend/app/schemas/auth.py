from typing import Optional
from pydantic import BaseModel, EmailStr, Field

class RegisterRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=100)
    email: EmailStr
    password: str = Field(..., min_length=6, max_length=100)
    phone: Optional[str] = None

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class GoogleAuthRequest(BaseModel):
    token: Optional[str] = None
    email: Optional[EmailStr] = None
    name: Optional[str] = None

class PhoneOTPRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)

class PhoneVerifyRequest(BaseModel):
    phone: str = Field(..., min_length=10, max_length=15)
    otp: str = Field(..., min_length=4, max_length=6)
    name: Optional[str] = "Friend"

class RefreshTokenRequest(BaseModel):
    refresh_token: str

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict
    friend_profile: Optional[dict] = None
    settings: Optional[dict] = None
    onboarding_completed: bool = False
