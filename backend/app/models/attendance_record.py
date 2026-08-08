
from datetime import (
    date,
    datetime,
    timezone,
)
from sqlalchemy import (
    Date,
    DateTime,
    ForeignKey,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class AttendanceRecord(Base):
    __tablename__ = "attendance_records"
    __table_args__ = (
        UniqueConstraint(
            "employee_id",
            "attendance_date",
            name=(
                "uq_attendance_record_"
                "employee_date"
            ),
        ),
    )
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    employee_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "attendance_employees.id"
            ),
            index=True,
            nullable=False,
        )
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
    status: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )
    note: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    recorded_by_id: Mapped[int] = (
        mapped_column(
            ForeignKey("users.id"),
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
