from datetime import (
    datetime,
    timezone,
)
from sqlalchemy import (
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import (
    Mapped,
    mapped_column,
)
from backend.app.db.database import Base
class UserAttendanceScope(Base):
    __tablename__ = (
        "user_attendance_scopes"
    )
    id: Mapped[int] = mapped_column(
        primary_key=True,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        unique=True,
        index=True,
        nullable=False,
    )
    team_id: Mapped[int] = mapped_column(
        ForeignKey(
            "attendance_teams.id"
        ),
        index=True,
        nullable=False,
    )
    shift_id: Mapped[
        int | None
    ] = mapped_column(
        ForeignKey(
            "attendance_shifts.id"
        ),
        index=True,
        nullable=True,
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
