import logging
from typing import Any

from app.services.database import get_unalerted_jobs, record_alert
from app.models.models import Profile, RankedJob
from app.services.notifications import format_job_alert, send_job_alert
from app.services.scoring import rank_job

logger = logging.getLogger(__name__)


async def scan_and_alert_jobs(
    profile: Profile,
    min_fit_score: int = 70,
    db_path: str | None = None,
) -> dict[str, Any]:
    """
    Scans unalerted jobs from SQLite, ranks them against the profile,
    and sends Telegram alerts for jobs meeting min_fit_score.
    Records alert status ('sent' or 'failed') to avoid repeated notifications.
    """
    unalerted = get_unalerted_jobs(db_path)
    sent_count = 0
    failed_count = 0
    skipped_count = 0
    details: list[dict[str, Any]] = []

    for job in unalerted:
        ranked: RankedJob = rank_job(job, profile)
        if ranked.fit_score >= min_fit_score:
            alert_text = format_job_alert(ranked)
            try:
                await send_job_alert(alert_text)
                record_alert(job.id, status="sent", db_path=db_path)
                sent_count += 1
                details.append(
                    {"job_id": job.id, "status": "sent", "fit_score": ranked.fit_score}
                )
            except Exception as e:
                error_msg = str(e)
                logger.error(f"Failed to send alert for job {job.id}: {error_msg}")
                record_alert(
                    job.id, status="failed", error_message=error_msg, db_path=db_path
                )
                failed_count += 1
                details.append(
                    {"job_id": job.id, "status": "failed", "error": error_msg}
                )
        else:
            skipped_count += 1

    return {
        "unalerted_scanned": len(unalerted),
        "alerts_sent": sent_count,
        "alerts_failed": failed_count,
        "skipped_low_score": skipped_count,
        "details": details,
    }

