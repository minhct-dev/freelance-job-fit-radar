from unittest.mock import AsyncMock, patch

import pytest

from app.services.alert_service import scan_and_alert_jobs
from app.services.database import get_alerts, is_alert_sent, save_jobs
from app.models.models import Job, Profile


@pytest.mark.asyncio
@patch("app.services.alert_service.send_job_alert", new_callable=AsyncMock)
async def test_scan_and_alert_deduplication(mock_send, tmp_path) -> None:
    db_file = str(tmp_path / "test.db")
    profile = Profile(skills={"python", "fastapi"})

    job_high_fit = Job(
        id="match-1",
        title="Python FastAPI API",
        skill_and_expertise=["Python", "FastAPI"],
    )
    job_low_fit = Job(
        id="low-1",
        title="Flutter Mobile App",
        skill_and_expertise=["Flutter", "Dart"],
    )

    save_jobs([job_high_fit, job_low_fit], db_path=db_file)

    # First scan: high fit matches and alert is sent
    result1 = await scan_and_alert_jobs(profile=profile, min_fit_score=70, db_path=db_file)

    assert result1["unalerted_scanned"] == 2
    assert result1["alerts_sent"] == 1
    assert result1["skipped_low_score"] == 1
    assert mock_send.call_count == 1
    assert is_alert_sent("match-1", db_path=db_file)

    # Second scan: match-1 was already sent, so it is skipped (0 alerts sent)
    result2 = await scan_and_alert_jobs(profile=profile, min_fit_score=70, db_path=db_file)

    assert result2["unalerted_scanned"] == 1  # only low-1 remains unalerted
    assert result2["alerts_sent"] == 0
    assert mock_send.call_count == 1  # no new send calls!

    alerts = get_alerts(db_path=db_file)
    assert len(alerts) == 1
    assert alerts[0]["job_id"] == "match-1"
    assert alerts[0]["status"] == "sent"


