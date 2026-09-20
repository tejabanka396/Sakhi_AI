import logging
from fastapi import APIRouter, HTTPException, UploadFile, File, Response, Query
from fastapi.responses import Response
from app.schemas.voice import SynthesizeRequest, VoiceOptionsResponse, TranscribeResponse
from app.voice.tts import tts_service
from app.voice.stt import stt_service

logger = logging.getLogger("sakhi_ai.api.voice")

router = APIRouter()

@router.get("/options", response_model=VoiceOptionsResponse)
async def get_voice_options():
    """
    Returns available voice profiles with descriptions and sample texts.
    """
    voices = tts_service.get_voice_options()
    return {"voices": voices}

@router.post("/synthesize")
async def synthesize_speech(payload: SynthesizeRequest):
    """
    Synthesizes input text to natural speech and returns binary audio/mpeg.
    If input text is empty or TTS returns empty bytes, returns a clean 200 response.
    """
    if not payload.text or not payload.text.strip():
        return Response(
            content=b"",
            media_type="audio/mpeg",
            status_code=200,
            headers={
                "Content-Disposition": "inline; filename=sakhi_speech.mp3",
                "Accept-Ranges": "bytes"
            }
        )

    try:
        audio_bytes = await tts_service.synthesize_async(
            text=payload.text,
            voice_id=payload.voice_id,
            language=payload.language
        )
        if not audio_bytes:
            return Response(
                content=b"",
                media_type="audio/mpeg",
                status_code=200,
                headers={
                    "Content-Disposition": "inline; filename=sakhi_speech.mp3",
                    "Accept-Ranges": "bytes"
                }
            )

        return Response(
            content=audio_bytes,
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": "inline; filename=sakhi_speech.mp3",
                "Accept-Ranges": "bytes"
            }
        )
    except Exception as e:
        logger.error(f"Voice synthesis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Could not synthesize speech.")

@router.get("/preview/{voice_id}")
async def preview_voice(voice_id: str):
    """
    Direct endpoint for audio preview of a specific voice.
    """
    options = {v["id"]: v for v in tts_service.get_voice_options()}
    voice = options.get(voice_id)
    sample_text = voice["sample_text"] if voice else "నమస్కారం! నేను మీ సఖిని."

    audio_bytes = await tts_service.synthesize_async(text=sample_text, voice_id=voice_id)
    return Response(content=audio_bytes, media_type="audio/mpeg")

@router.post("/transcribe", response_model=TranscribeResponse)
async def transcribe_audio(file: UploadFile = File(...)):
    """
    Transcribes uploaded audio file (WebM / WAV / MP3) to text.
    """
    try:
        content = await file.read()
        mime_type = file.content_type or "audio/webm"
        transcript = await stt_service.transcribe_audio_bytes(content, mime_type=mime_type)
        return TranscribeResponse(
            transcript=transcript or "Sarigga vinapadaledu, inko sari cheptara?",
            language="te"
        )
    except Exception as e:
        logger.error(f"Transcription endpoint error: {e}", exc_info=True)
        return TranscribeResponse(
            transcript="",
            language="te"
        )
