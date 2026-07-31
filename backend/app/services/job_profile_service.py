
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.job_profile import (
    JobProfile,
)
from backend.app.schemas.job import (
    JobProfileCreate,
)
class JobProfileNotFoundError(
    LookupError
):
    pass
def create_job_profile(
    database: Session,
    request: JobProfileCreate,
    created_by_id: int,
) -> JobProfile:
    job_profile = JobProfile(
        title=request.title,
        department=request.department,
        location=request.location,
        employment_type=(
            request.employment_type
        ),
        description=request.description,
        status=request.status,
        created_by_id=created_by_id,
    )
    database.add(job_profile)
    database.commit()
    database.refresh(job_profile)
    return job_profile
def list_job_profiles(
    database: Session,
) -> list[JobProfile]:
    statement = (
        select(JobProfile)
        .order_by(
            JobProfile.created_at.desc()
        )
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
def get_job_profile(
    database: Session,
    job_id: int,
) -> JobProfile:
    job_profile = database.get(
        JobProfile,
        job_id,
    )
    if job_profile is None:
        raise JobProfileNotFoundError(
            "The requested job profile was not found."
        )
    return job_profile
