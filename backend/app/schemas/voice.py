from typing import Optional, List
from pydantic import BaseModel, Field

class SynthesizeRequest(BaseModel):
    text: str = Field("", max_length=2000, description="Text to synthesize to speech")
    voice_id: str = Field("female_voice", description="Voice identifier")
    language: str = Field("auto", description="Target language: auto, te, en")

class VoiceOption(BaseModel):
    id: str
    voice_id: str
    name: str
    display_name: str
    label: Optional[str] = None
    gender: str
    style: str
    personality: Optional[str] = None
    dialect: Optional[str] = None
    language: str
    sample_text: str
    description: str
    provider: Optional[str] = None
    provider_voice: Optional[str] = None
    exact_underlying_voice: Optional[str] = None
    is_acoustically_independent: bool = False
    prosody_changes: Optional[str] = None
    dialect_layer: Optional[str] = None
    underlying_model: Optional[str] = None
    model_notes: Optional[str] = None
    preview_supported: bool = True

class VoiceOptionsResponse(BaseModel):
    voices: List[VoiceOption]

class TranscribeResponse(BaseModel):
    transcript: str
    language: str = "te"
