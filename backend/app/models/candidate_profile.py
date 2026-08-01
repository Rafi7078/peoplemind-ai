
from datetime import datetime, timezone
from sqlalchemy import (
    DateTime,
    ForeignKey,
    JSON,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class CandidateProfile(Base):
    __tablename__ = "candidate_profiles"
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    candidate_cv_id: Mapped[int] = mapped_column(
        ForeignKey(
            "candidate_cvs.id",
            ondelete="CASCADE",
        ),
        unique=True,
        nullable=False,
        index=True,
    )
    candidate_name: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )
    contact_information: Mapped[
        dict
    ] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    latest_completed_education: Mapped[
        dict | None
    ] = mapped_column(
        JSON,
        nullable=True,
    )
    work_experience: Mapped[
        list
    ] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    skills: Mapped[dict] = mapped_column(
        JSON,
        default=dict,
        nullable=False,
    )
    projects: Mapped[list] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    certifications: Mapped[
        list
    ] = mapped_column(
        JSON,
        default=list,
        nullable=False,
    )
    extraction_model: Mapped[str] = (
        mapped_column(
            String(150),
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
