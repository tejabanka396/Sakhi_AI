from typing import Optional
from pydantic import BaseModel, Field

class MemoryCreate(BaseModel):
    memory_text: str = Field(..., min_length=2, max_length=1000)
    category: str = Field("preference", description="Category: preference, learning, goal, personal")

class MemoryItem(BaseModel):
    id: str
    user_id: str
    memory_text: str
    category: str
    created_at: str
    updated_at: Optional[str] = None
