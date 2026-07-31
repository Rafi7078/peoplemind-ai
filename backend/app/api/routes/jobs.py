
from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from backend.app.api.dependencies import (
    CurrentUserDependency,
    DatabaseDependency,
)
from backend.app.schemas.job import (
    JobProfileCreate,
    JobProfileRead,
)
from backend.app.services.job_profile_service import (
    JobProfileNotFoundError,
    create_job_profile,
    get_job_profile,
    list_job_profiles,
)
router = APIRouter(
    prefix="/api/jobs",
    tags=["Job Profiles"],
)
@router.post(
    "",
    response_model=JobProfileRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a job profile",
)
def create_job(
    request: JobProfileCreate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> JobProfileRead:
    job_profile = create_job_profile(
        database=database,
        request=request,
        created_by_id=current_user.id,
    )
    return JobProfileRead.model_validate(
        job_profile
    )
@router.get(
    "",
    response_model=list[JobProfileRead],
    summary="List job profiles",
)
def read_jobs(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[JobProfileRead]:
    return [
        JobProfileRead.model_validate(
            job_profile
        )
        for job_profile in list_job_profiles(
            database
        )
    ]
@router.get(
    "/{job_id}",
    response_model=JobProfileRead,
    summary="Read a job profile",
)
def read_job(
    job_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> JobProfileRead:
    try:
        job_profile = get_job_profile(
            database=database,
            job_id=job_id,
        )
    except JobProfileNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    return JobProfileRead.model_validate(
        job_profile
    )
