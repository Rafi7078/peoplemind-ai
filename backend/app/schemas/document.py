from datetime import datetime
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
)
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
class DocumentIndexResult(BaseModel):
    document_id: int
    status: str
    chunk_count: int
    vector_dimension: int
    total_characters: int
class DocumentChunkPreview(BaseModel):
    page_number: int
    chunk_index: int
    char_count: int
    text_preview: str
class DocumentSearchRequest(BaseModel):
    query: str = Field(
        min_length=2,
        max_length=1000,
    )
    document_id: int | None = Field(
        default=None,
        ge=1,
    )
    top_k: int = Field(
        default=5,
        ge=1,
        le=10,
    )
class DocumentSearchResult(BaseModel):
    vector_id: str
    document_id: int
    document_name: str
    page_number: int
    chunk_index: int
    distance: float
    text: str
