import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator

from app.models.models import Job
from app.utils.settings import settings


def parse_db_path(db_url: str | None = None) -> str:
    url = db_url or settings.database_url
    if url.startswith("sqlite:///"):
        return url.replace("sqlite:///", "", 1)
    if url.startswith("sqlite://"):
        return url.replace("sqlite://", "", 1)
    return url


@contextmanager
def get_connection(db_path: str | None = None) -> Generator[sqlite3.Connection, None, None]:
    path = parse_db_path(db_path)
    if path != ":memory:":
        parent = Path(path).resolve().parent
        parent.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db(db_path: str | None = None) -> None:
    """Create jobs and alerts tables if they do not exist."""
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                summary TEXT DEFAULT '',
                url TEXT,
                skill_and_expertise TEXT DEFAULT '[]',
                client_review INTEGER DEFAULT 0,
                client_evaluate REAL DEFAULT 0.0,
                fixed_price REAL,
                hourly_price REAL,
                posted_at TEXT,
                created_at TEXT NOT NULL
            );
            """
        )
        cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id TEXT NOT NULL,
                sent_at TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                FOREIGN KEY (job_id) REFERENCES jobs (id) ON DELETE CASCADE
            );
            """
        )
        cursor.execute(
            """
            CREATE INDEX IF NOT EXISTS idx_alerts_job_status ON alerts (job_id, status);
            """
        )


def _row_to_job(row: sqlite3.Row) -> Job:
    skills_raw = row["skill_and_expertise"]
    try:
        skills = json.loads(skills_raw) if skills_raw else []
    except (json.JSONDecodeError, TypeError):
        skills = []

    return Job(
        id=row["id"],
        title=row["title"],
        summary=row["summary"] or "",
        url=row["url"],
        skill_and_expertise=skills,
        client_review=row["client_review"],
        client_evaluate=row["client_evaluate"],
        fixed_price=row["fixed_price"],
        hourly_price=row["hourly_price"],
        posted_at=row["posted_at"],
    )


def save_jobs(jobs: list[Job], db_path: str | None = None) -> int:
    """
    Insert jobs into the database.
    Skips jobs that already exist (deduplication on job.id).
    Returns the count of newly inserted jobs.
    """
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    inserted = 0
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        for job in jobs:
            cursor.execute(
                """
                INSERT OR IGNORE INTO jobs (
                    id, title, summary, url, skill_and_expertise,
                    client_review, client_evaluate, fixed_price, hourly_price, posted_at, created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    job.id,
                    job.title,
                    job.summary,
                    job.url,
                    json.dumps(job.skill_and_expertise),
                    job.client_review,
                    job.client_evaluate,
                    job.fixed_price,
                    job.hourly_price,
                    job.posted_at,
                    now,
                ),
            )
            if cursor.rowcount > 0:
                inserted += 1
    return inserted


def get_all_jobs(db_path: str | None = None) -> list[Job]:
    """Retrieve all jobs ordered by posted_at and created_at descending."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs ORDER BY posted_at DESC, created_at DESC")
        rows = cursor.fetchall()
        return [_row_to_job(row) for row in rows]


def get_job(job_id: str, db_path: str | None = None) -> Job | None:
    """Retrieve a single job by id."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        return _row_to_job(row) if row else None


def is_alert_sent(job_id: str, db_path: str | None = None) -> bool:
    """Check if an alert with status='sent' already exists for this job."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT 1 FROM alerts WHERE job_id = ? AND status = 'sent' LIMIT 1",
            (job_id,),
        )
        return cursor.fetchone() is not None


def record_alert(
    job_id: str,
    status: str = "sent",
    error_message: str | None = None,
    db_path: str | None = None,
) -> None:
    """Record an alert attempt (sent, failed, etc.) in the database."""
    init_db(db_path)
    now = datetime.now(timezone.utc).isoformat()
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO alerts (job_id, sent_at, status, error_message)
            VALUES (?, ?, ?, ?)
            """,
            (job_id, now, status, error_message),
        )


def get_alerts(db_path: str | None = None) -> list[dict]:
    """Retrieve all alert records ordered from newest to oldest."""
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT id, job_id, sent_at, status, error_message
            FROM alerts
            ORDER BY id DESC
            """
        )
        rows = cursor.fetchall()
        return [
            {
                "id": row["id"],
                "job_id": row["job_id"],
                "sent_at": row["sent_at"],
                "status": row["status"],
                "error_message": row["error_message"],
            }
            for row in rows
        ]


def get_unalerted_jobs(db_path: str | None = None) -> list[Job]:
    """
    Retrieve all jobs that do not have a successful ('sent') alert record.
    Used by the scanner to avoid re-alerting.
    """
    init_db(db_path)
    with get_connection(db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT j.* FROM jobs j
            WHERE NOT EXISTS (
                SELECT 1 FROM alerts a
                WHERE a.job_id = j.id AND a.status = 'sent'
            )
            ORDER BY j.posted_at DESC, j.created_at DESC
            """
        )
        rows = cursor.fetchall()
        return [_row_to_job(row) for row in rows]
