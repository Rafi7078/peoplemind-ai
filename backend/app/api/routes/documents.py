from typing import Annotated
from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
    status,
)
from backend.app.api.dependencies import (
    CurrentUserDependency,
    DatabaseDependency,
)
from backend.app.schemas.document import (
    DocumentAnswerResponse,
    DocumentAskRequest,
    DocumentChunkPreview,
    DocumentIndexResult,
    DocumentPagePreview,
    DocumentProcessResult,
    DocumentRead,
    DocumentSearchRequest,
    DocumentSearchResult,
)
from backend.app.services import rag_answer_service
from backend.app.services.document_index_service import (
    DocumentIndexingError,
    DocumentSearchError,
    index_document,
    list_document_chunks,
    search_document_chunks,
)
from backend.app.services.document_service import (
    DocumentValidationError,
    DuplicateDocumentError,
    list_documents,
    store_pdf_document,
)
from backend.app.services.pdf_extraction_service import (
    DocumentNotFoundError,
    DocumentProcessingError,
    list_document_pages,
    process_pdf_document,
)
router = APIRouter(
    prefix="/api/documents",
    tags=["Documents"],
)
@router.post(
    "/upload",
    response_model=DocumentRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload an HR PDF document",
    responses={
        400: {"description": "Invalid PDF upload"},
        409: {"description": "Duplicate PDF document"},
    },
)
async def upload_document(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    file: Annotated[
        UploadFile,
        File(
            description=(
                "HR policy or employee handbook PDF"
            )
        ),
    ],
) -> DocumentRead:
    try:
        document = await store_pdf_document(
            upload=file,
            database=database,
            uploaded_by_id=current_user.id,
        )
    except DocumentValidationError as error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(error),
        ) from error
    except DuplicateDocumentError as error:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(error),
        ) from error
    return DocumentRead.model_validate(document)
@router.get(
    "",
    response_model=list[DocumentRead],
    summary="List uploaded HR documents",
)
def read_documents(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[DocumentRead]:
    documents = list_documents(database)
    return [
        DocumentRead.model_validate(document)
        for document in documents
    ]
@router.post(
    "/search",
    response_model=list[DocumentSearchResult],
    summary="Run semantic search over indexed documents",
)
def search_documents(
    request: DocumentSearchRequest,
    current_user: CurrentUserDependency,
) -> list[DocumentSearchResult]:
    try:
        results = search_document_chunks(
            query=request.query,
            document_id=request.document_id,
            top_k=request.top_k,
        )
    except DocumentSearchError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    return [
        DocumentSearchResult.model_validate(result)
        for result in results
    ]
@router.post(
    "/ask",
    response_model=DocumentAnswerResponse,
    summary="Ask an evidence-grounded document question",
)
def ask_documents(
    request: DocumentAskRequest,
    current_user: CurrentUserDependency,
) -> DocumentAnswerResponse:
    try:
        result = (
            rag_answer_service.answer_document_question(
                question=request.question,
                document_id=request.document_id,
                top_k=request.top_k,
            )
        )
    except rag_answer_service.RagAnswerError as error:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(error),
        ) from error
    return DocumentAnswerResponse.model_validate(result)
@router.post(
    "/{document_id}/process",
    response_model=DocumentProcessResult,
    summary="Extract page text from an uploaded PDF",
)
def process_document(
    document_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> DocumentProcessResult:
    try:
        result = process_pdf_document(
            database=database,
            document_id=document_id,
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except DocumentProcessingError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return DocumentProcessResult.model_validate(result)
@router.get(
    "/{document_id}/pages",
    response_model=list[DocumentPagePreview],
    summary="Preview extracted PDF pages",
)
def read_document_pages(
    document_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[DocumentPagePreview]:
    try:
        pages = list_document_pages(
            database=database,
            document_id=document_id,
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return [
        DocumentPagePreview(
            page_number=page.page_number,
            char_count=page.char_count,
            text_preview=page.text[:500],
        )
        for page in pages
    ]
@router.post(
    "/{document_id}/index",
    response_model=DocumentIndexResult,
    summary="Chunk, embed and index a processed PDF",
)
def create_document_index(
    document_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> DocumentIndexResult:
    try:
        result = index_document(
            database=database,
            document_id=document_id,
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    except DocumentIndexingError as error:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(error),
        ) from error
    return DocumentIndexResult.model_validate(result)
@router.get(
    "/{document_id}/chunks",
    response_model=list[DocumentChunkPreview],
    summary="Preview indexed document chunks",
)
def read_document_chunks(
    document_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[DocumentChunkPreview]:
    try:
        chunks = list_document_chunks(
            database=database,
            document_id=document_id,
        )
    except DocumentNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
    return [
        DocumentChunkPreview(
            page_number=chunk.page_number,
            chunk_index=chunk.chunk_index,
            char_count=chunk.char_count,
            text_preview=chunk.text[:500],
        )
        for chunk in chunks
    ]
