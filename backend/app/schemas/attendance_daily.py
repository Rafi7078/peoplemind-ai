
from datetime import (
    date,
    datetime,
)
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)
AttendanceStatus = Literal[
    "present",
    "absent",
    "on_leave",
    "weekly_holiday",
]
class DailyRosterItem(BaseModel):
    employee_id: int
    employee_code: str
    full_name: str
    designation: str
    team_id: int
    shift_id: int
    weekly_holidays: list[str]
    suggested_status: AttendanceStatus
    saved_status: (
        AttendanceStatus
        | None
    ) = None
    note: str | None = None
    record_id: int | None = None
class DailyRosterRead(BaseModel):
    attendance_date: date
    team_id: int
    team_name: str
    shift_id: int
    shift_name: str
    total_members: int
    items: list[DailyRosterItem]
class DailyAttendanceEntry(BaseModel):
    employee_id: int = Field(
        gt=0
    )
    status: AttendanceStatus
    note: str | None = Field(
        default=None,
        max_length=500,
    )
    @field_validator("note")
    @classmethod
    def normalize_note(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
class DailyAttendanceSubmit(BaseModel):
    attendance_date: date
    team_id: int = Field(
        gt=0
    )
    shift_id: int = Field(
        gt=0
    )
    entries: list[
        DailyAttendanceEntry
    ] = Field(
        min_length=1
    )
    @model_validator(mode="after")
    def validate_unique_employees(
        self,
    ):
        employee_ids = [
            entry.employee_id
            for entry in self.entries
        ]
        if (
            len(employee_ids)
            != len(set(employee_ids))
        ):
            raise ValueError(
                "The same employee cannot "
                "appear more than once in "
                "one attendance submission."
            )
        return self
class DailyAttendanceRecordRead(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: int
    employee_id: int
    attendance_date: date
    team_id: int
    shift_id: int
    status: AttendanceStatus
    note: str | None
    recorded_by_id: int
    created_at: datetime
    updated_at: datetime
class DailyAttendanceSummary(
    BaseModel
):
    total_members: int
    present: int
    absent: int
    on_leave: int
    weekly_holiday: int
class DailyAttendanceSubmissionRead(
    BaseModel
):
    attendance_date: date
    team_id: int
    team_name: str
    shift_id: int
    shift_name: str
    summary: DailyAttendanceSummary
    records: list[
        DailyAttendanceRecordRead
    ]
