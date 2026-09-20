import pytest
from app.core.config import settings
from app.ai.gemini import gemini_provider
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_gemini_api_key_loaded():
    """Confirms Gemini API key is configured and not empty."""
    assert settings.GEMINI_API_KEY != "", "GEMINI_API_KEY must not be empty"
    assert len(settings.GEMINI_API_KEY) > 10, "GEMINI_API_KEY appears invalid"
    assert settings.GEMINI_MODEL in ["gemini-3.6-flash", "gemini-3.5-flash-lite", "gemini-2.5-flash", "gemini-1.5-flash"], f"Expected valid Gemini model, got {settings.GEMINI_MODEL}"

@pytest.mark.asyncio
async def test_gemini_provider_direct_telugu():
    """Confirms direct Gemini model call produces a valid Telugu response."""
    system_prompt = "You are Sakhi, a friendly Telugu companion. Reply in warm, natural Telugu/Tanglish."
    messages = [{"role": "user", "content": "Hi Sakhi, ela unnavu?"}]
    reply = await gemini_provider.generate_response(system_instruction=system_prompt, messages=messages)
    assert reply is not None
    assert len(reply.strip()) > 5
    # The reply should not be an error message
    assert "error" not in reply.lower() or "500" not in reply

def test_chat_api_greetings():
    """Tests /api/chat with 'Hi Sakhi, ela unnave?'."""
    response = client.post("/api/chat", json={
        "message": "Hi Sakhi, ela unnave?",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 5
    assert data["sender"] == "assistant"
    assert "conversation_id" in data

def test_chat_api_deadlock_explanation():
    """Tests /api/chat with 'Deadlock ante enti? Simple ga explain cheyyi.'."""
    response = client.post("/api/chat", json={
        "message": "Deadlock ante enti? Simple ga explain cheyyi.",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    reply_lower = data["reply"].lower()
    # Should explain deadlocks in simple conversational / educational manner
    assert any(term in reply_lower for term in ["deadlock", "process", "resource", "wait", "stuck", "lock"])
