
from datetime import datetime
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
AttendanceMasterStatus = Literal[
    "active",
    "archived",
]
WeekdayName = Literal[
    "Monday",
    "Tuesday",
    "Wednesday",
    "Thursday",
    "Friday",
    "Saturday",
    "Sunday",
]
class TeamCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=120,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    status: AttendanceMasterStatus = (
        "active"
    )
    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str,
    ) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "Team name cannot be empty."
            )
        return value
class TeamUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    status: (
        AttendanceMasterStatus
        | None
    ) = None
    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError(
                "Team name cannot be empty."
            )
        return value
class TeamRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: int
    name: str
    description: str | None
    status: AttendanceMasterStatus
    created_by_id: int
    created_at: datetime
    updated_at: datetime
class ShiftCreate(BaseModel):
    name: str = Field(
        min_length=1,
        max_length=120,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    status: AttendanceMasterStatus = (
        "active"
    )
    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str,
    ) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "Shift name cannot be empty."
            )
        return value
class ShiftUpdate(BaseModel):
    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=120,
    )
    description: str | None = Field(
        default=None,
        max_length=500,
    )
    status: (
        AttendanceMasterStatus
        | None
    ) = None
    @field_validator("name")
    @classmethod
    def normalize_name(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError(
                "Shift name cannot be empty."
            )
        return value
class ShiftRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: int
    name: str
    description: str | None
    status: AttendanceMasterStatus
    created_by_id: int
    created_at: datetime
    updated_at: datetime
class EmployeeCreate(BaseModel):
    employee_code: str = Field(
        min_length=1,
        max_length=50,
    )
    full_name: str = Field(
        min_length=1,
        max_length=200,
    )
    designation: str = Field(
        min_length=1,
        max_length=200,
    )
    team_id: int = Field(gt=0)
    shift_id: int = Field(gt=0)
    weekly_holidays: list[
        WeekdayName
    ] = Field(
        default_factory=list
    )
    is_active: bool = True
    @field_validator(
        "employee_code",
        "full_name",
        "designation",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: str,
    ) -> str:
        value = value.strip()
        if not value:
            raise ValueError(
                "This field cannot be empty."
            )
        return value
    @field_validator(
        "weekly_holidays"
    )
    @classmethod
    def validate_weekly_holidays(
        cls,
        value: list[WeekdayName],
    ) -> list[WeekdayName]:
        if len(value) != len(set(value)):
            raise ValueError(
                "Weekly holidays cannot "
                "contain duplicates."
            )
        return value
class EmployeeUpdate(BaseModel):
    employee_code: str | None = Field(
        default=None,
        min_length=1,
        max_length=50,
    )
    full_name: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    designation: str | None = Field(
        default=None,
        min_length=1,
        max_length=200,
    )
    team_id: int | None = Field(
        default=None,
        gt=0,
    )
    shift_id: int | None = Field(
        default=None,
        gt=0,
    )
    weekly_holidays: (
        list[WeekdayName]
        | None
    ) = None
    is_active: bool | None = None
    @field_validator(
        "employee_code",
        "full_name",
        "designation",
    )
    @classmethod
    def normalize_required_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        value = value.strip()
        if not value:
            raise ValueError(
                "This field cannot be empty."
            )
        return value
    @field_validator(
        "weekly_holidays"
    )
    @classmethod
    def validate_weekly_holidays(
        cls,
        value: (
            list[WeekdayName]
            | None
        ),
    ) -> (
        list[WeekdayName]
        | None
    ):
        if value is None:
            return None
        if len(value) != len(set(value)):
            raise ValueError(
                "Weekly holidays cannot "
                "contain duplicates."
            )
        return value
class EmployeeRead(BaseModel):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: int
    employee_code: str
    full_name: str
    designation: str
    team_id: int
    shift_id: int
    weekly_holidays: list[
        WeekdayName
    ]
    is_active: bool
    created_by_id: int
    created_at: datetime
    updated_at: datetime
