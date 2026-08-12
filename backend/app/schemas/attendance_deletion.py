from datetime import (
    date,
    datetime,
)
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
class AttendanceDeletionRequest(
    BaseModel
):
    reason: str = Field(
        min_length=3,
        max_length=500,
    )
    @field_validator("reason")
    @classmethod
    def normalize_reason(
        cls,
        value: str,
    ) -> str:
        value = value.strip()
        if len(value) < 3:
            raise ValueError(
                "Deletion reason must contain "
                "at least 3 characters."
            )
        return value
class AttendanceDeletionRead(
    BaseModel
):
    model_config = ConfigDict(
        from_attributes=True
    )
    id: int
    attendance_date: date
    team_id: int
    team_name: str
    shift_id: int
    shift_name: str
    deleted_record_count: int
    reason: str
    deleted_by_user_id: int
    deleted_by_email: str
    original_account_email: str | None
    original_submitter_code: str | None
    original_submitter_name: str | None
    deleted_at: datetime
