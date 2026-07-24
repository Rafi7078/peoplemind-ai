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
class DocumentProcessResult(BaseModel):
    document_id: int
    status: str
    page_count: int
    text_pages: int
    total_characters: int
class DocumentPagePreview(BaseModel):
    page_number: int
    char_count: int
    text_preview: str
