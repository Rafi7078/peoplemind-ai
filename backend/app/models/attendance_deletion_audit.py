from datetime import (
    date,
    datetime,
    timezone,
)
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    Integer,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class AttendanceDeletionAudit(Base):
    __tablename__ = (
        "attendance_deletion_audits"
    )
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    attendance_date: Mapped[date] = (
        mapped_column(
            Date,
            index=True,
            nullable=False,
        )
    )
    team_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )
    team_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    shift_id: Mapped[int] = mapped_column(
        Integer,
        index=True,
        nullable=False,
    )
    shift_name: Mapped[str] = mapped_column(
        String(120),
        nullable=False,
    )
    deleted_record_count: Mapped[int] = (
        mapped_column(
            Integer,
            nullable=False,
        )
    )
    reason: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )
    deleted_by_user_id: Mapped[int] = (
        mapped_column(
            ForeignKey("users.id"),
            nullable=False,
        )
    )
    deleted_by_email: Mapped[str] = (
        mapped_column(
            String(320),
            nullable=False,
        )
    )
    original_account_email: Mapped[
        str | None
    ] = mapped_column(
        String(320),
        nullable=True,
    )
    original_submitter_code: Mapped[
        str | None
    ] = mapped_column(
        String(50),
        nullable=True,
    )
    original_submitter_name: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )
    deleted_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(
                timezone.utc
            ),
            nullable=False,
        )
    )
