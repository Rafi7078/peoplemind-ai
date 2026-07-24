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
from backend.app.schemas.document import DocumentRead
from backend.app.services.document_service import (
    DocumentValidationError,
    DuplicateDocumentError,
    list_documents,
    store_pdf_document,
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
)
async def upload_document(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    file: Annotated[
        UploadFile,
        File(description="HR policy or employee handbook PDF"),
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
