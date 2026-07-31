
from hashlib import sha256
from pathlib import Path
from uuid import uuid4
from fastapi import UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.candidate_cv import (
    CandidateCV,
)
READ_CHUNK_SIZE = 1024 * 1024
ALLOWED_PDF_CONTENT_TYPES = {
    "application/pdf",
    "application/x-pdf",
    "application/octet-stream",
}
class CandidateValidationError(
    ValueError
):
    pass
class DuplicateCandidateCVError(
    ValueError
):
    def __init__(
        self,
        candidate_id: int,
    ) -> None:
        self.candidate_id = candidate_id
        super().__init__(
            "This candidate CV has already "
            "been uploaded "
            f"(candidate ID: {candidate_id})."
        )
class CandidateCVNotFoundError(
    LookupError
):
    pass
class CandidateCVFileNotFoundError(
    FileNotFoundError
):
    pass
def get_candidate_cv(
    database: Session,
    candidate_id: int,
) -> CandidateCV:
    candidate = database.get(
        CandidateCV,
        candidate_id,
    )
    if candidate is None:
        raise CandidateCVNotFoundError(
            "The requested candidate CV "
            "was not found."
        )
    return candidate
def list_candidate_cvs(
    database: Session,
) -> list[CandidateCV]:
    statement = (
        select(CandidateCV)
        .order_by(
            CandidateCV.created_at.desc()
        )
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
async def store_candidate_cv(
    upload: UploadFile,
    database: Session,
    uploaded_by_id: int,
) -> CandidateCV:
    original_name = Path(
        upload.filename or ""
    ).name
    if not original_name:
        raise CandidateValidationError(
            "The uploaded CV must have a filename."
        )
    if (
        Path(original_name).suffix.lower()
        != ".pdf"
    ):
        raise CandidateValidationError(
            "Only PDF candidate CVs are allowed."
        )
    if (
        upload.content_type
        and upload.content_type
        not in ALLOWED_PDF_CONTENT_TYPES
    ):
        raise CandidateValidationError(
            "The uploaded CV has an "
            "unsupported content type."
        )
    upload_directory = Path(
        settings.candidate_upload_dir
    )
    upload_directory.mkdir(
        parents=True,
        exist_ok=True,
    )
    upload_id = uuid4().hex
    temporary_path = (
        upload_directory
        / f"{upload_id}.part"
    )
    stored_name = f"{upload_id}.pdf"
    final_path = (
        upload_directory
        / stored_name
    )
    maximum_size_bytes = (
        settings.max_candidate_size_mb
        * 1024
        * 1024
    )
    content_hasher = sha256()
    total_size = 0
    first_chunk = True
    try:
        with temporary_path.open(
            "wb"
        ) as output_file:
            while True:
                chunk = await upload.read(
                    READ_CHUNK_SIZE
                )
                if not chunk:
                    break
                if first_chunk:
                    first_chunk = False
                    if not chunk.startswith(
                        b"%PDF-"
                    ):
                        raise CandidateValidationError(
                            "The uploaded CV does not "
                            "contain a valid PDF signature."
                        )
                total_size += len(chunk)
                if (
                    total_size
                    > maximum_size_bytes
                ):
                    raise CandidateValidationError(
                        "The candidate CV exceeds "
                        "the maximum allowed size of "
                        f"{settings.max_candidate_size_mb} MB."
                    )
                content_hasher.update(chunk)
                output_file.write(chunk)
        if total_size == 0:
            raise CandidateValidationError(
                "The uploaded candidate CV is empty."
            )
        file_digest = (
            content_hasher.hexdigest()
        )
        existing_candidate = (
            database.scalar(
                select(CandidateCV).where(
                    CandidateCV.sha256
                    == file_digest
                )
            )
        )
        if existing_candidate is not None:
            raise DuplicateCandidateCVError(
                existing_candidate.id
            )
        temporary_path.replace(
            final_path
        )
        candidate = CandidateCV(
            original_name=original_name,
            stored_name=stored_name,
            file_path=str(final_path),
            sha256=file_digest,
            size_bytes=total_size,
            mime_type=(
                upload.content_type
                or "application/pdf"
            ),
            status="uploaded",
            page_count=None,
            uploaded_by_id=uploaded_by_id,
        )
        try:
            database.add(candidate)
            database.commit()
            database.refresh(candidate)
        except IntegrityError as error:
            database.rollback()
            if final_path.exists():
                final_path.unlink()
            existing_candidate = (
                database.scalar(
                    select(CandidateCV).where(
                        CandidateCV.sha256
                        == file_digest
                    )
                )
            )
            existing_id = (
                existing_candidate.id
                if existing_candidate
                is not None
                else 0
            )
            raise DuplicateCandidateCVError(
                existing_id
            ) from error
        except Exception:
            database.rollback()
            if final_path.exists():
                final_path.unlink()
            raise
        return candidate
    finally:
        if temporary_path.exists():
            temporary_path.unlink()
        await upload.close()

def get_candidate_cv_file(
    database: Session,
    candidate_id: int,
) -> tuple[CandidateCV, Path]:
    candidate = get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    upload_directory = Path(
        settings.candidate_upload_dir
    ).resolve()
    candidate_path = Path(
        candidate.file_path
    ).resolve()
    try:
        candidate_path.relative_to(
            upload_directory
        )
    except ValueError as error:
        raise CandidateCVFileNotFoundError(
            "The candidate CV file path "
            "is outside the secure upload directory."
        ) from error
    if (
        not candidate_path.exists()
        or not candidate_path.is_file()
    ):
        raise CandidateCVFileNotFoundError(
            "The stored candidate CV file "
            "could not be found."
        )
    return candidate, candidate_path
