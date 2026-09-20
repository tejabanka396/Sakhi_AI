from typing import Optional, Literal, List, Dict
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
    response_id: Optional[str] = None
    voice_id: Optional[str] = None
    gender: Optional[str] = None
    title: Optional[str] = None
    sender: str = "assistant"
    language: Optional[str] = "auto"
    searched: bool = False
    sources: Optional[List[Dict[str, str]]] = None
    search_timestamp: Optional[str] = None
