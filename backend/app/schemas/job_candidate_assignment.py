
from datetime import datetime
from pydantic import (
    BaseModel,
    ConfigDict,
)
class JobCandidateAssignmentRead(
    BaseModel
):
    id: int
    job_profile_id: int
    candidate_cv_id: int
    assigned_by_id: int
    created_at: datetime
    model_config = ConfigDict(
        from_attributes=True
    )
