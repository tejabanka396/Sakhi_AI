from typing import Optional
from pydantic import BaseModel, EmailStr

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    auth_provider: str
    created_at: str
    onboarding_completed: bool = False
