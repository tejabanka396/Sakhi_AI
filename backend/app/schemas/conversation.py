from typing import Optional, List
from pydantic import BaseModel, Field

class ConversationUpdate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)

class MessageItem(BaseModel):
    id: str
    conversation_id: str
    sender: str
    content: str
    input_type: str
    created_at: str

class ConversationSummary(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    message_count: int = 0
    last_message: Optional[str] = None

class ConversationDetail(BaseModel):
    id: str
    user_id: str
    title: str
    created_at: str
    updated_at: str
    messages: List[MessageItem]
