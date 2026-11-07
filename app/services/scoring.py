from app.models.models import Job, Profile, RankedJob


def rank_job(job: Job, profile: Profile) -> RankedJob:
    """Score exact skill overlap; this is not a probability of winning a job."""
    def normalize(values: set[str] | list[str]) -> set[str]:
        return {value.strip().casefold() for value in values if value.strip()}

    job_skills = normalize(job.skill_and_expertise)
    profile_skills = normalize(profile.skills)
    matched = sorted(job_skills & profile_skills)
    missing = sorted(profile_skills - job_skills)
    score = round(100 * len(matched) / len(profile_skills)) if profile_skills else 0

    reasons = (
        [f"Matched skills: {', '.join(matched)}"]
        if matched
        else ["No profile skills matched"]
    )
    if missing:
        reasons.append(f"Profile skills not listed: {', '.join(missing)}")

    return RankedJob(
        **job.model_dump(),
        fit_score=score,
        matched_skills=matched,
        missing_skills=missing,
        reasons=reasons,
    )

