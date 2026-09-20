import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient
from app.main import app
from app.voice.sanitizer import sanitize_text_for_tts
from app.voice.tts import tts_service, VOICE_PROFILES, VOICE_ALIASES, get_voice_for_gender, migrate_voice_id
from app.ai.service import chat_service
from app.database.database import SessionLocal
from app.database.models import Message

client = TestClient(app)


def test_voice_options():
    """
    Verify /api/voice/options returns exactly 2 active voices: female_voice and male_voice.
    No legacy technical IDs are exposed in the options list.
    """
    res = client.get("/api/voice/options")
    assert res.status_code == 200
    data = res.json()
    assert "voices" in data
    assert len(data["voices"]) == 2

    # Verify exactly 1 female and 1 male voice
    female_voices = [v for v in data["voices"] if v["gender"] == "female"]
    male_voices = [v for v in data["voices"] if v["gender"] == "male"]
    assert len(female_voices) == 1
    assert len(male_voices) == 1

    voice_map = {v["voice_id"]: v for v in data["voices"]}
    assert "female_voice" in voice_map
    assert "male_voice" in voice_map

    # Check female voice properties
    fv = voice_map["female_voice"]
    assert fv["display_name"] == "Female Voice"
    assert fv["provider_voice"] == "te-IN-ShrutiNeural"
    assert fv["gender"] == "female"
    assert "sample_text" in fv

    # Check male voice properties
    mv = voice_map["male_voice"]
    assert mv["display_name"] == "Male Voice"
    assert mv["provider_voice"] == "te-IN-MohanNeural"
    assert mv["gender"] == "male"
    assert "sample_text" in mv


def test_gender_mapping_and_legacy_migration():
    """
    Test centralized gender mapping and backward compatibility migration:
    - female -> female_voice
    - male -> male_voice
    - legacy aliases migrate to female_voice or male_voice
    """
    # 1. Gender mapping
    assert get_voice_for_gender("female") == "female_voice"
    assert get_voice_for_gender("Female") == "female_voice"
    assert get_voice_for_gender("FEMALE") == "female_voice"
    assert get_voice_for_gender("male") == "male_voice"
    assert get_voice_for_gender("Male") == "male_voice"
    assert get_voice_for_gender("MALE") == "male_voice"
    assert get_voice_for_gender(None) == "female_voice"
    assert get_voice_for_gender("unknown") == "female_voice"

    # 2. Legacy migration
    assert migrate_voice_id("female_soft") == "female_voice"
    assert migrate_voice_id("female_friendly") == "female_voice"
    assert migrate_voice_id("female_andhra") == "female_voice"
    assert migrate_voice_id("female_energetic") == "female_voice"
    assert migrate_voice_id("female_telangana") == "female_voice"

    assert migrate_voice_id("male_friendly") == "male_voice"
    assert migrate_voice_id("male_warm") == "male_voice"
    assert migrate_voice_id("male_calm") == "male_voice"
    assert migrate_voice_id("male_deep_calm") == "male_voice"
    assert migrate_voice_id("male_energetic") == "male_voice"

    # 3. Gender takes precedence when provided
    assert migrate_voice_id("female_soft", gender="male") == "male_voice"
    assert migrate_voice_id("male_warm", gender="female") == "female_voice"


def test_tts_emoji_and_markdown_sanitization():
    # 1. Test emoji stripping (audio must never speak emojis)
    raw_emoji_text = "That's amazing! ❤️😂 Keep shining! ✨🚀"
    clean_text = sanitize_text_for_tts(raw_emoji_text)
    assert "❤️" not in clean_text
    assert "😂" not in clean_text
    assert "✨" not in clean_text
    assert "🚀" not in clean_text
    assert "That's amazing!" in clean_text
    assert "Keep shining!" in clean_text

    # 2. Test markdown stripping (bold, italic, headers, code, bullet marks)
    markdown_text = """### Deadlock Conditions:
**1. Mutual Exclusion**: Only one process can hold resource.
- *Hold and Wait*: Process waits for next resource.
```python
def deadlock(): pass
```
Visit [Sakhi Portal](https://sakhi.ai) for details."""
    clean_md = sanitize_text_for_tts(markdown_text)
    assert "###" not in clean_md
    assert "**" not in clean_md
    assert "```" not in clean_md
    assert "https://" not in clean_md
    assert "Mutual Exclusion" in clean_md
    assert "Hold and Wait" in clean_md
    assert "Sakhi Portal" in clean_md


def test_two_voice_synthesis_and_previews():
    """
    Test audio preview endpoints for female_voice and male_voice.
    """
    for vid in ["female_voice", "male_voice"]:
        res = client.get(f"/api/voice/preview/{vid}")
        assert res.status_code == 200
        assert res.headers["content-type"] == "audio/mpeg"
        assert len(res.content) > 500


def test_voice_synthesize_telugu_with_sanitization():
    res = client.post("/api/voice/synthesize", json={
        "text": "హలో తేజా! ❤️ నేను మీ సఖిని. ఎలా ఉన్నావు? 😄",
        "voice_id": "female_voice",
        "language": "te"
    })
    assert res.status_code == 200
    assert res.headers["content-type"] == "audio/mpeg"
    assert len(res.content) > 1000


def test_required_sanitizer_suite():
    # TEST 1: Emojis stripped
    t1_in = "That's awesome! ❤️ 😊 Deadlock ante..."
    assert sanitize_text_for_tts(t1_in) == "That's awesome! Deadlock ante..."

    # TEST 2: Compound spoken emoji descriptions stripped
    t2_in = "That's awesome! red heart smiling face. Deadlock ante..."
    assert sanitize_text_for_tts(t2_in) == "That's awesome! Deadlock ante..."

    # TEST 3: Thumbs up emoji stripped
    t3_in = "Great job! 👍"
    assert sanitize_text_for_tts(t3_in) == "Great job!"

    # TEST 4: Telugu script with emojis
    t4_in = "బాగుంది! చాలా మంచి పని చేశావు! ❤️ 👍 రేపు కలుద్దాం."
    assert sanitize_text_for_tts(t4_in) == "బాగుంది! చాలా మంచి పని చేశావు! రేపు కలుద్దాం."

    # TEST 5: Tanglish with emojis
    t5_in = "Chala bagundi bro! 😊 Inka emiti sangathulu? 🔥"
    assert sanitize_text_for_tts(t5_in) == "Chala bagundi bro! Inka emiti sangathulu?"

    # TEST 6: Educational / medical sentences preserved
    t6_in = "The human heart pumps blood throughout the body. Normal resting heart rate is between 60 to 100 bpm. Coronary heart disease is a serious condition."
    assert sanitize_text_for_tts(t6_in) == t6_in

    # TEST 7: Smiling face detection (educational / CV context) preserved
    t7_in = "Smiling face detection is an important computer vision application in deep learning."
    assert sanitize_text_for_tts(t7_in) == t7_in

    # TEST 8: Only emojis and whitespace -> empty string
    t8_in = "❤️ 😊 👍"
    assert sanitize_text_for_tts(t8_in) == ""

    # TEST 9: Compound with dots cleaned
    t9_in = "Great job! red heart. smiling face. Deadlock ante..."
    assert sanitize_text_for_tts(t9_in) == "Great job! Deadlock ante..."

    # TEST 10: Leading dot cleaned
    t10_in = ". Hello"
    assert sanitize_text_for_tts(t10_in) == "Hello"

    # TEST 11: Natural ellipsis preserved
    t11_in = "Wait... let's continue."
    assert sanitize_text_for_tts(t11_in) == "Wait... let's continue."


def test_tts_empty_and_skip_edge_tts():
    emoji_only_text = "❤️ 😊 👍"
    assert sanitize_text_for_tts(emoji_only_text) == ""

    with patch("edge_tts.Communicate") as mock_edge, patch("app.voice.tts.gTTS") as mock_gtts:
        audio = tts_service.synthesize(emoji_only_text)
        assert audio == b""
        mock_edge.assert_not_called()
        mock_gtts.assert_not_called()

    res_emoji = client.post("/api/voice/synthesize", json={
        "text": "❤️ 😊 👍",
        "voice_id": "female_voice"
    })
    assert res_emoji.status_code == 200
    assert res_emoji.content == b""

    res_empty = client.post("/api/voice/synthesize", json={
        "text": "",
        "voice_id": "female_voice"
    })
    assert res_empty.status_code == 200
    assert res_empty.content == b""


def test_tts_safe_logging_never_logs_user_text(caplog):
    sensitive_token = "SECRET_AADHAAR_PHONE_9988776655_PRIVATE_TEXT_XYZ"
    test_input = f"Hello there! ❤️ 😊 {sensitive_token} test"

    with caplog.at_level("INFO", logger="sakhi_ai.voice.tts"):
        tts_service.synthesize(test_input)

    captured_logs = caplog.text
    assert sensitive_token not in captured_logs
    assert "Hello there" not in captured_logs
    assert "PRIVATE_TEXT" not in captured_logs
    assert "original_length=" in captured_logs
    assert "sanitized_length=" in captured_logs


def test_chat_two_tier_response_and_storage():
    simulated_gemini_reply = "That's awesome! ❤️ Deadlock ante oka situation."

    with patch.object(chat_service.provider, "generate_response", return_value=simulated_gemini_reply):
        res = client.post("/api/chat", json={
            "message": "Tell me about deadlock ❤️",
            "input_type": "text"
        })
        assert res.status_code == 200
        data = res.json()

        assert "display_text" in data
        assert "speech_text" in data
        assert data["display_text"] == "That's awesome! ❤️ Deadlock ante oka situation."
        assert data["speech_text"] == "That's awesome! Deadlock ante oka situation."
        assert data["reply"] == data["display_text"]
        assert "❤️" in data["display_text"]
        assert "❤️" not in data["speech_text"]

        db = SessionLocal()
        try:
            db_msg = db.query(Message).filter_by(id=data["message_id"]).first()
            assert db_msg is not None
            assert db_msg.content == data["display_text"]
            assert "❤️" in db_msg.content
        finally:
            db.close()

        tts_clean = sanitize_text_for_tts(data["speech_text"])
        assert "❤️" not in tts_clean
        assert tts_clean == "That's awesome! Deadlock ante oka situation."
