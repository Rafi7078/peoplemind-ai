from datetime import (
    date,
    datetime,
)
from typing import Literal
from pydantic import BaseModel
AttendanceMonthlyDayStatus = Literal[
    "present",
    "absent",
    "on_leave",
    "weekly_holiday",
    "not_recorded",
]
class AttendanceMonthlySummary(
    BaseModel
):
    days_in_month: int
    recorded_days: int
    not_recorded_days: int
    working_day_records: int
    present: int
    absent: int
    on_leave: int
    weekly_holiday: int
    attendance_rate: float
class AttendanceMonthlyDayRead(
    BaseModel
):
    attendance_date: date
    weekday: str
    status: AttendanceMonthlyDayStatus
    is_recorded: bool
    record_id: int | None = None
    note: str | None = None
    team_name: str
    shift_name: str
    leave_id: int | None = None
    leave_type: str | None = None
    leave_reason: str | None = None
    leave_from_date: date | None = None
    leave_to_date: date | None = None
    updated_at: datetime | None = None
class AttendanceEmployeeMonthlyReportRead(
    BaseModel
):
    employee_id: int
    employee_code: str
    full_name: str
    designation: str
    team_id: int
    team_name: str
    shift_id: int
    shift_name: str
    year: int
    month: int
    month_label: str
    summary: AttendanceMonthlySummary
    days: list[
        AttendanceMonthlyDayRead
    ]
