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
class AttendanceRecordLeaveSnapshot(Base):
    __tablename__ = (
        "attendance_record_leave_snapshots"
    )
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    attendance_record_id: Mapped[int] = (
        mapped_column(
            ForeignKey(
                "attendance_records.id"
            ),
            unique=True,
            index=True,
            nullable=False,
        )
    )
    attendance_leave_id: Mapped[
        int | None
    ] = mapped_column(
        Integer,
        nullable=True,
    )
    leave_type: Mapped[str] = (
        mapped_column(
            String(40),
            nullable=False,
        )
    )
    leave_reason: Mapped[
        str | None
    ] = mapped_column(
        String(500),
        nullable=True,
    )
    leave_from_date: Mapped[date] = (
        mapped_column(
            Date,
            nullable=False,
        )
    )
    leave_to_date: Mapped[date] = (
        mapped_column(
            Date,
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
