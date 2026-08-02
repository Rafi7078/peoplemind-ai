
from datetime import datetime
from typing import (
    Literal,
    TypeAlias,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
from backend.app.schemas.candidate import (
    CandidateCVRead,
)
JobReviewStatus: TypeAlias = Literal[
    "not_reviewed",
    "in_review",
    "shortlisted",
    "on_hold",
    "not_selected",
]
class JobCandidateReviewUpdate(
    BaseModel
):
    status: JobReviewStatus
    notes: str | None = Field(
        default=None,
        max_length=5000,
    )
    @field_validator("notes")
    @classmethod
    def normalize_notes(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized_value = value.strip()
        return normalized_value or None
class JobCandidateReviewRead(
    BaseModel
):
    id: int
    job_profile_id: int
    candidate_cv_id: int
    status: JobReviewStatus
    notes: str | None
    reviewed_by_id: int
    reviewed_at: datetime
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
class JobMatchRankingSummary(
    BaseModel
):
    score: int
    rating: str
    recommendation: str
    engine_version: str
    updated_at: datetime
class JobCandidateRankingItem(
    BaseModel
):
    rank: int | None
    analysis_status: Literal[
        "analyzed",
        "not_analyzed",
    ]
    candidate: CandidateCVRead
    candidate_name: str | None
    match: (
        JobMatchRankingSummary
        | None
    )
    ats_score: int | None
    ats_rating: str | None
    review_status: JobReviewStatus
    review: (
        JobCandidateReviewRead
        | None
    )
