from fastapi import FastAPI

from app.models import Profile, RankedJob
from app.repository import load_jobs
from app.scoring import rank_job

app = FastAPI(title="Freelance Job Fit Radar", version="0.1.0")

# Demo profile only; user-configurable profiles are a later milestone.
PROFILE = Profile(skills={"python", "fastapi", "rest api", "sql"})


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/jobs", response_model=list[RankedJob])
def list_jobs() -> list[RankedJob]:
    jobs = [rank_job(job, PROFILE) for job in load_jobs()]
    return sorted(jobs, key=lambda job: job.fit_score, reverse=True)
