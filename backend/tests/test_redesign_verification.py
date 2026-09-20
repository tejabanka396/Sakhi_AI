import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.voice.sanitizer import sanitize_text_for_tts
from app.voice.tts import tts_service, VOICE_PROFILES, VOICE_ALIASES, get_voice_for_gender, migrate_voice_id

client = TestClient(app)

def test_voice_options_two_distinct():
    """Verify exactly 2 active curated voice options: female_voice and male_voice"""
    res = client.get("/api/voice/options")
    assert res.status_code == 200
    voices = res.json()["voices"]
    assert len(voices) == 2

    female_voices = [v for v in voices if v["gender"] == "female"]
    male_voices = [v for v in voices if v["gender"] == "male"]
    assert len(female_voices) == 1
    assert len(male_voices) == 1

    voice_ids = {v["id"] for v in voices}
    assert voice_ids == {"female_voice", "male_voice"}

def test_two_voice_audio_previews():
    """Verify voice preview endpoints work for female_voice and male_voice"""
    for vid in ["female_voice", "male_voice"]:
        res = client.get(f"/api/voice/preview/{vid}")
        assert res.status_code == 200
        assert res.headers["content-type"] == "audio/mpeg"
        assert len(res.content) > 500

def test_voice_models_configuration():
    """Verify female and male voices use proper Edge TTS models and prosody configuration"""
    res = client.get("/api/voice/options")
    assert res.status_code == 200
    voices_by_id = {v["id"]: v for v in res.json()["voices"]}

    assert voices_by_id["female_voice"]["provider_voice"] == "te-IN-ShrutiNeural"
    assert voices_by_id["male_voice"]["provider_voice"] == "te-IN-MohanNeural"

    # Verify underlying voice profile specs
    female_prof = VOICE_PROFILES["female_voice"]
    assert female_prof["te_voice"] == "te-IN-ShrutiNeural"
    assert female_prof["en_voice"] == "en-IN-NeerjaNeural"
    assert female_prof["te_rate"] == "+5%"
    assert female_prof["te_pitch"] == "+4Hz"

    male_prof = VOICE_PROFILES["male_voice"]
    assert male_prof["te_voice"] == "te-IN-MohanNeural"
    assert male_prof["en_voice"] == "en-IN-PrabhatNeural"
    assert male_prof["te_rate"] == "+10%"
    assert male_prof["te_pitch"] == "+4Hz"

def test_legacy_voice_migration():
    """Verify all legacy voice IDs safely map to female_voice or male_voice"""
    legacy_females = ["female_soft", "female_friendly", "female_andhra", "female_energetic", "female_telangana"]
    for fid in legacy_females:
        assert migrate_voice_id(fid) == "female_voice"
        assert VOICE_ALIASES[fid] == "female_voice"

    legacy_males = ["male_friendly", "male_warm", "male_calm", "male_deep_calm", "male_energetic"]
    for mid in legacy_males:
        assert migrate_voice_id(mid) == "male_voice"
        assert VOICE_ALIASES[mid] == "male_voice"

def test_gender_mapping():
    """Verify gender strictly determines the voice"""
    assert get_voice_for_gender("female") == "female_voice"
    assert get_voice_for_gender("Female") == "female_voice"
    assert get_voice_for_gender("FEMALE") == "female_voice"

    assert get_voice_for_gender("male") == "male_voice"
    assert get_voice_for_gender("Male") == "male_voice"
    assert get_voice_for_gender("MALE") == "male_voice"

    assert get_voice_for_gender(None) == "female_voice"
    assert get_voice_for_gender("") == "female_voice"

def test_language_matrix_telugu_tanglish_english():
    """Verify Telugu, Tanglish, and English synthesize successfully on both active voices"""
    test_cases = [
        ("te_unicode", "హలో! నమస్కారం, ఎలా ఉన్నారు? అంతా బాగుందా?"),
        ("tanglish", "Namaskaram bro! Ela unnavu? Chala bagunnanu."),
        ("english", "Hello! I am your AI companion Sakhi. How can I help you today?")
    ]
    for lang_type, sample_text in test_cases:
        for vid in ["female_voice", "male_voice"]:
            audio = tts_service.synthesize(text=sample_text, voice_id=vid)
            assert len(audio) > 500, f"Synthesis failed for {vid} on {lang_type}"

def test_emoji_and_symbol_description_bug_fix():
    sample_1 = "That's awesome! ❤️😊👍 Great job!"
    cleaned_1 = sanitize_text_for_tts(sample_1)
    assert "❤️" not in cleaned_1
    assert "😊" not in cleaned_1
    assert "👍" not in cleaned_1
    assert "That's awesome!" in cleaned_1

    sample_2 = "Hello Teja red heart smiling face. How are you today? laughing emoji"
    cleaned_2 = sanitize_text_for_tts(sample_2)
    assert "red heart" not in cleaned_2.lower()
    assert "smiling face" not in cleaned_2.lower()
    assert "laughing emoji" not in cleaned_2.lower()
    assert "Hello Teja" in cleaned_2
    assert "How are you today?" in cleaned_2

def test_response_completion_no_truncation():
    long_explanation = (
        "Deadlock ante operating system lo rendu leda anthakante ekkuva processes okadanikosam okati wait chestu, "
        "deniki adhi resources release cheyakunda freeze aipoye situation. Idi jaragalante naalugu conditions mandatory ga undali: "
        "Modatidi Mutual Exclusion, ante oka resource ni oka time lo oka process mathrame vadukogaladu. "
        "Rendodidi Hold and Wait, ante process already oka resource ni hold cheskuni inko resource kosam wait chestu untundi. "
        "Moododidi No Preemption, ante allocate aina resource ni balavanthanga evaru lakkoleru. "
        "Naalugodidi Circular Wait, ante process P1 process P2 kosam, P2 process P3 kosam, P3 malli P1 kosam circular chain lo wait chestaru. "
        "Ivi unte system deadlock loki velthundi, deenni prevent cheyadaniki Bankers Algorithm mariyu Resource Allocation Graph vadataru."
    )
    assert len(long_explanation) > 700
    cleaned = sanitize_text_for_tts(long_explanation)
    assert len(cleaned) > 650
    assert "Bankers Algorithm" in cleaned
    assert "Resource Allocation Graph" in cleaned
