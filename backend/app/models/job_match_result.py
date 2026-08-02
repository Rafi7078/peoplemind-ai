
from datetime import (
    datetime,
    timezone,
)
from sqlalchemy import (
    DateTime,
    ForeignKey,
    Integer,
    JSON,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class JobMatchResult(Base):
    __tablename__ = "job_match_results"
    __table_args__ = (
        UniqueConstraint(
            "job_profile_id",
            "candidate_cv_id",
            name=(
                "uq_job_match_result_pair"
            ),
        ),
    )
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    job_profile_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "job_profiles.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )
    candidate_cv_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "candidate_cvs.id",
                ondelete="CASCADE",
            ),
            nullable=False,
            index=True,
        )
    )
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        index=True,
    )
    rating: Mapped[str] = mapped_column(
        String(60),
        nullable=False,
    )
    recommendation: Mapped[str] = (
        mapped_column(
            String(80),
            nullable=False,
        )
    )
    category_scores: Mapped[dict] = (
        mapped_column(
            JSON,
            default=dict,
            nullable=False,
        )
    )
    requirements: Mapped[dict] = (
        mapped_column(
            JSON,
            default=dict,
            nullable=False,
        )
    )
    checks: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    matched_requirements: Mapped[list] = (
        mapped_column(
            JSON,
            default=list,
            nullable=False,
        )
    )
    missing_requirements: Mapped[list] = (
        mapped_column(
            JSON,
            default=list,
            nullable=False,
        )
    )
    notes: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    engine_version: Mapped[str] = (
        mapped_column(
            String(120),
            nullable=False,
        )
    )
    created_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(
                timezone.utc
            ),
            nullable=False,
        )
    )
    updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(
                timezone.utc
            ),
            onupdate=lambda: datetime.now(
                timezone.utc
            ),
            nullable=False,
        )
    )
