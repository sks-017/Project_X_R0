import os
import sys
from pathlib import Path
from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
TEST_DB = ROOT / "test_chat_gepulse.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SIMULATOR_ENABLED"] = "false"
os.environ["DEMO_MODE"] = "true"
os.environ["SECRET_KEY"] = "test-secret"
sys.path.insert(0, str(ROOT / "ingress-api"))

from app.main import app  # noqa: E402

def test_chat_assistant():
    with TestClient(app) as client:
        # Initial health check to seed database
        health = client.get("/api/v1/health")
        assert health.status_code == 200

        # Test health of a specific machine
        response = client.post("/api/v1/ai/chat", json={"message": "What is the health of IMM-01?"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "context_used" in data
        assert "IMM-01" in data["response"]
        assert any("IMM-01" in c for c in data["context_used"])

        # Test OEE queries
        response = client.post("/api/v1/ai/chat", json={"message": "What is our current OEE?"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "OEE" in data["response"]
        assert "Overall OEE" in data["context_used"][0]

        # Test defect troubleshooting
        response = client.post("/api/v1/ai/chat", json={"message": "How do I fix mold flash?"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "Flash" in data["response"]
        assert "troubleshooting guides - Flash" in data["context_used"][0]

        # Test fallback / help response
        response = client.post("/api/v1/ai/chat", json={"message": "Hello, who are you?"})
        assert response.status_code == 200
        data = response.json()
        assert "response" in data
        assert "TechMate AI Assistant" in data["response"]
        assert "TechMate System Help" in data["context_used"][0]
