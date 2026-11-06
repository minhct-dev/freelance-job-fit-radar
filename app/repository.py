import json
from pathlib import Path

from app.models import Job

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "jobs.json"


def load_jobs(path: Path = DATA_FILE) -> list[Job]:
    """Load demo fixtures. Replace this with persistent storage in a later milestone."""
    with path.open(encoding="utf-8") as file:
        records = json.load(file)
    if not isinstance(records, list):
        raise ValueError("Job fixture must contain a JSON array")
    return [Job.model_validate(record) for record in records]
