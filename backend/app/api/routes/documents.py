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
    DocumentPagePreview,
    DocumentProcessResult,
    DocumentRead,
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
        400: {
            "description": "Invalid PDF upload",
        },
        409: {
            "description": "Duplicate PDF document",
        },
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
    "/{document_id}/process",
    response_model=DocumentProcessResult,
    summary="Extract page text from an uploaded PDF",
    responses={
        404: {
            "description": "Document not found",
        },
        422: {
            "description": "PDF processing failed",
        },
    },
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
    responses={
        404: {
            "description": "Document not found",
        },
    },
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
