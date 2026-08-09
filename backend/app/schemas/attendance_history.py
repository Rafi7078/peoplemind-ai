
from datetime import (
    date,
    datetime,
)
from pydantic import BaseModel
from backend.app.schemas.attendance_daily import (
    AttendanceStatus,
    DailyAttendanceSummary,
)
class AttendanceHistoryItem(BaseModel):
    attendance_date: date
    team_id: int
    team_name: str
    shift_id: int
    shift_name: str
    summary: DailyAttendanceSummary
    last_updated_at: datetime
class AttendanceHistoryListRead(
    BaseModel
):
    total_reports: int
    items: list[
        AttendanceHistoryItem
    ]
class AttendanceHistoryEmployeeRead(
    BaseModel
):
    record_id: int
    employee_id: int
    employee_code: str
    full_name: str
    designation: str
    status: AttendanceStatus
    note: str | None
    leave_id: int | None = None
    leave_type: str | None = None
    leave_reason: str | None = None
    leave_from_date: date | None = None
    leave_to_date: date | None = None
    updated_at: datetime
class AttendanceHistoryReportRead(
    BaseModel
):
    attendance_date: date
    team_id: int
    team_name: str
    shift_id: int
    shift_name: str
    summary: DailyAttendanceSummary
    employees: list[
        AttendanceHistoryEmployeeRead
    ]
    last_updated_at: datetime
