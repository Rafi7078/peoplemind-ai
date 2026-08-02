
from fastapi import (
    APIRouter,
    HTTPException,
    status,
)
from backend.app.api.dependencies import (
    CurrentUserDependency,
    DatabaseDependency,
)
from backend.app.schemas.candidate import (
    CandidateCVRead,
)
from backend.app.schemas.job import (
    JobProfileCreate,
    JobProfileRead,
    JobProfileUpdate,
)
from backend.app.schemas.job_candidate_assignment import (
    JobCandidateAssignmentRead,
)
from backend.app.schemas.job_match import (
    JobMatchRead,
)
from backend.app.services.job_profile_service import (
    JobProfileNotFoundError,
    create_job_profile,
    delete_job_profile,
    get_job_profile,
    list_job_profiles,
    update_job_profile,
)
from backend.app.services.candidate_service import (
    CandidateCVNotFoundError,
)
from backend.app.services.job_candidate_assignment_service import (
    CandidateAlreadyAssignedError,
    CandidateAssignmentNotFoundError,
    assign_candidate_to_job,
    list_job_candidates,
    remove_candidate_from_job,
)
from backend.app.services import (
    job_match_service,
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

@router.post(
    (
        "/{job_id}/candidates/"
        "{candidate_id}/match/analyze"
    ),
    response_model=JobMatchRead,
    summary=(
        "Analyze a candidate against a job"
    ),
)
def analyze_candidate_job_match(
    job_id: int,
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> JobMatchRead:
    try:
        result = (
            job_match_service
            .analyze_job_candidate_match(
                database=database,
                job_id=job_id,
                candidate_id=candidate_id,
            )
        )
    except (
        JobProfileNotFoundError,
        CandidateCVNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        job_match_service
        .JobMatchPrerequisiteError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
    return JobMatchRead.model_validate(
        result
    )
@router.get(
    (
        "/{job_id}/candidates/"
        "{candidate_id}/match"
    ),
    response_model=JobMatchRead,
    summary=(
        "Read a candidate job-match result"
    ),
)
def read_candidate_job_match(
    job_id: int,
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> JobMatchRead:
    try:
        result = (
            job_match_service
            .get_job_match_result(
                database=database,
                job_id=job_id,
                candidate_id=candidate_id,
            )
        )
    except (
        JobProfileNotFoundError,
        CandidateCVNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        job_match_service
        .JobMatchResultNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    return JobMatchRead.model_validate(
        result
    )
@router.get(
    "/{job_id}/matches",
    response_model=list[JobMatchRead],
    summary=(
        "List analyzed candidates ranked "
        "for a job"
    ),
)
def read_job_match_ranking(
    job_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[JobMatchRead]:
    try:
        results = (
            job_match_service
            .list_job_match_results(
                database=database,
                job_id=job_id,
            )
        )
    except JobProfileNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    return [
        JobMatchRead.model_validate(
            result
        )
        for result in results
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

@router.patch(
    "/{job_id}",
    response_model=JobProfileRead,
    summary="Update a job profile",
)
def update_job(
    job_id: int,
    request: JobProfileUpdate,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> JobProfileRead:
    try:
        job_profile = update_job_profile(
            database=database,
            job_id=job_id,
            request=request,
        )
        job_match_service.invalidate_job_matches_for_job(
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
@router.delete(
    "/{job_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a job profile",
)
def delete_job(
    job_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> None:
    try:
        delete_job_profile(
            database=database,
            job_id=job_id,
        )
        job_match_service.invalidate_job_matches_for_job(
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
@router.post(
    "/{job_id}/candidates/{candidate_id}",
    response_model=(
        JobCandidateAssignmentRead
    ),
    status_code=status.HTTP_201_CREATED,
    summary="Assign a candidate to a job",
)
def assign_candidate(
    job_id: int,
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> JobCandidateAssignmentRead:
    try:
        assignment = (
            assign_candidate_to_job(
                database=database,
                job_id=job_id,
                candidate_id=candidate_id,
                assigned_by_id=(
                    current_user.id
                ),
            )
        )
    except (
        JobProfileNotFoundError,
        CandidateCVNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        CandidateAlreadyAssignedError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
    return (
        JobCandidateAssignmentRead
        .model_validate(assignment)
    )
@router.delete(
    "/{job_id}/candidates/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove a candidate from a job",
)
def remove_candidate(
    job_id: int,
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> None:
    try:
        remove_candidate_from_job(
            database=database,
            job_id=job_id,
            candidate_id=candidate_id,
        )
        job_match_service.invalidate_job_match_pair(
            database=database,
            job_id=job_id,
            candidate_id=candidate_id,
        )
    except (
        JobProfileNotFoundError,
        CandidateCVNotFoundError,
        CandidateAssignmentNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
@router.get(
    "/{job_id}/candidates",
    response_model=list[CandidateCVRead],
    summary="List candidates assigned to a job",
)
def read_job_candidates(
    job_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[CandidateCVRead]:
    try:
        candidates = list_job_candidates(
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
    return [
        CandidateCVRead.model_validate(
            candidate
        )
        for candidate in candidates
    ]
