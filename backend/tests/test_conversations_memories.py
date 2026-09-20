import pytest
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_conversations_and_memories_lifecycle():
    # 1. Register User 1
    u1_res = client.post("/api/auth/register", json={
        "name": "Conv Tester 1",
        "email": f"tester1_{uuid.uuid4().hex[:6]}@example.com",
        "password": "Password123!"
    })
    token1 = u1_res.json()["access_token"]

    # 2. Register User 2
    u2_res = client.post("/api/auth/register", json={
        "name": "Conv Tester 2",
        "email": f"tester2_{uuid.uuid4().hex[:6]}@example.com",
        "password": "Password123!"
    })
    token2 = u2_res.json()["access_token"]

    # 3. User 1 sends message
    chat_res = client.post("/api/chat", headers={"Authorization": f"Bearer {token1}"}, json={
        "message": "Hello Sakhi, tell me a Telugu proverb.",
        "input_type": "text"
    })
    assert chat_res.status_code == 200
    conv_id = chat_res.json()["conversation_id"]

    # 4. User 1 lists conversations
    list_res = client.get("/api/conversations", headers={"Authorization": f"Bearer {token1}"})
    assert list_res.status_code == 200
    convs = list_res.json()
    assert len(convs) >= 1
    assert any(c["id"] == conv_id for c in convs)

    # 5. User 1 views conversation details
    detail_res = client.get(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token1}"})
    assert detail_res.status_code == 200
    assert len(detail_res.json()["messages"]) >= 2

    # 6. CRITICAL USER ISOLATION TEST: User 2 attempts to view User 1's conversation -> MUST RETURN 403!
    unauthorized_res = client.get(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token2}"})
    assert unauthorized_res.status_code == 403  # Strictly blocked!

    # 7. User 1 renames conversation
    rename_res = client.put(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token1}"}, json={
        "title": "Telugu Samethalu Chat"
    })
    assert rename_res.status_code == 200
    assert rename_res.json()["title"] == "Telugu Samethalu Chat"

    # 8. Memory lifecycle
    mem_add = client.post("/api/memories", headers={"Authorization": f"Bearer {token1}"}, json={
        "memory_text": "User enjoys reading Telugu poetry and proverbs.",
        "category": "preference"
    })
    assert mem_add.status_code == 200
    mem_id = mem_add.json()["id"]

    # List memories
    mem_list = client.get("/api/memories", headers={"Authorization": f"Bearer {token1}"})
    assert mem_list.status_code == 200
    assert len(mem_list.json()) >= 1

    # User 2 cannot see User 1's memories
    mem_u2 = client.get("/api/memories", headers={"Authorization": f"Bearer {token2}"})
    assert mem_u2.status_code == 200
    assert not any(m["id"] == mem_id for m in mem_u2.json())

    # Delete single memory
    del_mem = client.delete(f"/api/memories/{mem_id}", headers={"Authorization": f"Bearer {token1}"})
    assert del_mem.status_code == 200

    # 9. Delete conversation
    del_conv = client.delete(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token1}"})
    assert del_conv.status_code == 200

    # Verify conversation is gone
    not_found = client.get(f"/api/conversations/{conv_id}", headers={"Authorization": f"Bearer {token1}"})
    assert not_found.status_code == 404
