
from datetime import (
    datetime,
    timezone,
)
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class JobCandidateReview(Base):
    __tablename__ = (
        "job_candidate_reviews"
    )
    __table_args__ = (
        UniqueConstraint(
            "job_profile_id",
            "candidate_cv_id",
            name=(
                "uq_job_candidate_review_pair"
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
    status: Mapped[str] = mapped_column(
        String(32),
        default="not_reviewed",
        nullable=False,
        index=True,
    )
    notes: Mapped[
        str | None
    ] = mapped_column(
        Text,
        nullable=True,
    )
    reviewed_by_id: Mapped[int] = (
        mapped_column(
            ForeignKey("users.id"),
            nullable=False,
            index=True,
        )
    )
    reviewed_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(
                timezone.utc
            ),
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
