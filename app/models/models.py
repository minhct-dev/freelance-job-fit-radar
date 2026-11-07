from pydantic import BaseModel, ConfigDict, Field


class Job(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    summary: str = ""
    url: str | None = None
    skill_and_expertise: list[str] = Field(default_factory=list)
    client_review: int = 0
    client_evaluate: float = 0.0
    fixed_price: float | None = None
    hourly_price: float | None = None
    posted_at: str | None = None


class Profile(BaseModel):
    skills: set[str] = Field(default_factory=set)


class RankedJob(Job):
    fit_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    reasons: list[str]
