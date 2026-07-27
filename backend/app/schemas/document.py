from typing import Literal
from datetime import datetime
from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
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
class DocumentRenameRequest(BaseModel):
    original_name: str = Field(
        min_length=5,
        max_length=255,
    )
    @field_validator("original_name")
    @classmethod
    def validate_original_name(
        cls,
        value: str,
    ) -> str:
        normalized_name = value.strip()
        if (
            "/" in normalized_name
            or "\\" in normalized_name
            or "\x00" in normalized_name
        ):
            raise ValueError(
                "The document name cannot contain path characters."
            )
        if not normalized_name.lower().endswith(".pdf"):
            raise ValueError(
                "The document name must end with .pdf."
            )
        if normalized_name.lower().endswith(
            ".pdf.pdf"
        ):
            raise ValueError(
                "The document name cannot contain a repeated PDF extension."
            )
        return normalized_name
class DocumentDeleteResult(BaseModel):
    document_id: int
    deleted: bool
    file_deleted: bool
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
class DocumentAskRequest(BaseModel):
    question: str = Field(
        min_length=1,
        max_length=2000,
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
class AnswerCitation(BaseModel):
    source_id: str
    document_id: int
    document_name: str
    page_number: int
    chunk_index: int
    text_preview: str
class DocumentAnswerResponse(BaseModel):
    question: str
    answer: str
    answer_found: bool
    response_type: Literal[
        "conversation",
        "policy_guidance",
        "no_supporting_policy",
    ]
    citations: list[AnswerCitation]
    retrieved_chunks: int
    model: str
