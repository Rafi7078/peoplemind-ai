
from datetime import datetime
from typing import Literal
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
)
class JobProfileCreate(BaseModel):
    title: str = Field(
        min_length=2,
        max_length=200,
    )
    department: str | None = Field(
        default=None,
        max_length=150,
    )
    location: str | None = Field(
        default=None,
        max_length=150,
    )
    employment_type: str | None = Field(
        default=None,
        max_length=80,
    )
    description: str = Field(
        min_length=20,
        max_length=30_000,
    )
    status: Literal[
        "draft",
        "active",
        "closed",
    ] = "draft"
    @field_validator(
        "title",
        "department",
        "location",
        "employment_type",
        "description",
    )
    @classmethod
    def normalize_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized_value = value.strip()
        if not normalized_value:
            return None
        return normalized_value

class JobProfileUpdate(BaseModel):
    title: str | None = Field(
        default=None,
        min_length=2,
        max_length=200,
    )
    department: str | None = Field(
        default=None,
        max_length=150,
    )
    location: str | None = Field(
        default=None,
        max_length=150,
    )
    employment_type: str | None = Field(
        default=None,
        max_length=80,
    )
    description: str | None = Field(
        default=None,
        min_length=20,
        max_length=30_000,
    )
    status: Literal[
        "draft",
        "active",
        "closed",
        "archived",
    ] | None = None
    @field_validator(
        "title",
        "description",
    )
    @classmethod
    def normalize_required_update_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized_value = value.strip()
        if not normalized_value:
            raise ValueError(
                "This value cannot be empty."
            )
        return normalized_value
    @field_validator(
        "department",
        "location",
        "employment_type",
    )
    @classmethod
    def normalize_optional_update_text(
        cls,
        value: str | None,
    ) -> str | None:
        if value is None:
            return None
        normalized_value = value.strip()
        return normalized_value or None
class JobProfileRead(BaseModel):
    id: int
    title: str
    department: str | None
    location: str | None
    employment_type: str | None
    description: str
    status: str
    created_by_id: int
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
