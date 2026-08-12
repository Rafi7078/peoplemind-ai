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
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class AttendanceSubmissionAudit(Base):
    __tablename__ = (
        "attendance_submission_audits"
    )
    __table_args__ = (
        UniqueConstraint(
            "attendance_date",
            "team_id",
            "shift_id",
            name=(
                "uq_attendance_submission_"
                "date_team_shift"
            ),
        ),
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
        ForeignKey(
            "attendance_teams.id"
        ),
        index=True,
        nullable=False,
    )
    shift_id: Mapped[int] = mapped_column(
        ForeignKey(
            "attendance_shifts.id"
        ),
        index=True,
        nullable=False,
    )
    submitted_by_user_id: Mapped[int] = (
        mapped_column(
            ForeignKey("users.id"),
            nullable=False,
        )
    )
    submitted_account_email: Mapped[str] = (
        mapped_column(
            String(320),
            nullable=False,
        )
    )
    submitted_by_employee_id: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )
    submitted_by_employee_code: Mapped[
        str | None
    ] = mapped_column(
        String(50),
        nullable=True,
    )
    submitted_by_employee_name: Mapped[
        str | None
    ] = mapped_column(
        String(255),
        nullable=True,
    )
    submitted_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(
                timezone.utc
            ),
            nullable=False,
        )
    )
    last_updated_by_user_id: Mapped[int] = (
        mapped_column(
            ForeignKey("users.id"),
            nullable=False,
        )
    )
    last_updated_account_email: Mapped[str] = (
        mapped_column(
            String(320),
            nullable=False,
        )
    )
    last_updated_at: Mapped[datetime] = (
        mapped_column(
            DateTime(timezone=True),
            default=lambda: datetime.now(
                timezone.utc
            ),
            nullable=False,
        )
    )
