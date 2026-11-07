import json
from pathlib import Path

from app.services.database import get_all_jobs, save_jobs
from app.models.models import Job

DATA_FILE = Path(__file__).resolve().parent.parent.parent / "data" / "jobs.json"


def load_jobs_from_fixture(path: Path = DATA_FILE) -> list[Job]:
    """Load raw job fixtures from a JSON file."""
    with path.open(encoding="utf-8") as file:
        records = json.load(file)
    if not isinstance(records, list):
        raise ValueError("Job fixture must contain a JSON array")
    return [Job.model_validate(record) for record in records]


def load_jobs(db_path: str | None = None) -> list[Job]:
    """
    Load jobs from SQLite.
    If the database is currently empty and the fixture file exists,
    seed the database with the sample fixtures.
    """
    jobs = get_all_jobs(db_path)
    if not jobs and DATA_FILE.exists():
        fixture_jobs = load_jobs_from_fixture(DATA_FILE)
        save_jobs(fixture_jobs, db_path)
        jobs = get_all_jobs(db_path)
    return jobs


