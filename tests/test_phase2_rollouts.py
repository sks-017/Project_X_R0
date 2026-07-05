"""Tests for Acron Phase 2 rollout endpoints."""
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


def _auth_headers(client: TestClient, role: str = "manager"):
    response = client.post("/api/v1/auth/demo-login", json={"role": role})
    assert response.status_code == 200
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def test_shift_calendar_and_target_standard_management():
    with TestClient(app) as client:
        headers = _auth_headers(client, "manager")

        response = client.get("/api/v1/factory/shift-calendars")
        assert response.status_code == 200
        assert len(response.json()) >= 3

        response = client.post(
            "/api/v1/factory/shift-calendars",
            json={
                "plant_code": "S7-PUNE-01",
                "shift_name": "D",
                "starts_at": "08:00",
                "ends_at": "16:00",
                "planned_downtime_minutes": 20,
                "active": True,
            },
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        calendars = client.get("/api/v1/factory/shift-calendars").json()
        assert any(item["shift_name"] == "D" and item["plant_code"] == "S7-PUNE-01" for item in calendars)

        response = client.post(
            "/api/v1/factory/target-standards",
            json={
                "equipment_id": "IMM-01",
                "shift_name": "A",
                "target_parts": 2100,
                "standard_cycle_time": 34.5,
                "quality_target": 0.99,
            },
            headers=headers,
        )
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        standards = client.get("/api/v1/factory/target-standards").json()
        assert any(item["equipment_id"] == "IMM-01" and item["target_parts"] == 2100 for item in standards)


def test_connector_probe_and_report_endpoints():
    with TestClient(app) as client:
        headers = _auth_headers(client, "maintenance")
        payload = {
            "name": "sim-line-a",
            "protocol": "simulator",
            "endpoint": "demo://line-a",
            "tag_map": {"cycle_time": "D100", "status": "D101"},
        }

        response = client.post("/api/v1/connectors", json=payload, headers=headers)
        assert response.status_code == 200
        assert response.json()["status"] == "ok"

        response = client.post("/api/v1/connectors/test", json=payload, headers=headers)
        assert response.status_code == 200
        probe = response.json()
        assert probe["ok"] is True
        assert probe["protocol"] == "simulator"
        assert "sample" in probe

        report = client.get("/api/v1/reports/oee?scope=shift")
        assert report.status_code == 200
        data = report.json()
        assert data["scope"] == "shift"
        assert "summary" in data
        assert isinstance(data["machines"], list)
        assert data["summary"]["machines"] == len(data["machines"])
        assert "oee" in data["summary"]
