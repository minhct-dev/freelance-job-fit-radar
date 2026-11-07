from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, Query

from app.models.models import Job, Profile, RankedJob
from app.services.alert_service import scan_and_alert_jobs
from app.services.database import get_alerts, save_jobs
from app.services.repository import load_jobs
from app.services.scheduler import scheduler
from app.services.scoring import rank_job
from app.utils.settings import settings

# Demo profile only; user-configurable profiles can be added in a later milestone.
PROFILE = Profile(skills={"python", "fastapi", "rest api", "sql"})


@asynccontextmanager
async def lifespan(app: FastAPI):
    if settings.scheduler_enabled:
        scheduler.start()
    yield
    if scheduler.is_running:
        await scheduler.stop()


app = FastAPI(
    title="Freelance Job Fit Radar",
    version="0.3.0",
    lifespan=lifespan,
)


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs", response_model=list[RankedJob])
def list_jobs() -> list[RankedJob]:
    """Retrieve all jobs from SQLite and rank them against the current profile."""
    jobs = [rank_job(job, PROFILE) for job in load_jobs()]
    return sorted(jobs, key=lambda job: job.fit_score, reverse=True)


@app.post("/jobs")
def import_jobs(jobs: list[Job]) -> dict[str, int]:
    """
    Import new jobs into SQLite with automatic deduplication.
    Existing jobs with the same ID will be skipped.
    """
    inserted = save_jobs(jobs)
    return {"received": len(jobs), "inserted": inserted, "skipped": len(jobs) - inserted}


@app.get("/alerts")
def list_alerts() -> list[dict[str, Any]]:
    """View alert history recorded in SQLite."""
    return get_alerts()


@app.post("/alerts/scan")
async def trigger_alert_scan(
    min_score: int = Query(default=70, ge=0, le=100)
) -> dict[str, Any]:
    """
    Scan unalerted jobs, score them, and send Telegram alerts for matches >= min_score.
    Deduplication prevents sending the same job twice.
    """
    return await scan_and_alert_jobs(profile=PROFILE, min_fit_score=min_score)


@app.get("/scheduler/status")
def get_scheduler_status() -> dict[str, Any]:
    """Get the current running status and health metrics of the background scheduler."""
    return scheduler.get_status()


@app.post("/scheduler/start")
def start_scheduler() -> dict[str, Any]:
    """Start the periodic background job scanning task."""
    scheduler.start()
    return {"message": "Scheduler started", "status": scheduler.get_status()}


@app.post("/scheduler/stop")
async def stop_scheduler() -> dict[str, Any]:
    """Stop the periodic background job scanning task."""
    await scheduler.stop()
    return {"message": "Scheduler stopped", "status": scheduler.get_status()}


@app.post("/scheduler/trigger")
async def trigger_scheduler_cycle() -> dict[str, Any]:
    """Manually trigger one scheduler cycle immediately."""
    result = await scheduler.run_once()
    return {"message": "Scheduler cycle executed", "result": result}
