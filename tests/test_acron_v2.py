"""Tests for Acron analytics and AI endpoints."""
import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
TEST_DB = ROOT / "test_acron.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SIMULATOR_ENABLED"] = "false"
os.environ["DEMO_MODE"] = "true"
os.environ["SECRET_KEY"] = "test-secret"
sys.path.insert(0, str(ROOT / "ingress-api"))

from app.main import app  # noqa: E402


def test_analytics_endpoints():
    with TestClient(app) as client:
        # OEE trend
        resp = client.get("/api/v1/analytics/oee-trend?hours=1")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

        # Downtime summary
        resp = client.get("/api/v1/analytics/downtime-summary?hours=1")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

        # Dashboard stats
        resp = client.get("/api/v1/analytics/summary")
        assert resp.status_code == 200
        data = resp.json()
        assert "total_assets" in data
        assert data["total_assets"] >= 30


def test_ai_endpoints():
    with TestClient(app) as client:
        # Anomaly detection
        resp = client.get("/api/v1/ai/anomalies?hours=1")
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

        # Health scores
        resp = client.get("/api/v1/ai/health-scores?hours=1")
        assert resp.status_code == 200
        scores = resp.json()
        assert isinstance(scores, list)
        assert len(scores) >= 30
        # Each score should have the expected fields
        for s in scores:
            assert "equipment_id" in s
            assert "health_score" in s
            assert 0 <= s["health_score"] <= 100


def test_brand_is_acron():
    with TestClient(app) as client:
        resp = client.get("/health")
        assert resp.status_code == 200
        brand = resp.json()["brand"]
        assert brand["name"] == "Acron"
        assert brand["owner"] == "S7 Corp"
        assert "intelligence" in brand["tagline"].lower()
