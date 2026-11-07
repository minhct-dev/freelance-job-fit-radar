from pydantic import BaseModel, ConfigDict, Field


class Job(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: str = Field(min_length=1)
    title: str = Field(min_length=1)
    description: str = ""
    url: str | None = None
    skills: list[str] = Field(default_factory=list)
    budget_min: float | None = Field(default=None, ge=0)
    budget_max: float | None = Field(default=None, ge=0)
    currency: str | None = None
    posted_at: str | None = None


class Profile(BaseModel):
    skills: set[str] = Field(default_factory=set)


class RankedJob(Job):
    fit_score: int
    matched_skills: list[str]
    missing_skills: list[str]
    reasons: list[str]

