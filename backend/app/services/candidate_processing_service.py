
import re
from typing import Any
from pathlib import Path
from pypdf import PdfReader
from pypdf.errors import PdfReadError
from sqlalchemy import delete, select
from sqlalchemy.orm import Session
from backend.app.models.candidate_cv import (
    CandidateCV,
)
from backend.app.models.candidate_cv_page import (
    CandidateCVPage,
)
from backend.app.models.candidate_profile import (
    CandidateProfile,
)
from backend.app.models.candidate_ats_result import (
    CandidateATSResult,
)
from backend.app.services.candidate_service import (
    CandidateCVNotFoundError,
    get_candidate_cv,
)
class CandidateCVProcessingError(
    ValueError
):
    pass
def extract_candidate_page_text(
    page: Any,
) -> str:
    try:
        return (
            page.extract_text(
                extraction_mode="layout",
                layout_mode_space_vertically=False,
            )
            or ""
        )
    except KeyError as error:
        if error.args != ("/Contents",):
            raise
        return page.extract_text() or ""
def clean_candidate_extracted_text(
    text: str,
) -> str:
    cleaned_text = (
        text
        .replace("\x00", "")
        .replace("\ufeff", "")
        .replace("\ufffe", "-")
        .replace("\u00ad", "-")
    )
    cleaned_text = re.sub(
        r"-[ \t]*\n[ \t]*(?=\w)",
        "-",
        cleaned_text,
    )
    lines = [
        line.rstrip()
        for line in cleaned_text.splitlines()
    ]
    normalized_text = "\n".join(
        lines
    )
    normalized_text = re.sub(
        r"\n{4,}",
        "\n\n\n",
        normalized_text,
    )
    return normalized_text.strip()
def mark_candidate_failed(
    database: Session,
    candidate_id: int,
) -> None:
    database.rollback()
    candidate = database.get(
        CandidateCV,
        candidate_id,
    )
    if candidate is not None:
        candidate.status = "failed"
        database.commit()
def process_candidate_cv(
    database: Session,
    candidate_id: int,
) -> dict[str, int | str]:
    candidate = get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    file_path = Path(
        candidate.file_path
    )
    if not file_path.exists():
        candidate.status = "failed"
        database.commit()
        raise CandidateCVProcessingError(
            "The stored candidate CV "
            "could not be found."
        )
    candidate.status = "processing"
    database.commit()
    try:
        reader = PdfReader(
            str(file_path)
        )
        if reader.is_encrypted:
            raise CandidateCVProcessingError(
                "Password-protected candidate "
                "CVs are not supported."
            )
        if len(reader.pages) == 0:
            raise CandidateCVProcessingError(
                "The candidate CV does not "
                "contain any pages."
            )
        extracted_pages: list[
            CandidateCVPage
        ] = []
        total_characters = 0
        text_pages = 0
        for page_number, page in enumerate(
            reader.pages,
            start=1,
        ):
            extracted_text = (
                extract_candidate_page_text(
                    page
                )
            )
            cleaned_text = (
                clean_candidate_extracted_text(
                    extracted_text
                )
            )
            character_count = len(
                cleaned_text
            )
            total_characters += (
                character_count
            )
            if character_count > 0:
                text_pages += 1
            extracted_pages.append(
                CandidateCVPage(
                    candidate_cv_id=(
                        candidate.id
                    ),
                    page_number=page_number,
                    text=cleaned_text,
                    char_count=(
                        character_count
                    ),
                )
            )
        database.execute(
            delete(
                CandidateCVPage
            ).where(
                CandidateCVPage.candidate_cv_id
                == candidate.id
            )
        )
        database.execute(
            delete(
                CandidateATSResult
            ).where(
                CandidateATSResult
                .candidate_cv_id
                == candidate.id
            )
        )
        database.execute(
            delete(
                CandidateProfile
            ).where(
                CandidateProfile.candidate_cv_id
                == candidate.id
            )
        )
        database.add_all(
            extracted_pages
        )
        candidate.page_count = len(
            extracted_pages
        )
        candidate.status = (
            "ready"
            if total_characters > 0
            else "needs_ocr"
        )
        database.commit()
        database.refresh(candidate)
        return {
            "candidate_id": candidate.id,
            "status": candidate.status,
            "page_count": (
                candidate.page_count
            ),
            "text_pages": text_pages,
            "total_characters": (
                total_characters
            ),
        }
    except CandidateCVProcessingError:
        mark_candidate_failed(
            database=database,
            candidate_id=candidate_id,
        )
        raise
    except (
        PdfReadError,
        OSError,
        ValueError,
        TypeError,
    ) as error:
        mark_candidate_failed(
            database=database,
            candidate_id=candidate_id,
        )
        raise CandidateCVProcessingError(
            "The candidate CV could not "
            "be processed."
        ) from error
    except Exception as error:
        mark_candidate_failed(
            database=database,
            candidate_id=candidate_id,
        )
        raise CandidateCVProcessingError(
            "An unexpected candidate CV "
            "processing error occurred."
        ) from error
def list_candidate_cv_pages(
    database: Session,
    candidate_id: int,
) -> list[CandidateCVPage]:
    get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    statement = (
        select(CandidateCVPage)
        .where(
            CandidateCVPage.candidate_cv_id
            == candidate_id
        )
        .order_by(
            CandidateCVPage.page_number
        )
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
