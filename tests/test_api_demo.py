import os
import sys
from pathlib import Path

from fastapi.testclient import TestClient

ROOT = Path(__file__).resolve().parents[1]
TEST_DB = ROOT / "test_gepulse.db"
if TEST_DB.exists():
    TEST_DB.unlink()

os.environ["DATABASE_URL"] = f"sqlite:///{TEST_DB}"
os.environ["SIMULATOR_ENABLED"] = "false"
os.environ["DEMO_MODE"] = "true"
os.environ["SECRET_KEY"] = "test-secret"
sys.path.insert(0, str(ROOT / "ingress-api"))

from app.main import app  # noqa: E402


def test_health_and_seeded_machine_master():
    with TestClient(app) as client:
        health = client.get("/api/v1/health")
        assert health.status_code == 200
        assert health.json()["checks"]["api"]["status"] == "up"

        machines = client.get("/api/v1/factory/machines")
        assert machines.status_code == 200
        assert len(machines.json()) >= 30


def test_demo_login_reset_and_oee_flow():
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/demo-login", json={"role": "manager"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        reset = client.post("/api/v1/demo/reset", headers=headers)
        assert reset.status_code == 200

        downtime = client.post(
            "/api/v1/downtime",
            json={
                "equipment_id": "IMM-01",
                "reason_code": "MACHINE_STOP",
                "category": "machine stop",
                "minutes": 12,
                "comment": "Test stop",
            },
            headers=headers,
        )
        assert downtime.status_code == 200

        oee = client.get("/api/v1/oee")
        assert oee.status_code == 200
        imm_01 = [item for item in oee.json() if item["equipment_id"] == "IMM-01"][0]
        assert imm_01["availability"] < 100
        assert {"availability", "performance", "quality", "oee"} <= set(imm_01)


def test_operator_cannot_reset_demo_data():
    with TestClient(app) as client:
        login = client.post("/api/v1/auth/demo-login", json={"role": "operator"})
        headers = {"Authorization": f"Bearer {login.json()['access_token']}"}
        reset = client.post("/api/v1/demo/reset", headers=headers)
        assert reset.status_code == 403
