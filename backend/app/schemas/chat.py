from typing import Optional, Literal
from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, description="The message from user (Telugu, English, or Tanglish)")
    conversation_id: Optional[str] = Field(None, description="Active conversation UUID if continuing")
    input_type: Literal["text", "voice"] = Field("text", description="Input modality")

class ChatResponse(BaseModel):
    reply: str
    display_text: Optional[str] = None
    speech_text: Optional[str] = None
    conversation_id: str
    message_id: str
    title: Optional[str] = None
    sender: str = "assistant"
    language: Optional[str] = "auto"
