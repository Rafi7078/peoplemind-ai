from datetime import datetime
from pydantic import BaseModel, ConfigDict
class DocumentRead(BaseModel):
    id: int
    original_name: str
    size_bytes: int
    mime_type: str
    status: str
    page_count: int | None
    uploaded_by_id: int
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)
