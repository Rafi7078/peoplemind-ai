
from datetime import datetime
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
class JobMatchCheck(BaseModel):
    check_id: str
    category: str
    title: str
    status: Literal[
        "match",
        "partial",
        "missing",
        "not_specified",
    ]
    points_awarded: int
    max_points: int
    message: str
    evidence: list[str] = Field(
        default_factory=list,
    )
class JobMatchRead(BaseModel):
    id: int
    job_profile_id: int
    candidate_cv_id: int
    score: int
    rating: str
    recommendation: str
    category_scores: dict[str, int]
    requirements: dict = Field(
        default_factory=dict,
    )
    checks: list[
        JobMatchCheck
    ] = Field(
        default_factory=list,
    )
    matched_requirements: list[
        str
    ] = Field(
        default_factory=list,
    )
    missing_requirements: list[
        str
    ] = Field(
        default_factory=list,
    )
    notes: list[str] = Field(
        default_factory=list,
    )
    engine_version: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
