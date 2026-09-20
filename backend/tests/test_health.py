from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"
    assert data["service"] == "Sakhi AI Backend"
    assert "version" in data
    assert "database" in data
    # Verify no secrets or credentials leaked in response
    assert "password" not in str(data).lower()
    assert "secret" not in str(data).lower()

def test_root():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data
    assert "Sakhi" in data["message"]
