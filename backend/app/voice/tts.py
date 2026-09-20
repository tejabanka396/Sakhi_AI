import io
import re
import asyncio
import logging
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from gtts import gTTS
import edge_tts
from app.voice.sanitizer import sanitize_text_for_tts
from app.core.config import settings

logger = logging.getLogger("sakhi_ai.voice.tts")

# Canonical test & preview sentence required by Master Prompt
CANONICAL_TELUGU_SENTENCE = "నువ్వు ఈరోజు ఎలా ఉన్నావు? నాకు చెప్పు, నేను నీతో మాట్లాడటానికి ఇక్కడే ఉన్నాను."

# Exactly two active curated voice profiles: female_voice and male_voice
VOICE_PROFILES: Dict[str, Dict[str, Any]] = {
    # --------------------------------------------------------------------------
    # FEMALE VOICE — Telangana Telugu Configuration (Azure ShrutiNeural)
    # --------------------------------------------------------------------------
    "female_voice": {
        "id": "female_voice",
        "voice_id": "female_voice",
        "name": "Female Voice",
        "display_name": "Female Voice",
        "label": "Female Voice",
        "gender": "female",
        "style": "Playful & Expressive",
        "personality": "playful, confident, expressive, friendly",
        "dialect": "Telangana Telugu",
        "engine": "edge",
        "provider": "Microsoft Edge TTS",
        "provider_voice": "te-IN-ShrutiNeural",
        "exact_underlying_voice": "te-IN-ShrutiNeural",
        "is_acoustically_independent": True,
        "prosody_changes": "Pitch: +4Hz, Rate: +5%",
        "dialect_layer": "Natural everyday Telangana conversational flavor",
        "underlying_model": "te-IN-ShrutiNeural (Expressive Rhythm)",
        "language": "Telugu & English",
        "sample_text": CANONICAL_TELUGU_SENTENCE,
        "description": "Natural Telugu female voice",
        "model_notes": "Microsoft Edge TTS te-IN-ShrutiNeural with subtle Telangana conversational cadence (+5% rate, +4Hz pitch)",
        "preview_supported": True,
        "te_voice": "te-IN-ShrutiNeural",
        "te_rate": "+5%",
        "te_pitch": "+4Hz",
        "en_voice": "en-IN-NeerjaNeural",
        "en_rate": "+0%",
        "en_pitch": "+0Hz",
    },

    # --------------------------------------------------------------------------
    # MALE VOICE — Energetic Configuration (Azure MohanNeural)
    # --------------------------------------------------------------------------
    "male_voice": {
        "id": "male_voice",
        "voice_id": "male_voice",
        "name": "Male Voice",
        "display_name": "Male Voice",
        "label": "Male Voice",
        "gender": "male",
        "style": "Energetic & Upbeat",
        "personality": "young, cheerful, fun, energetic, highly conversational",
        "dialect": "Natural Telugu",
        "engine": "edge",
        "provider": "Microsoft Edge TTS",
        "provider_voice": "te-IN-MohanNeural",
        "exact_underlying_voice": "te-IN-MohanNeural",
        "is_acoustically_independent": True,
        "prosody_changes": "Pitch: +4Hz, Rate: +10%",
        "dialect_layer": "Casual everyday Telugu (youthful, energetic, upbeat)",
        "underlying_model": "te-IN-MohanNeural (Upbeat Tempo)",
        "language": "Telugu & English",
        "sample_text": CANONICAL_TELUGU_SENTENCE,
        "description": "Natural Telugu male voice",
        "model_notes": "Microsoft Edge TTS te-IN-MohanNeural with energetic conversational tempo (+10% rate, +4Hz pitch)",
        "preview_supported": True,
        "te_voice": "te-IN-MohanNeural",
        "te_rate": "+10%",
        "te_pitch": "+4Hz",
        "en_voice": "en-IN-PrabhatNeural",
        "en_rate": "+0%",
        "en_pitch": "+0Hz",
    },
}

# Legacy voice ID mappings strictly for backward compatibility
VOICE_ALIASES: Dict[str, str] = {
    # Old female IDs -> female_voice
    "female_soft": "female_voice",
    "female_friendly": "female_voice",
    "female_andhra": "female_voice",
    "female_energetic": "female_voice",
    "female_telangana": "female_voice",
    "ananya": "female_voice",
    "sravani": "female_voice",
    "harika": "female_voice",
    # Old male IDs -> male_voice
    "male_friendly": "male_voice",
    "male_warm": "male_voice",
    "male_calm": "male_voice",
    "male_deep_calm": "male_voice",
    "male_energetic": "male_voice",
    "karthik": "male_voice",
    "rao": "male_voice",
    "varun": "male_voice",
}


def get_voice_for_gender(gender: Optional[str]) -> str:
    """
    Gender normalization (female, Female, FEMALE -> female_voice; male, Male, MALE -> male_voice).
    If missing or invalid, safely defaults to female_voice.
    """
    if not gender:
        return "female_voice"
    clean = str(gender).strip().lower()
    if clean == "male":
        return "male_voice"
    return "female_voice"


def migrate_voice_id(voice_id: Optional[str], gender: Optional[str] = None) -> str:
    """
    Safely migrates legacy voice IDs to female_voice or male_voice.
    Enforces consistency with companion gender if provided.
    """
    if gender:
        return get_voice_for_gender(gender)
    if not voice_id:
        return "female_voice"
    vid = str(voice_id).strip().lower()
    if vid in VOICE_PROFILES:
        return vid
    if vid in VOICE_ALIASES:
        return VOICE_ALIASES[vid]
    if "male" in vid:
        return "male_voice"
    return "female_voice"


class TTSService:
    def get_voice_options(self) -> List[Dict[str, Any]]:
        """
        Returns exactly the 2 active voice profiles (female_voice, male_voice).
        No legacy IDs or unselected cards are exposed.
        """
        return [
            {
                "id": v["id"],
                "voice_id": v["voice_id"],
                "name": v["name"],
                "display_name": v["display_name"],
                "label": v.get("label", v["name"]),
                "gender": v["gender"],
                "style": v["style"],
                "personality": v["personality"],
                "dialect": v["dialect"],
                "provider": v.get("provider", "Microsoft Edge TTS"),
                "provider_voice": v.get("provider_voice", v["te_voice"]),
                "exact_underlying_voice": v.get("exact_underlying_voice", v.get("provider_voice")),
                "is_acoustically_independent": v.get("is_acoustically_independent", True),
                "prosody_changes": v.get("prosody_changes", "None"),
                "dialect_layer": v.get("dialect_layer", ""),
                "underlying_model": v.get("underlying_model", v["id"]),
                "model_notes": v.get("model_notes", ""),
                "language": v["language"],
                "sample_text": v["sample_text"],
                "description": v["description"],
                "preview_supported": v.get("preview_supported", True)
            }
            for v in VOICE_PROFILES.values()
        ]

    def resolve_profile(self, voice_id: str) -> Dict[str, Any]:
        """Resolves profile with alias support and default fallback to female_voice."""
        clean_id = (voice_id or "").strip().lower()
        key = VOICE_ALIASES.get(clean_id, clean_id)
        return VOICE_PROFILES.get(key, VOICE_PROFILES["female_voice"])

    def detect_language(self, text: str) -> str:
        """
        Detects whether the clean text is primarily Telugu (Unicode or Tanglish) or English.
        """
        if re.search(r'[\u0C00-\u0C7F]', text):
            return "te"
        
        tanglish_words = {
            "ela", "unnav", "unnavu", "cheppu", "endi", "enti", "ante", "naaku",
            "chala", "baaga", "ledu", "kadu", "kadha", "em", "jarigindi", "chey",
            "cheyyi", "cheddam", "ra", "bro", "nenu", "unnanu", "babu", "amma",
            "ayyo", "mari", "inka", "eppudu", "ekkada", "enduku", "avunu", "kuda",
            "namaskaram", "namaste", "bagunnanu", "bavunna", "matladu"
        }
        words = set(re.findall(r'\b\w+\b', text.lower()))
        if words.intersection(tanglish_words):
            return "te"
        return "en"

    async def synthesize_async(self, text: str, voice_id: str = "female_voice", language: str = "auto") -> bytes:
        """
        Direct native async synthesis entry point without threadpool dispatch.
        Used by FastAPI routes for maximum speed and minimal latency.
        """
        original_length = len(text or "")
        speech_text = sanitize_text_for_tts(text)
        sanitized_length = len(speech_text)
        logger.info(f"TTS synthesis: original_length={original_length} sanitized_length={sanitized_length}")
        if not speech_text:
            return b""
        return await self._synthesize_async(speech_text, voice_id, language)

    def synthesize(self, text: str, voice_id: str = "female_voice", language: str = "auto") -> bytes:
        """
        Synchronous wrapper for scripts or sync test runners.
        """
        original_length = len(text or "")
        speech_text = sanitize_text_for_tts(text)
        sanitized_length = len(speech_text)
        logger.info(f"TTS synthesis: original_length={original_length} sanitized_length={sanitized_length}")
        if not speech_text:
            return b""

        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                    return pool.submit(asyncio.run, self._synthesize_async(speech_text, voice_id, language)).result()
            else:
                return asyncio.run(self._synthesize_async(speech_text, voice_id, language))
        except Exception as e:
            logger.warning(f"Async loop dispatch warning: {e}. Running direct thread execution.")
            return asyncio.run(self._synthesize_async(speech_text, voice_id, language))

    async def _synthesize_async(self, clean_text: str, voice_id: str, language: str) -> bytes:
        if not clean_text or not clean_text.strip():
            return b""

        has_telugu_script = bool(re.search(r'[\u0C00-\u0C7F]', clean_text))
        target_lang = self.detect_language(clean_text) if language == "auto" else language
        profile = self.resolve_profile(voice_id)

        # 1. Edge-TTS Neural Synthesis
        if has_telugu_script:
            edge_v = profile.get("te_voice", "te-IN-ShrutiNeural" if profile.get("gender") == "female" else "te-IN-MohanNeural")
            rate = profile.get("te_rate", "+5%" if profile.get("gender") == "female" else "+10%")
            pitch = profile.get("te_pitch", "+4Hz")
        else:
            edge_v = profile.get("en_voice", "en-IN-NeerjaNeural" if profile.get("gender") == "female" else "en-IN-PrabhatNeural")
            rate = profile.get("en_rate", "+0%")
            pitch = profile.get("en_pitch", "+0Hz")

        try:
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=edge_v,
                rate=rate,
                pitch=pitch
            )
            audio_bytes = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    audio_bytes += chunk["data"]

            if audio_bytes and len(audio_bytes) > 200:
                return audio_bytes
        except Exception as e:
            logger.warning(f"Edge-TTS failed for voice {voice_id} ({edge_v}): {e}. Attempting gTTS fallback.")

        # 2. Failover to gTTS if Edge-TTS encounters network failure
        try:
            fp = io.BytesIO()
            if has_telugu_script or target_lang == "te":
                tts = gTTS(text=clean_text, lang="te", slow=False)
            else:
                tts = gTTS(text=clean_text, lang="en", tld="co.in", slow=False)
            tts.write_to_fp(fp)
            fp.seek(0)
            return fp.read()
        except Exception as gtts_err:
            logger.error(f"gTTS fallback also failed: {gtts_err}", exc_info=True)
            return b""


tts_service = TTSService()
