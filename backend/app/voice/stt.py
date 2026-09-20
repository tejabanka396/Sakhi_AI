import logging
from typing import Optional

try:
    from google import genai
    from google.genai import types
    HAS_GOOGLE_GENAI = True
except ImportError:
    HAS_GOOGLE_GENAI = False

try:
    import google.generativeai as legacy_genai
    HAS_LEGACY_GENAI = True
except ImportError:
    HAS_LEGACY_GENAI = False

from app.core.config import settings

logger = logging.getLogger("sakhi_ai.voice.stt")

class STTService:
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        self.client = None

        if self.api_key:
            if HAS_GOOGLE_GENAI:
                try:
                    self.client = genai.Client(api_key=self.api_key)
                except Exception as e:
                    logger.warning(f"Could not initialize Google GenAI Client for STT: {e}")
            elif HAS_LEGACY_GENAI:
                try:
                    legacy_genai.configure(api_key=self.api_key)
                except Exception as e:
                    logger.warning(f"Could not configure legacy Gemini for STT: {e}")

    async def transcribe_audio_bytes(self, audio_bytes: bytes, mime_type: str = "audio/webm") -> str:
        """
        Transcribes audio bytes into Telugu or English text using Gemini multimodal recognition.
        """
        if not self.api_key or not audio_bytes:
            return ""

        prompt = (
            "Listen carefully to this audio recording in Telugu or English. "
            "Transcribe exactly what is spoken by the speaker. "
            "Do not add any commentary, explanations, or notes. "
            "Return ONLY the verbatim transcript text."
        )

        if self.client and HAS_GOOGLE_GENAI:
            try:
                part = types.Part.from_bytes(data=audio_bytes, mime_type=mime_type)
                response = await self.client.aio.models.generate_content(
                    model=settings.GEMINI_MODEL,
                    contents=[part, prompt]
                )
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.warning(f"Google GenAI audio transcription error: {e}. Trying legacy if available.")

        if HAS_LEGACY_GENAI:
            try:
                model = legacy_genai.GenerativeModel(model_name=settings.GEMINI_MODEL)
                response = model.generate_content([
                    {"mime_type": mime_type, "data": audio_bytes},
                    prompt
                ])
                if response and response.text:
                    return response.text.strip()
            except Exception as e:
                logger.error(f"Legacy audio transcription error: {e}", exc_info=True)

        return ""

stt_service = STTService()
