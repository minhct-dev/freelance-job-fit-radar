import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from app.models.models import Job, Profile
from app.services.database import get_alerts, is_alert_sent, save_jobs
from app.services.scheduler import JobScheduler


@pytest.mark.asyncio
@patch("app.services.alert_service.send_job_alert", new_callable=AsyncMock)
async def test_scheduler_run_once_scans_and_alerts(mock_send, db_file) -> None:
    profile = Profile(skills={"python", "fastapi"})

    job_high = Job(
        id="sched-job-1",
        title="Senior FastAPI Backend Developer",
        skill_and_expertise=["Python", "FastAPI"],
        fixed_price=500.0,
    )
    job_low = Job(
        id="sched-job-2",
        title="Flutter Mobile Engineer",
        skill_and_expertise=["Flutter", "Dart"],
        hourly_price=30.0,
    )
    save_jobs([job_high, job_low], db_path=db_file)

    scheduler = JobScheduler(
        profile=profile,
        interval_seconds=60,
        min_fit_score=70,
        db_path=db_file,
        sync_fixture=False,
    )

    result = await scheduler.run_once()

    assert result["unalerted_scanned"] == 2
    assert result["alerts_sent"] == 1
    assert result["skipped_low_score"] == 1
    assert mock_send.call_count == 1
    assert is_alert_sent("sched-job-1", db_path=db_file)

    # Check scheduler status tracking
    status = scheduler.get_status()
    assert status["run_count"] == 1
    assert status["last_run"] is not None
    assert status["min_fit_score"] == 70

    # Second run_once on same db: duplicate alert is skipped
    result_second = await scheduler.run_once()
    assert result_second["alerts_sent"] == 0
    assert mock_send.call_count == 1  # No additional message sent


@pytest.mark.asyncio
async def test_scheduler_start_stop_lifecycle() -> None:
    scheduler = JobScheduler(interval_seconds=1)

    assert not scheduler.is_running
    scheduler.start()
    assert scheduler.is_running

    # Starting again while already running should be a no-op
    scheduler.start()
    assert scheduler.is_running

    await asyncio.sleep(0.05)
    await scheduler.stop()
    assert not scheduler.is_running
