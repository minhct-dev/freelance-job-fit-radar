from app.services.database import (
    get_all_jobs,
    get_unalerted_jobs,
    init_db,
    is_alert_sent,
    record_alert,
    save_jobs,
)
from app.models.models import Job


def test_init_db_creates_tables(db_file) -> None:
    init_db(db_file)
    assert get_all_jobs(db_file) == []


def test_save_jobs_deduplicates_by_id(db_file) -> None:
    job1 = Job(id="job-1", title="Python Dev", skill_and_expertise=["Python"])
    job2 = Job(id="job-2", title="FastAPI Dev", skill_and_expertise=["FastAPI"])

    # First insert: 2 new jobs
    inserted = save_jobs([job1, job2], db_path=db_file)
    assert inserted == 2

    # Second insert with identical job1 and new job3: only 1 new job inserted
    job3 = Job(id="job-3", title="React Dev", skill_and_expertise=["React"])
    inserted_second = save_jobs([job1, job3], db_path=db_file)
    assert inserted_second == 1

    all_jobs = get_all_jobs(db_path=db_file)
    assert len(all_jobs) == 3
    ids = {job.id for job in all_jobs}
    assert ids == {"job-1", "job-2", "job-3"}


def test_alert_tracking_and_deduplication(db_file) -> None:
    job = Job(id="job-100", title="Backend Engineer", skill_and_expertise=["Python", "FastAPI"])
    save_jobs([job], db_path=db_file)

    # Initially unalerted
    assert not is_alert_sent("job-100", db_path=db_file)
    unalerted = get_unalerted_jobs(db_path=db_file)
    assert len(unalerted) == 1
    assert unalerted[0].id == "job-100"

    # Record successful alert
    record_alert("job-100", status="sent", db_path=db_file)

    # Now marked as sent and removed from unalerted list
    assert is_alert_sent("job-100", db_path=db_file)
    assert get_unalerted_jobs(db_path=db_file) == []


def test_failed_alert_allows_retry(db_file) -> None:
    job = Job(id="job-200", title="DevOps Engineer", skill_and_expertise=["Docker"])
    save_jobs([job], db_path=db_file)

    # Record failed alert attempt
    record_alert("job-200", status="failed", error_message="Network timeout", db_path=db_file)

    # Failed alert does NOT mark it as successfully sent
    assert not is_alert_sent("job-200", db_path=db_file)
    # Job is still considered unalerted for retry
    unalerted = get_unalerted_jobs(db_path=db_file)
    assert len(unalerted) == 1
    assert unalerted[0].id == "job-200"
