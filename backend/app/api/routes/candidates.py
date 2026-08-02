from urllib.parse import quote

from typing import Annotated
from fastapi.responses import FileResponse
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
from backend.app.schemas.candidate_ats import (
    CandidateATSRead,
)
from backend.app.schemas.candidate_profile import (
    CandidateProfileRead,
)
from backend.app.services.candidate_processing_service import (
    CandidateCVProcessingError,
    list_candidate_cv_pages,
    process_candidate_cv,
)
from backend.app.services.candidate_service import (
    CandidateCVFileNotFoundError,
    CandidateCVNotFoundError,
    CandidateValidationError,
    DuplicateCandidateCVError,
    delete_candidate_cv_permanently,
    get_candidate_cv_file,
    list_candidate_cvs,
    store_candidate_cv,
)
from backend.app.services.job_candidate_assignment_service import (
    list_unassigned_candidates,
)
from backend.app.services import (
    candidate_ats_service,
    candidate_profile_service,
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

@router.get(
    "/unassigned",
    response_model=list[CandidateCVRead],
    summary="List unassigned candidate CVs",
)
def read_unassigned_candidate_cvs(
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> list[CandidateCVRead]:
    return [
        CandidateCVRead.model_validate(
            candidate
        )
        for candidate
        in list_unassigned_candidates(
            database
        )
    ]
@router.get(
    "/{candidate_id}/file",
    response_class=FileResponse,
    summary="Open the original candidate CV securely",
    responses={
        404: {
            "description": (
                "Candidate or stored PDF file not found"
            )
        },
    },
)
def read_candidate_cv_file(
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> FileResponse:
    try:
        candidate, candidate_path = (
            get_candidate_cv_file(
                database=database,
                candidate_id=candidate_id,
            )
        )
    except (
        CandidateCVNotFoundError,
        CandidateCVFileNotFoundError,
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    encoded_filename = quote(
        candidate.original_name
    )
    return FileResponse(
        path=candidate_path,
        media_type="application/pdf",
        headers={
            "Content-Disposition": (
                "inline; "
                f"filename*=UTF-8''{encoded_filename}"
            ),
            "Cache-Control": (
                "private, no-store, max-age=0"
            ),
        },
    )
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
            text=page.text,
        )
        for page in pages
    ]

@router.post(
    "/{candidate_id}/profile/extract",
    response_model=CandidateProfileRead,
    summary="Extract a structured candidate profile",
)
def extract_structured_candidate_profile(
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> CandidateProfileRead:
    try:
        profile = (
            candidate_profile_service
            .extract_candidate_profile(
                database=database,
                candidate_id=candidate_id,
            )
        )
    except CandidateCVNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        candidate_profile_service
        .CandidateProfilePrerequisiteError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
    except (
        candidate_profile_service
        .CandidateProfileExtractionError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_502_BAD_GATEWAY
            ),
            detail=str(error),
        ) from error
    return CandidateProfileRead.model_validate(
        profile
    )
@router.get(
    "/{candidate_id}/profile",
    response_model=CandidateProfileRead,
    summary="Read a structured candidate profile",
)
def read_structured_candidate_profile(
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> CandidateProfileRead:
    try:
        profile = (
            candidate_profile_service
            .get_candidate_profile(
                database=database,
                candidate_id=candidate_id,
            )
        )
    except CandidateCVNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        candidate_profile_service
        .CandidateProfileNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    return CandidateProfileRead.model_validate(
        profile
    )


@router.post(
    "/{candidate_id}/ats/analyze",
    response_model=CandidateATSRead,
    summary="Run ATS compatibility analysis",
)
def analyze_candidate_ats_result(
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> CandidateATSRead:
    try:
        result = (
            candidate_ats_service
            .analyze_candidate_ats(
                database=database,
                candidate_id=candidate_id,
            )
        )
    except CandidateCVNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        candidate_ats_service
        .CandidateATSPrerequisiteError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
    return CandidateATSRead.model_validate(
        result
    )
@router.get(
    "/{candidate_id}/ats",
    response_model=CandidateATSRead,
    summary="Read ATS compatibility result",
)
def read_candidate_ats_result(
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> CandidateATSRead:
    try:
        result = (
            candidate_ats_service
            .get_candidate_ats_result(
                database=database,
                candidate_id=candidate_id,
            )
        )
    except CandidateCVNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    except (
        candidate_ats_service
        .CandidateATSNotFoundError
    ) as error:
        raise HTTPException(
            status_code=(
                status.HTTP_404_NOT_FOUND
            ),
            detail=str(error),
        ) from error
    return CandidateATSRead.model_validate(
        result
    )
@router.delete(
    "/{candidate_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Permanently delete a candidate CV",
)
def delete_candidate_permanently(
    candidate_id: int,
    current_user: CurrentUserDependency,
    database: DatabaseDependency,
) -> None:
    try:
        delete_candidate_cv_permanently(
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
    except CandidateCVFileNotFoundError as error:
        raise HTTPException(
            status_code=(
                status.HTTP_409_CONFLICT
            ),
            detail=str(error),
        ) from error
