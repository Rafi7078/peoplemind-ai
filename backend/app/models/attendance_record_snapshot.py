
from datetime import (
    datetime,
    timezone,
)
from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class AttendanceRecordSnapshot(Base):
    __tablename__ = (
        "attendance_record_snapshots"
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
    employee_code: Mapped[str] = (
        mapped_column(
            String(80),
            nullable=False,
        )
    )
    full_name: Mapped[str] = (
        mapped_column(
            String(160),
            nullable=False,
        )
    )
    designation: Mapped[str] = (
        mapped_column(
            String(160),
            nullable=False,
        )
    )
    team_name: Mapped[str] = (
        mapped_column(
            String(120),
            nullable=False,
        )
    )
    shift_name: Mapped[str] = (
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
