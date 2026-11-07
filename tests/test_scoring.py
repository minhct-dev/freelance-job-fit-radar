from app.models.models import Job, Profile
from app.services.scoring import rank_job


def test_rank_job_explains_exact_skill_overlap() -> None:
    result = rank_job(
        Job(id="1", title="API", skill_and_expertise=["Python", "FastAPI"]),
        Profile(skills={"python", "fastapi", "sql", "rest api"}),
    )

    assert result.fit_score == 50
    assert result.matched_skills == ["fastapi", "python"]
    assert result.missing_skills == ["rest api", "sql"]
    assert result.reasons[0] == "Matched skills: fastapi, python"


def test_empty_profile_has_zero_score() -> None:
    result = rank_job(Job(id="1", title="Any job"), Profile())

    assert result.fit_score == 0
    assert result.matched_skills == []
    assert result.missing_skills == []


