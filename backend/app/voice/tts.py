import io
import re
import time
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

        t0 = time.perf_counter()
        has_telugu_script = bool(re.search(r'[\u0C00-\u0C7F]', clean_text))
        target_lang = self.detect_language(clean_text) if language == "auto" else language
        profile = self.resolve_profile(voice_id)
        gender = profile.get("gender", "female")

        # 1. Edge-TTS Neural Voice Selection:
        # Telugu / Tanglish -> Telugu Neural Voice (te-IN-ShrutiNeural for female, te-IN-MohanNeural for male)
        # English -> Indian English Neural Voice (en-IN-NeerjaNeural for female, en-IN-PrabhatNeural for male)
        if has_telugu_script or target_lang == "te":
            edge_v = profile.get("te_voice", "te-IN-ShrutiNeural" if gender == "female" else "te-IN-MohanNeural")
            rate = profile.get("te_rate", "+5%" if gender == "female" else "+10%")
            pitch = profile.get("te_pitch", "+4Hz")
        else:
            edge_v = profile.get("en_voice", "en-IN-NeerjaNeural" if gender == "female" else "en-IN-PrabhatNeural")
            rate = profile.get("en_rate", "+0%")
            pitch = profile.get("en_pitch", "+0Hz")

        async def _stream_edge_tts() -> bytes:
            communicate = edge_tts.Communicate(
                text=clean_text,
                voice=edge_v,
                rate=rate,
                pitch=pitch
            )
            data = b""
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    data += chunk["data"]
            return data

        try:
            audio_bytes = await asyncio.wait_for(_stream_edge_tts(), timeout=7.0)
            elapsed_ms = (time.perf_counter() - t0) * 1000
            if audio_bytes and len(audio_bytes) > 200:
                logger.info(
                    f"[TTS_TIMING] Success: voice_id={voice_id} gender={gender} "
                    f"edge_voice={edge_v} duration_ms={elapsed_ms:.1f} bytes={len(audio_bytes)}"
                )
                return audio_bytes
        except asyncio.TimeoutError:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.warning(f"[TTS_TIMEOUT] Edge-TTS timed out after {elapsed_ms:.1f}ms for voice_id={voice_id} ({edge_v})")
        except Exception as e:
            elapsed_ms = (time.perf_counter() - t0) * 1000
            logger.warning(f"[TTS_ERROR] Edge-TTS failed after {elapsed_ms:.1f}ms for voice_id={voice_id} ({edge_v}): {type(e).__name__} - {str(e)[:150]}")

        # 2. Strict Gender-Preserving Fallback Handling:
        # NEVER use gTTS for a male companion because gTTS only has a female voice,
        # which would cause a male companion to speak with a female voice.
        if gender == "male":
            logger.error(
                f"[TTS_FAIL] Controlled TTS failure for male companion (voice_id={voice_id}). "
                f"Suppressing gTTS to prevent male companion from speaking in female voice."
            )
            return b""

        # Controlled female-only failover: gTTS can only be used if the companion is female
        try:
            gtts_t0 = time.perf_counter()
            fp = io.BytesIO()
            if has_telugu_script or target_lang == "te":
                tts = gTTS(text=clean_text, lang="te", slow=False)
            else:
                tts = gTTS(text=clean_text, lang="en", tld="co.in", slow=False)
            tts.write_to_fp(fp)
            fp.seek(0)
            gtts_bytes = fp.read()
            gtts_ms = (time.perf_counter() - gtts_t0) * 1000
            logger.info(f"[TTS_FALLBACK] Female gTTS fallback succeeded in {gtts_ms:.1f}ms, bytes={len(gtts_bytes)}")
            return gtts_bytes
        except Exception as gtts_err:
            logger.error(f"[TTS_FALLBACK_FAIL] Female gTTS fallback failed: {type(gtts_err).__name__} - {str(gtts_err)[:150]}")
            return b""


tts_service = TTSService()
