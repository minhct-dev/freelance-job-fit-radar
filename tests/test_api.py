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
    assert len(jobs) == 2
    assert jobs[0]["id"] == "demo-api-001"
    assert jobs[0]["fit_score"] == 100
    assert jobs[0]["reasons"] == ["Matched skills: fastapi, python, rest api, sql"]
