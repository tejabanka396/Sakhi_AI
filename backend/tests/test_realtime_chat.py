import pytest
from unittest.mock import AsyncMock, patch
from fastapi.testclient import TestClient
from app.main import app
from app.services.web_search import SearchResponse, SearchResultItem
from app.voice.sanitizer import sanitize_text_for_tts

client = TestClient(app)

def test_chat_pure_date_today_direct():
    """Verify today's date query is answered directly with 100% accuracy and searched=False."""
    response = client.post("/api/chat", json={
        "message": "ఈరోజు తేది ఏంటి?",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert "ఈరోజు" in data["reply"]
    assert data.get("searched") is False
    assert data.get("sources") is None
    assert "voice_id" in data
    assert "gender" in data
    assert data.get("response_id") is not None

def test_chat_pure_time_direct():
    """Verify time query is answered directly with current IST time and searched=False."""
    response = client.post("/api/chat", json={
        "message": "ఇప్పుడు టైమ్ ఎంత?",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert any(term in data["reply"] for term in ["సమయం", "IST", "PM", "AM"])
    assert data.get("searched") is False

def test_chat_tomorrow_date_direct():
    """Verify tomorrow query is answered directly without Gemini."""
    response = client.post("/api/chat", json={
        "message": "రేపు ఏ తేదీ?",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "రేపు" in data["reply"]
    assert data.get("searched") is False

def test_chat_normal_query_does_not_search():
    """Verify standard educational queries have searched=False."""
    response = client.post("/api/chat", json={
        "message": "Explain binary search in simple terms.",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert data.get("searched") is False
    assert data.get("sources") is None
    assert len(data["reply"]) > 20

def test_chat_realtime_web_search_with_mocked_results():
    """Verify live search query calls search, passes sources, and preserves voice/gender."""
    mock_search_res = SearchResponse(
        query="latest AI news",
        results=[
            SearchResultItem(
                title="DeepMind announces Gemini updates",
                url="https://blog.google/technology/ai/gemini-updates-2026/",
                domain="blog.google",
                snippet="Google DeepMind introduced breakthrough AI reasoning capabilities today."
            ),
            SearchResultItem(
                title="AI Breakthroughs in September 2026",
                url="https://techcrunch.com/2026/09/ai-breakthroughs/",
                domain="techcrunch.com",
                snippet="New advances in open multimodal architectures were revealed this week."
            )
        ],
        provider="tavily",
        searched=True,
        timestamp="2026-09-20T12:00:00+05:30"
    )

    with patch("app.services.web_search.web_search_service.search", new_callable=AsyncMock) as mock_search:
        mock_search.return_value = mock_search_res

        response = client.post("/api/chat", json={
            "message": "What is the latest AI news today?",
            "input_type": "text"
        })
        assert response.status_code == 200
        data = response.json()

        # Web search fields
        assert data.get("searched") is True
        assert data.get("sources") is not None
        assert len(data["sources"]) == 2
        assert data["sources"][0]["domain"] == "blog.google"
        assert data["sources"][0]["url"] == "https://blog.google/technology/ai/gemini-updates-2026/"

        # Authoritative voice & gender preservation
        assert data.get("voice_id") is not None
        assert data.get("gender") in ["female", "male"]
        assert data.get("response_id") is not None

        # Verify speech_text never contains raw URLs
        speech_text = data.get("speech_text", "")
        assert "https://" not in speech_text
        assert "http://" not in speech_text
        assert "www." not in speech_text

def test_tts_sanitizer_removes_all_urls_and_sources():
    """Verify sanitize_text_for_tts scrubs URLs, source citations, and footnotes."""
    text_with_sources = (
        "Here is the latest news! The new model was released today. "
        "For more info visit https://example.com/news or www.tech.org/update. "
        "[Read more](https://docs.python.org/3/). [1, 2]\n\n"
        "Sources:\n"
        "1. https://example.com/news\n"
        "2. https://tech.org/update"
    )
    cleaned = sanitize_text_for_tts(text_with_sources)
    assert "https://" not in cleaned
    assert "http://" not in cleaned
    assert "www." not in cleaned
    assert "example.com" not in cleaned
    assert "Sources:" not in cleaned
    assert "[1, 2]" not in cleaned
    assert "Here is the latest news" in cleaned
