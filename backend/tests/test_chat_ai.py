import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.database.database import SessionLocal
from app.database.models import User, FriendProfile, Memory

client = TestClient(app)

def test_chat_casual_telugu():
    response = client.post("/api/chat", json={
        "message": "Hi Sakhi, ela unnavu? 😊",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 5
    assert "conversation_id" in data
    assert "message_id" in data
    assert data["sender"] == "assistant"

def test_chat_study_question():
    response = client.post("/api/chat", json={
        "message": "DBMS lo deadlocks ante enti? 4 conditions cheppu.",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    reply_lower = data["reply"].lower()
    # Should explain deadlocks and condition terms
    assert any(term in reply_lower for term in ["deadlock", "mutual exclusion", "hold", "wait", "preemption", "process"])

def test_chat_memory_extraction():
    db = SessionLocal()
    try:
        # Send message with explicit memory trigger
        response = client.post("/api/chat", json={
            "message": "Remember that my favorite programming language is Python and I love AI.",
            "input_type": "text"
        })
        assert response.status_code == 200

        # Verify memory stored in MySQL
        user = db.query(User).filter_by(email="teja@sakhi.local").first()
        assert user is not None
        memories = db.query(Memory).filter_by(user_id=user.id).all()
        assert len(memories) > 0
        memory_texts = " ".join([m.memory_text for m in memories])
        assert "favorite programming language is Python" in memory_texts or "Python" in memory_texts
    finally:
        db.close()

def test_chat_pure_english():
    response = client.post("/api/chat", json={
        "message": "Explain the concept of recursion in computer science with a simple example.",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 20
    assert data.get("language") == "english"
    # Should not contain Telugu script
    has_telugu_script = any('\u0c00' <= char <= '\u0c7f' for char in data["reply"])
    assert not has_telugu_script

def test_chat_pure_telugu():
    response = client.post("/api/chat", json={
        "message": "నమస్కారం, ఈ రోజు నా స్నేహితుడికి పుట్టినరోజు. శుభాకాంక్షలు ఎలా చెప్పాలి?",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 10
    assert data.get("language") == "telugu"
    # Should contain Telugu script
    has_telugu_script = any('\u0c00' <= char <= '\u0c7f' for char in data["reply"])
    assert has_telugu_script

def test_chat_mixed_tanglish():
    response = client.post("/api/chat", json={
        "message": "Naku Python programming lo functions ela create cheyyalo simple ga cheppu.",
        "input_type": "text"
    })
    assert response.status_code == 200
    data = response.json()
    assert "reply" in data
    assert len(data["reply"]) > 15
    # Should explain python functions in conversational Tanglish
    assert any(term in data["reply"].lower() for term in ["def", "function", "return", "python"])

