
from sqlalchemy import (
    select,
)
from sqlalchemy.exc import (
    IntegrityError,
)
from sqlalchemy.orm import Session
from backend.app.models.candidate_cv import (
    CandidateCV,
)
from backend.app.models.job_candidate_assignment import (
    JobCandidateAssignment,
)
from backend.app.services.candidate_service import (
    get_candidate_cv,
)
from backend.app.services.job_profile_service import (
    get_job_profile,
)
class CandidateAlreadyAssignedError(
    ValueError
):
    pass
class CandidateAssignmentNotFoundError(
    LookupError
):
    pass
def assign_candidate_to_job(
    database: Session,
    job_id: int,
    candidate_id: int,
    assigned_by_id: int,
) -> JobCandidateAssignment:
    get_job_profile(
        database=database,
        job_id=job_id,
    )
    get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    statement = select(
        JobCandidateAssignment
    ).where(
        JobCandidateAssignment.job_profile_id
        == job_id,
        JobCandidateAssignment.candidate_cv_id
        == candidate_id,
    )
    existing_assignment = (
        database.scalar(statement)
    )
    if existing_assignment is not None:
        raise CandidateAlreadyAssignedError(
            "This candidate is already "
            "assigned to the selected job."
        )
    assignment = JobCandidateAssignment(
        job_profile_id=job_id,
        candidate_cv_id=candidate_id,
        assigned_by_id=assigned_by_id,
    )
    try:
        database.add(assignment)
        database.commit()
        database.refresh(assignment)
    except IntegrityError as error:
        database.rollback()
        raise CandidateAlreadyAssignedError(
            "This candidate is already "
            "assigned to the selected job."
        ) from error
    return assignment
def remove_candidate_from_job(
    database: Session,
    job_id: int,
    candidate_id: int,
) -> None:
    get_job_profile(
        database=database,
        job_id=job_id,
    )
    get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    statement = select(
        JobCandidateAssignment
    ).where(
        JobCandidateAssignment.job_profile_id
        == job_id,
        JobCandidateAssignment.candidate_cv_id
        == candidate_id,
    )
    assignment = database.scalar(
        statement
    )
    if assignment is None:
        raise (
            CandidateAssignmentNotFoundError(
                "The candidate is not assigned "
                "to the selected job."
            )
        )
    database.delete(assignment)
    database.commit()
def list_job_candidates(
    database: Session,
    job_id: int,
) -> list[CandidateCV]:
    get_job_profile(
        database=database,
        job_id=job_id,
    )
    statement = (
        select(CandidateCV)
        .join(
            JobCandidateAssignment,
            (
                JobCandidateAssignment
                .candidate_cv_id
                == CandidateCV.id
            ),
        )
        .where(
            JobCandidateAssignment
            .job_profile_id
            == job_id
        )
        .order_by(
            CandidateCV.created_at.desc()
        )
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
def list_unassigned_candidates(
    database: Session,
) -> list[CandidateCV]:
    assignment_exists = (
        select(
            JobCandidateAssignment.id
        )
        .where(
            JobCandidateAssignment
            .candidate_cv_id
            == CandidateCV.id
        )
        .exists()
    )
    statement = (
        select(CandidateCV)
        .where(
            ~assignment_exists
        )
        .order_by(
            CandidateCV.created_at.desc()
        )
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
