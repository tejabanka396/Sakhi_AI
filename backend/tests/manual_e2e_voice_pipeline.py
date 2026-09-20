import os
import sys
import asyncio
import logging

# Add backend directory to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    except Exception:
        pass

from app.ai.gemini import gemini_provider
from app.ai.prompts import build_sakhi_system_prompt
from app.voice.sanitizer import sanitize_text_for_tts
from app.voice.tts import tts_service, VOICE_PROFILES

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("e2e_voice_pipeline")

async def run_pipeline_step(step_name: str, user_prompt: str, voice_id: str, output_filename: str):
    print(f"\n{'='*70}")
    print(f"▶ STEP: {step_name}")
    print(f"{'='*70}")
    print(f"1. User Prompt: '{user_prompt}'")
    print(f"   Selected Voice Profile: '{voice_id}' ({VOICE_PROFILES[voice_id]['name']})")
    print(f"   Underlying Model: {VOICE_PROFILES[voice_id]['underlying_model']}")
    print(f"   Provider: {VOICE_PROFILES[voice_id]['provider']}")

    # 1. Gemini / LLM Generation with Sakhi Persona System Prompt
    system_prompt = build_sakhi_system_prompt(
        user_name="Teja",
        friend_name="Sakhi" if "female" in voice_id else "Sakha",
        gender="female" if "female" in voice_id else "male",
        personality="friendly",
        language_preference="auto",
        conversation_mode="talk",
        memories=["Teja is an engineering student preparing for tech interviews."],
        detected_language="auto"
    )

    messages = [{"role": "user", "content": user_prompt}]
    
    print("\n2. Calling Gemini LLM Engine...")
    raw_ai_reply = await gemini_provider.generate_response(
        system_instruction=system_prompt,
        messages=messages,
        temperature=0.7
    )
    print(f"   Gemini Raw AI Response:\n   \"{raw_ai_reply}\"")

    # 2. Display Text (Rendered in Chat UI Bubble with visual markdown & emojis)
    display_text = raw_ai_reply
    print(f"\n3. Display Text for Chat Panel: Length={len(display_text)} chars")

    # 3. Speech Text Sanitizer (Must strip emojis, asterisks, markdown, and meta descriptions)
    clean_speech_text = sanitize_text_for_tts(display_text)
    print(f"\n4. TTS Speech Sanitized Text (emojis & markdown stripped):")
    print(f"   \"{clean_speech_text}\"")

    # Verify no raw emojis remain in speech text
    assert "😊" not in clean_speech_text
    assert "❤️" not in clean_speech_text
    assert "✨" not in clean_speech_text
    assert "🎉" not in clean_speech_text
    assert "**" not in clean_speech_text

    # 4. Selected Voice TTS Synthesis
    print(f"\n5. Synthesizing audio via {VOICE_PROFILES[voice_id]['underlying_model']}...")
    audio_bytes = tts_service.synthesize(text=clean_speech_text, voice_id=voice_id)
    print(f"   Audio Synthesized: {len(audio_bytes)} bytes")
    assert len(audio_bytes) > 1000, f"Synthesized audio too small: {len(audio_bytes)} bytes"

    # 5. Save audio playback file to verify
    output_path = os.path.join(os.path.dirname(__file__), output_filename)
    with open(output_path, "wb") as f:
        f.write(audio_bytes)
    print(f"6. Audio successfully written to: {output_path} (Ready for playback)")
    print(f"✔ PIPELINE PASSED FOR {step_name}!\n")

async def main():
    print("\n" + "#"*70)
    print("# SAKHI AI: MANUAL END-TO-END CONVERSATION & VOICE PIPELINE TEST")
    print("# Flow: Gemini LLM -> display_text -> TTS Sanitizer -> Selected TTS Voice -> Audio")
    print("#"*70)

    # Test Case 1: Pure Telugu Script with Shruti Neural (Female Friendly)
    await run_pipeline_step(
        step_name="Telugu Unicode Pipeline (Shruti Neural)",
        user_prompt="నమస్కారం సఖి! ఈరోజు నా కాలేజ్ ప్రాజెక్ట్ సబ్మిట్ చేశాను, చాలా సంతోషంగా ఉంది! 😊",
        voice_id="female_friendly",
        output_filename="e2e_telugu_reply.mp3"
    )

    # Test Case 2: Tanglish with Neerja Expressive (Female Energetic)
    await run_pipeline_step(
        step_name="Tanglish Pipeline (Neerja Expressive Neural)",
        user_prompt="Hey Sakhi, naaku repu oka technical interview undi. Koncham nervous ga undi, tips cheptava? 😊",
        voice_id="female_energetic",
        output_filename="e2e_tanglish_reply.mp3"
    )

    # Test Case 3: English with Prabhat Neural (Male Calm)
    await run_pipeline_step(
        step_name="English Pipeline (Prabhat Neural Male)",
        user_prompt="Hi Sakha! What are three practical daily habits to improve coding consistency?",
        voice_id="male_calm",
        output_filename="e2e_english_reply.mp3"
    )

    print("\n" + "="*70)
    print("ALL 3 END-TO-END REAL CONVERSATION PIPELINES VERIFIED SUCCESSFULLY!")
    print("="*70 + "\n")

if __name__ == "__main__":
    asyncio.run(main())
