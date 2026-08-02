
from datetime import datetime
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
class CandidateATSCheck(BaseModel):
    check_id: str
    category: str
    title: str
    status: Literal[
        "pass",
        "warning",
        "fail",
    ]
    points_awarded: int
    max_points: int
    message: str
    evidence: list[str] = Field(
        default_factory=list,
    )
class CandidateATSRead(BaseModel):
    id: int
    candidate_cv_id: int
    score: int
    rating: str
    risk_level: str
    category_scores: dict[str, int]
    checks: list[
        CandidateATSCheck
    ] = Field(
        default_factory=list,
    )
    suggestions: list[str] = Field(
        default_factory=list,
    )
    engine_version: str
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
