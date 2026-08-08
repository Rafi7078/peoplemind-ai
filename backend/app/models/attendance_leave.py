
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
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class AttendanceLeave(Base):
    __tablename__ = "attendance_leaves"
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    employee_id: Mapped[int] = mapped_column(
        ForeignKey(
            "attendance_employees.id"
        ),
        index=True,
        nullable=False,
    )
    leave_type: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
    )
    from_date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )
    to_date: Mapped[date] = mapped_column(
        Date,
        index=True,
        nullable=False,
    )
    reason: Mapped[str | None] = mapped_column(
        String(500),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(30),
        index=True,
        nullable=False,
        default="pending",
    )
    created_by_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
    )
    approved_by_id: Mapped[int | None] = (
        mapped_column(
            ForeignKey("users.id"),
            nullable=True,
        )
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(
            timezone.utc
        ),
        onupdate=lambda: datetime.now(
            timezone.utc
        ),
        nullable=False,
    )
