from datetime import date
from pydantic import BaseModel
class AttendanceAnalyticsCounts(
    BaseModel
):
    total_records: int
    working_day_records: int
    present: int
    absent: int
    on_leave: int
    weekly_holiday: int
    attendance_rate: float
class AttendanceAnalyticsDailyItem(
    AttendanceAnalyticsCounts
):
    attendance_date: date
class AttendanceAnalyticsTeamItem(
    AttendanceAnalyticsCounts
):
    team_id: int
    team_name: str
class AttendanceAnalyticsShiftItem(
    AttendanceAnalyticsCounts
):
    shift_id: int
    shift_name: str
class AttendanceAnalyticsEmployeeItem(
    AttendanceAnalyticsCounts
):
    employee_id: int
    employee_code: str
    full_name: str
    designation: str
    team_id: int
    team_name: str
    shift_id: int
    shift_name: str
class AttendanceAnalyticsRead(
    BaseModel
):
    date_from: date
    date_to: date
    team_id: int | None
    shift_id: int | None
    summary: AttendanceAnalyticsCounts
    daily_trend: list[
        AttendanceAnalyticsDailyItem
    ]
    teams: list[
        AttendanceAnalyticsTeamItem
    ]
    shifts: list[
        AttendanceAnalyticsShiftItem
    ]
    employees: list[
        AttendanceAnalyticsEmployeeItem
    ]
