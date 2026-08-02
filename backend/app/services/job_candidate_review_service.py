
from datetime import (
    datetime,
    timezone,
)
from sqlalchemy import (
    and_,
    delete,
    select,
)
from sqlalchemy.orm import Session
from backend.app.models.candidate_ats_result import (
    CandidateATSResult,
)
from backend.app.models.candidate_cv import (
    CandidateCV,
)
from backend.app.models.candidate_profile import (
    CandidateProfile,
)
from backend.app.models.job_candidate_assignment import (
    JobCandidateAssignment,
)
from backend.app.models.job_candidate_review import (
    JobCandidateReview,
)
from backend.app.models.job_match_result import (
    JobMatchResult,
)
from backend.app.schemas.job_candidate_review import (
    JobCandidateReviewUpdate,
)
from backend.app.services.candidate_service import (
    get_candidate_cv,
)
from backend.app.services.job_candidate_assignment_service import (
    CandidateAssignmentNotFoundError,
)
from backend.app.services.job_profile_service import (
    get_job_profile,
)
class JobCandidateReviewNotFoundError(
    LookupError
):
    pass
def require_job_candidate_assignment(
    database: Session,
    job_id: int,
    candidate_id: int,
) -> JobCandidateAssignment:
    get_job_profile(
        database=database,
        job_id=job_id,
    )
    get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    statement = (
        select(
            JobCandidateAssignment
        )
        .where(
            JobCandidateAssignment
            .job_profile_id
            == job_id,
            JobCandidateAssignment
            .candidate_cv_id
            == candidate_id,
        )
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
    return assignment
def get_job_candidate_review(
    database: Session,
    job_id: int,
    candidate_id: int,
) -> JobCandidateReview:
    require_job_candidate_assignment(
        database=database,
        job_id=job_id,
        candidate_id=candidate_id,
    )
    statement = (
        select(JobCandidateReview)
        .where(
            JobCandidateReview
            .job_profile_id
            == job_id,
            JobCandidateReview
            .candidate_cv_id
            == candidate_id,
        )
    )
    review = database.scalar(
        statement
    )
    if review is None:
        raise (
            JobCandidateReviewNotFoundError(
                "HR review has not been saved "
                "for this candidate and job."
            )
        )
    return review
def upsert_job_candidate_review(
    database: Session,
    job_id: int,
    candidate_id: int,
    request: JobCandidateReviewUpdate,
    reviewed_by_id: int,
) -> JobCandidateReview:
    require_job_candidate_assignment(
        database=database,
        job_id=job_id,
        candidate_id=candidate_id,
    )
    statement = (
        select(JobCandidateReview)
        .where(
            JobCandidateReview
            .job_profile_id
            == job_id,
            JobCandidateReview
            .candidate_cv_id
            == candidate_id,
        )
    )
    review = database.scalar(
        statement
    )
    review_time = datetime.now(
        timezone.utc
    )
    if review is None:
        review = JobCandidateReview(
            job_profile_id=job_id,
            candidate_cv_id=candidate_id,
            status=request.status,
            notes=request.notes,
            reviewed_by_id=(
                reviewed_by_id
            ),
            reviewed_at=review_time,
        )
        database.add(review)
    else:
        review.status = request.status
        review.notes = request.notes
        review.reviewed_by_id = (
            reviewed_by_id
        )
        review.reviewed_at = (
            review_time
        )
    try:
        database.commit()
        database.refresh(review)
    except Exception:
        database.rollback()
        raise
    return review
def list_job_candidate_ranking(
    database: Session,
    job_id: int,
) -> list[dict]:
    get_job_profile(
        database=database,
        job_id=job_id,
    )
    statement = (
        select(
            CandidateCV,
            CandidateProfile.candidate_name,
            JobMatchResult,
            CandidateATSResult,
            JobCandidateReview,
        )
        .select_from(CandidateCV)
        .join(
            JobCandidateAssignment,
            (
                JobCandidateAssignment
                .candidate_cv_id
                == CandidateCV.id
            ),
        )
        .outerjoin(
            CandidateProfile,
            (
                CandidateProfile
                .candidate_cv_id
                == CandidateCV.id
            ),
        )
        .outerjoin(
            JobMatchResult,
            and_(
                JobMatchResult
                .candidate_cv_id
                == CandidateCV.id,
                JobMatchResult
                .job_profile_id
                == job_id,
            ),
        )
        .outerjoin(
            CandidateATSResult,
            (
                CandidateATSResult
                .candidate_cv_id
                == CandidateCV.id
            ),
        )
        .outerjoin(
            JobCandidateReview,
            and_(
                JobCandidateReview
                .candidate_cv_id
                == CandidateCV.id,
                JobCandidateReview
                .job_profile_id
                == job_id,
            ),
        )
        .where(
            JobCandidateAssignment
            .job_profile_id
            == job_id
        )
    )
    rows = list(
        database.execute(
            statement
        ).all()
    )
    def ranking_sort_key(
        row: tuple,
    ) -> tuple:
        candidate = row[0]
        match_result = row[2]
        candidate_created = (
            candidate.created_at.timestamp()
        )
        if match_result is None:
            return (
                1,
                0,
                0,
                -candidate_created,
            )
        match_updated = (
            match_result
            .updated_at
            .timestamp()
        )
        return (
            0,
            -match_result.score,
            -match_updated,
            -candidate_created,
        )
    rows.sort(
        key=ranking_sort_key
    )
    ranking_items: list[dict] = []
    analyzed_rank = 0
    for (
        candidate,
        candidate_name,
        match_result,
        ats_result,
        review,
    ) in rows:
        if match_result is None:
            rank = None
            analysis_status = (
                "not_analyzed"
            )
            match_summary = None
        else:
            analyzed_rank += 1
            rank = analyzed_rank
            analysis_status = "analyzed"
            match_summary = {
                "score": (
                    match_result.score
                ),
                "rating": (
                    match_result.rating
                ),
                "recommendation": (
                    match_result
                    .recommendation
                ),
                "engine_version": (
                    match_result
                    .engine_version
                ),
                "updated_at": (
                    match_result.updated_at
                ),
            }
        normalized_name = (
            candidate_name.strip()
            if (
                isinstance(
                    candidate_name,
                    str,
                )
                and candidate_name.strip()
            )
            else None
        )
        ranking_items.append(
            {
                "rank": rank,
                "analysis_status": (
                    analysis_status
                ),
                "candidate": candidate,
                "candidate_name": (
                    normalized_name
                ),
                "match": match_summary,
                "ats_score": (
                    ats_result.score
                    if ats_result
                    is not None
                    else None
                ),
                "ats_rating": (
                    ats_result.rating
                    if ats_result
                    is not None
                    else None
                ),
                "review_status": (
                    review.status
                    if review is not None
                    else "not_reviewed"
                ),
                "review": review,
            }
        )
    return ranking_items
def delete_job_candidate_review_pair(
    database: Session,
    job_id: int,
    candidate_id: int,
) -> None:
    try:
        database.execute(
            delete(
                JobCandidateReview
            ).where(
                JobCandidateReview
                .job_profile_id
                == job_id,
                JobCandidateReview
                .candidate_cv_id
                == candidate_id,
            )
        )
        database.commit()
    except Exception:
        database.rollback()
        raise
def delete_job_candidate_reviews_for_job(
    database: Session,
    job_id: int,
) -> None:
    try:
        database.execute(
            delete(
                JobCandidateReview
            ).where(
                JobCandidateReview
                .job_profile_id
                == job_id
            )
        )
        database.commit()
    except Exception:
        database.rollback()
        raise
def delete_job_candidate_reviews_for_candidate(
    database: Session,
    candidate_id: int,
) -> None:
    try:
        database.execute(
            delete(
                JobCandidateReview
            ).where(
                JobCandidateReview
                .candidate_cv_id
                == candidate_id
            )
        )
        database.commit()
    except Exception:
        database.rollback()
        raise
