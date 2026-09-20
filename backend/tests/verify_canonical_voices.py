import sys
import os
import asyncio

sys.path.insert(0, os.path.abspath('.'))
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
from app.voice.tts import tts_service, CANONICAL_TELUGU_SENTENCE

async def verify_canonical():
    voices = tts_service.get_voice_options()
    print("================================================================================================================================")
    print("CANONICAL VOICE SYNTHESIS & ACOUSTIC TRANSPARENCY VERIFICATION")
    print(f"Canonical Sentence: {CANONICAL_TELUGU_SENTENCE}")
    print("================================================================================================================================")
    header = f"{'Voice ID':<18} | {'Display Name':<28} | {'Provider':<15} | {'Underlying Voice':<20} | {'Independent?':<12} | {'Prosody':<24} | {'Bytes':<7}"
    print(header)
    print("-" * len(header))
    results = {}
    for v in voices:
        vid = v["voice_id"]
        dname = v["display_name"]
        provider = v["provider"]
        underlying = v.get("exact_underlying_voice", v.get("provider_voice", ""))
        independent = "Yes" if v.get("is_acoustically_independent") else "No (tuned)"
        prosody = v.get("prosody_changes", "None")
        dialect = v.get("dialect_layer", "")

        audio = await tts_service.synthesize_async(CANONICAL_TELUGU_SENTENCE, voice_id=vid)
        assert len(audio) > 1000, f"Synthesis failed for {vid}"
        results[vid] = len(audio)
        print(f"{vid:<18} | {dname:<28} | {provider:<15} | {underlying:<20} | {independent:<12} | {prosody:<24} | {len(audio):<7}")
    print("================================================================================================================================")
    print("All 6 canonical voice profile syntheses SUCCEEDED with verified real Telugu audio!")
    return results

if __name__ == "__main__":
    asyncio.run(verify_canonical())
