"""
ClearDesk backend tests
- GET /api/dashboard : seeded project, stats, insight, docket
- PATCH /api/docket/{item_id} : status update + persistence
- GET /api/status, POST /api/status : basic health
"""
import os
import pytest
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parents[2] / "frontend" / ".env")
BASE_URL = os.environ['REACT_APP_BACKEND_URL'].rstrip('/')
API = f"{BASE_URL}/api"


@pytest.fixture(scope="module")
def api_client():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


# --- Dashboard endpoint ---
class TestDashboard:
    def test_dashboard_status(self, api_client):
        r = api_client.get(f"{API}/dashboard", timeout=15)
        assert r.status_code == 200, r.text

    def test_dashboard_shape(self, api_client):
        r = api_client.get(f"{API}/dashboard", timeout=15)
        data = r.json()
        # top-level keys
        for k in ("project", "stats", "docket", "insight"):
            assert k in data, f"missing key: {k}"

        # project
        assert data["project"]["name"] == "West Quay Redevelopment"
        assert data["project"]["code"] == "WQ-042"
        assert data["project"]["contract"] == "NEC4 ECC Option C"

        # stats
        stats = data["stats"]
        for k in ("needs_review", "urgent", "waiting", "open_projects"):
            assert k in stats
            assert isinstance(stats[k], int)
        assert stats["needs_review"] == 12
        assert stats["urgent"] == 3

        # insight
        insight = data["insight"]
        assert "title" in insight and "body" in insight
        assert isinstance(insight["items"], list) and len(insight["items"]) == 3

        # docket
        docket = data["docket"]
        assert isinstance(docket, list) and len(docket) == 4
        ids = [d["id"] for d in docket]
        assert "cor-1048" in ids
        for item in docket:
            for f in ("id", "priority", "type", "subject", "sender", "project",
                      "received", "deadline", "risk", "risk_detail", "excerpt",
                      "attachment", "status"):
                assert f in item, f"docket item missing {f}"


# --- Docket PATCH endpoint ---
class TestDocketPatch:
    def test_patch_updates_status_persists_in_response(self, api_client):
        payload = {"status": "Reviewed"}
        r = api_client.patch(f"{API}/docket/cor-1048", json=payload, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["id"] == "cor-1048"
        assert body["status"] == "Reviewed"

    def test_patch_persists_across_get(self, api_client):
        # Set a distinct value
        marker = "In progress"
        r = api_client.patch(f"{API}/docket/cor-1047", json={"status": marker}, timeout=15)
        assert r.status_code == 200
        # Verify via GET /dashboard
        r2 = api_client.get(f"{API}/dashboard", timeout=15)
        assert r2.status_code == 200
        item = next(x for x in r2.json()["docket"] if x["id"] == "cor-1047")
        assert item["status"] == marker
        # Restore
        api_client.patch(f"{API}/docket/cor-1047", json={"status": "Waiting on QS"}, timeout=15)

    def test_patch_unknown_id_returns_error_payload(self, api_client):
        r = api_client.patch(f"{API}/docket/does-not-exist",
                             json={"status": "Reviewed"}, timeout=15)
        # Current impl returns 200 with {"error": ...}. Accept either behaviour but assert error signal.
        if r.status_code == 200:
            assert "error" in r.json()
        else:
            assert r.status_code in (404, 400)

    def test_patch_missing_status_returns_422(self, api_client):
        r = api_client.patch(f"{API}/docket/cor-1048", json={}, timeout=15)
        assert r.status_code == 422


# --- Status check endpoints (basic sanity) ---
class TestStatus:
    def test_root(self, api_client):
        r = api_client.get(f"{API}/", timeout=15)
        assert r.status_code == 200
        assert r.json().get("message") == "Hello World"

    def test_create_and_list_status(self, api_client):
        r = api_client.post(f"{API}/status", json={"client_name": "TEST_pytest"}, timeout=15)
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["client_name"] == "TEST_pytest"
        assert "id" in body and "timestamp" in body

        r2 = api_client.get(f"{API}/status", timeout=15)
        assert r2.status_code == 200
        assert any(x["client_name"] == "TEST_pytest" for x in r2.json())
