
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
LeaveType = Literal[
    "casual",
    "sick",
    "annual",
    "other",
]
LeaveStatus = Literal[
    "pending",
    "approved",
    "cancelled",
]
class AttendanceLeaveCreate(BaseModel):
    employee_id: int = Field(gt=0)
    leave_type: LeaveType
    from_date: date
    to_date: date
    reason: str | None = Field(
        default=None,
        max_length=500,
    )
    status: LeaveStatus = "pending"
    @field_validator("reason")
    @classmethod
    def normalize_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
    @model_validator(mode="after")
    def validate_date_range(
        self,
    ):
        if self.from_date > self.to_date:
            raise ValueError(
                "from_date cannot be later "
                "than to_date."
            )
        return self
class AttendanceLeaveUpdate(BaseModel):
    leave_type: LeaveType | None = None
    from_date: date | None = None
    to_date: date | None = None
    reason: str | None = Field(
        default=None,
        max_length=500,
    )
    status: LeaveStatus | None = None
    @field_validator("reason")
    @classmethod
    def normalize_reason(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        value = value.strip()
        return value or None
class AttendanceLeaveRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: int
    employee_id: int
    leave_type: LeaveType
    from_date: date
    to_date: date
    reason: str | None
    status: LeaveStatus
    created_by_id: int
    approved_by_id: int | None
    created_at: datetime
    updated_at: datetime
class AttendanceLeaveListRead(BaseModel):
    total: int
    items: list[
        AttendanceLeaveRead
    ]
