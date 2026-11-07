import asyncio
import logging
from datetime import datetime, timezone
from typing import Any

from app.models.models import Profile
from app.services.alert_service import scan_and_alert_jobs
from app.services.database import save_jobs
from app.services.repository import DATA_FILE, load_jobs_from_fixture
from app.utils.settings import settings

logger = logging.getLogger(__name__)

DEFAULT_PROFILE = Profile(skills={"python", "fastapi", "rest api", "sql"})


class JobScheduler:
    """
    Background worker that runs periodically to:
    1. Read jobs from source fixture (data/jobs.json) and save to SQLite (with deduplication).
    2. Rank unalerted jobs against the profile via scoring.py.
    3. If fit_score >= threshold (e.g. 70%) and not yet alerted, send Telegram alert and record in SQLite.
    """

    def __init__(
        self,
        profile: Profile | None = None,
        interval_seconds: int | None = None,
        min_fit_score: int | None = None,
        db_path: str | None = None,
        sync_fixture: bool = True,
    ) -> None:
        self.profile = profile or DEFAULT_PROFILE
        self.interval_seconds = (
            interval_seconds
            if interval_seconds is not None
            else settings.scan_interval_minutes * 60
        )
        self.min_fit_score = (
            min_fit_score
            if min_fit_score is not None
            else settings.min_fit_score
        )
        self.db_path = db_path
        self.sync_fixture = sync_fixture
        self._task: asyncio.Task[None] | None = None
        self._stop_event = asyncio.Event()
        self.last_run: datetime | None = None
        self.last_result: dict[str, Any] | None = None
        self.run_count: int = 0

    @property
    def is_running(self) -> bool:
        return self._task is not None and not self._task.done()

    async def run_once(self) -> dict[str, Any]:
        """
        Execute a single scan cycle:
        1. Ingest new jobs from fixture file if it exists and sync_fixture is True.
        2. Match unalerted jobs, score them, and alert if score >= threshold.
        """
        ingested_count = 0
        if self.sync_fixture and DATA_FILE.exists():
            try:
                fixture_jobs = load_jobs_from_fixture(DATA_FILE)
                ingested_count = save_jobs(fixture_jobs, db_path=self.db_path)
                if ingested_count > 0:
                    logger.info(f"Ingested {ingested_count} new jobs from fixture into database.")
            except Exception as e:
                logger.warning(f"Could not ingest jobs from fixture: {e}")

        scan_result = await scan_and_alert_jobs(
            profile=self.profile,
            min_fit_score=self.min_fit_score,
            db_path=self.db_path,
        )

        self.last_run = datetime.now(timezone.utc)
        self.last_result = {
            "timestamp": self.last_run.isoformat(),
            "jobs_ingested": ingested_count,
            **scan_result,
        }
        self.run_count += 1
        logger.info(
            f"Scheduler cycle #{self.run_count} completed: "
            f"scanned={scan_result['unalerted_scanned']}, "
            f"sent={scan_result['alerts_sent']}, "
            f"skipped={scan_result['skipped_low_score']}, "
            f"failed={scan_result['alerts_failed']}"
        )
        return self.last_result

    async def _loop(self) -> None:
        logger.info(
            f"Scheduler loop started (interval={self.interval_seconds}s, "
            f"min_fit_score={self.min_fit_score}%)."
        )
        while not self._stop_event.is_set():
            try:
                await self.run_once()
            except Exception as e:
                logger.error(f"Unexpected error during scheduler run_once: {e}", exc_info=True)

            try:
                # Wait for interval or until stopped
                await asyncio.wait_for(self._stop_event.wait(), timeout=self.interval_seconds)
            except TimeoutError:
                # Timeout elapsed without stop_event -> continue loop
                pass

        logger.info("Scheduler loop exited.")

    def start(self) -> None:
        """Start the background periodic task if not already running."""
        if self.is_running:
            logger.warning("Scheduler is already running.")
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(self._loop())
        logger.info("Scheduler task created and started.")

    async def stop(self) -> None:
        """Gracefully stop the background periodic task."""
        if not self.is_running:
            return

        self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except (TimeoutError, asyncio.CancelledError):
                if self._task and not self._task.done():
                    self._task.cancel()
            self._task = None
        logger.info("Scheduler task stopped.")

    def get_status(self) -> dict[str, Any]:
        """Get current scheduler health and status metrics."""
        return {
            "is_running": self.is_running,
            "interval_seconds": self.interval_seconds,
            "interval_minutes": round(self.interval_seconds / 60, 2),
            "min_fit_score": self.min_fit_score,
            "run_count": self.run_count,
            "last_run": self.last_run.isoformat() if self.last_run else None,
            "last_result": self.last_result,
        }


# Global singleton scheduler instance
scheduler = JobScheduler()
