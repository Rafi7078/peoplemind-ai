
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
from backend.app.schemas.candidate import (
    CandidateCVPagePreview,
    CandidateCVProcessResult,
    CandidateCVRead,
)
from backend.app.services.candidate_processing_service import (
    CandidateCVProcessingError,
    list_candidate_cv_pages,
    process_candidate_cv,
)
from backend.app.services.candidate_service import (
    CandidateCVNotFoundError,
    CandidateValidationError,
    DuplicateCandidateCVError,
    list_candidate_cvs,
    store_candidate_cv,
)
router = APIRouter(
    prefix="/api/candidates",
    tags=["Candidate CVs"],
)
@router.post(
    "/upload",
    response_model=CandidateCVRead,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a candidate CV PDF",
    responses={
        400: {
            "description": "Invalid candidate CV"
        },
        409: {
            "description": "Duplicate candidate CV"
        },
    },
)
async def upload_candidate_cv(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
    file: Annotated[
        UploadFile,
        File(
            description=(
                "Candidate curriculum vitae PDF"
            )
        ),
    ],
) -> CandidateCVRead:
    try:
        candidate = await store_candidate_cv(
            upload=file,
            database=database,
            uploaded_by_id=current_user.id,
        )
    except CandidateValidationError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_400_BAD_REQUEST
            ),
            detail=str(error),
        ) from error
    except DuplicateCandidateCVError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
    return CandidateCVRead.model_validate(
        candidate
    )
@router.get(
    "",
    response_model=list[CandidateCVRead],
    summary="List uploaded candidate CVs",
)
def read_candidate_cvs(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[CandidateCVRead]:
    return [
        CandidateCVRead.model_validate(
            candidate
        )
        for candidate in list_candidate_cvs(
            database
        )
    ]
@router.post(
    "/{candidate_id}/process",
    response_model=CandidateCVProcessResult,
    summary="Extract page text from a candidate CV",
)
def process_candidate(
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> CandidateCVProcessResult:
    try:
        result = process_candidate_cv(
            database=database,
            candidate_id=candidate_id,
        )
    except CandidateCVNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except CandidateCVProcessingError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_422_UNPROCESSABLE_ENTITY
            ),
            detail=str(error),
        ) from error
    return (
        CandidateCVProcessResult
        .model_validate(result)
    )
@router.get(
    "/{candidate_id}/pages",
    response_model=list[
        CandidateCVPagePreview
    ],
    summary="Preview extracted candidate CV pages",
)
def read_candidate_pages(
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[CandidateCVPagePreview]:
    try:
        pages = list_candidate_cv_pages(
            database=database,
            candidate_id=candidate_id,
        )
    except CandidateCVNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    return [
        CandidateCVPagePreview(
            page_number=page.page_number,
            char_count=page.char_count,
            text_preview=page.text[:500],
        )
        for page in pages
    ]
