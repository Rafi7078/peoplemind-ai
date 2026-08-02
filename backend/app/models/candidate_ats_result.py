
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
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class CandidateATSResult(Base):
    __tablename__ = "candidate_ats_results"
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    candidate_cv_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "candidate_cvs.id",
                ondelete="CASCADE",
            ),
            unique=True,
            nullable=False,
            index=True,
        )
    )
    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )
    rating: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )
    risk_level: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
    )
    category_scores: Mapped[dict] = (
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
    suggestions: Mapped[list] = (
        mapped_column(
            JSON,
            default=list,
            nullable=False,
        )
    )
    engine_version: Mapped[str] = (
        mapped_column(
            String(100),
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
