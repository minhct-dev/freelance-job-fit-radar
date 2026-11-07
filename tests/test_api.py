from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint() -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_jobs_endpoint_returns_ranked_sample_fixtures() -> None:
    response = client.get("/jobs")
    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) >= 2
    # Verify ranked output structure
    first_job = jobs[0]
    assert "fit_score" in first_job
    assert "reasons" in first_job


def test_import_jobs_deduplication() -> None:
    payload = [
        {
            "id": "test-import-1",
            "title": "Data Engineer",
            "skill_and_expertise": ["Python", "SQL"],
        }
    ]
    # First import: 1 inserted
    res1 = client.post("/jobs", json=payload)
    assert res1.status_code == 200
    assert res1.json()["received"] == 1
    assert res1.json()["inserted"] == 1

    # Second import of identical job: 0 inserted, 1 skipped
    res2 = client.post("/jobs", json=payload)
    assert res2.status_code == 200
    assert res2.json()["received"] == 1
    assert res2.json()["inserted"] == 0
    assert res2.json()["skipped"] == 1


def test_get_alerts_endpoint() -> None:
    response = client.get("/alerts")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@patch("app.services.alert_service.send_job_alert", new_callable=AsyncMock)
def test_scan_alerts_endpoint(mock_send) -> None:
    response = client.post("/alerts/scan?min_score=50")
    assert response.status_code == 200
    data = response.json()
    assert "unalerted_scanned" in data
    assert "alerts_sent" in data


def test_scheduler_status_endpoint() -> None:
    response = client.get("/scheduler/status")
    assert response.status_code == 200
    data = response.json()
    assert "is_running" in data
    assert "interval_minutes" in data
    assert "min_fit_score" in data


@patch("app.services.alert_service.send_job_alert", new_callable=AsyncMock)
def test_scheduler_trigger_endpoint(mock_send) -> None:
    response = client.post("/scheduler/trigger")
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Scheduler cycle executed"
    assert "result" in data
