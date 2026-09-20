from typing import Optional, Literal
from pydantic import BaseModel, Field

class FriendProfileUpdate(BaseModel):
    friend_name: Optional[str] = Field(None, min_length=1, max_length=50)
    gender: Optional[Literal["female", "male"]] = None
    voice_id: Optional[str] = None
    personality: Optional[str] = None

class FriendProfileResponse(BaseModel):
    id: str
    user_id: str
    friend_name: str
    gender: str
    voice_id: str
    personality: str

class SettingUpdate(BaseModel):
    default_mode: Optional[Literal["talk", "chat", "auto"]] = None
    voice_enabled: Optional[bool] = None
    always_speak: Optional[bool] = None
    language_preference: Optional[Literal["auto", "telugu", "english"]] = None

class SettingResponse(BaseModel):
    id: str
    user_id: str
    default_mode: str
    voice_enabled: bool
    always_speak: bool
    language_preference: str
