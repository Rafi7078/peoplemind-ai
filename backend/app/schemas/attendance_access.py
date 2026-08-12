from typing import Literal
from pydantic import BaseModel
class AttendanceAllowedShiftRead(
    BaseModel
):
    id: int
    name: str
class DailyAttendanceAccessRead(
    BaseModel
):
    role: Literal[
        "admin",
        "attendance",
    ]
    is_admin: bool
    team_id: int | None = None
    team_name: str | None = None
    shift_id: int | None = None
    shift_name: str | None = None
    scope_type: Literal[
        "admin",
        "team",
        "team_shift",
    ]
    allowed_shifts: list[
        AttendanceAllowedShiftRead
    ] = []
