
from datetime import datetime, timezone
from sqlalchemy import (
    Boolean,
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
class AttendanceEmployee(Base):
    __tablename__ = "attendance_employees"
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    employee_code: Mapped[str] = (
        mapped_column(
            String(50),
            unique=True,
            index=True,
            nullable=False,
        )
    )
    full_name: Mapped[str] = mapped_column(
        String(200),
        index=True,
        nullable=False,
    )
    designation: Mapped[str] = (
        mapped_column(
            String(200),
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
    weekly_holidays: Mapped[list[str]] = (
        mapped_column(
            JSON,
            default=list,
            nullable=False,
        )
    )
    is_active: Mapped[bool] = (
        mapped_column(
            Boolean,
            default=True,
            index=True,
            nullable=False,
        )
    )
    created_by_id: Mapped[int] = (
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
