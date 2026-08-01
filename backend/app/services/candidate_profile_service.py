
import re
from threading import Lock
from datetime import (
    datetime,
    timezone,
)
from dateutil import parser as date_parser
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.core.config import settings
from backend.app.models.candidate_cv_page import (
    CandidateCVPage,
)
from backend.app.models.candidate_profile import (
    CandidateProfile,
)
from backend.app.schemas.candidate_profile import (
    CandidateProfileData,
)
from backend.app.services.candidate_profile_ai_service import (
    CandidateProfileAIError,
    generate_candidate_profile,
)
from backend.app.services.candidate_profile_parser_service import (
    merge_candidate_profiles,
    parse_candidate_profile,
    profile_needs_ai_fallback,
)
from backend.app.services.candidate_service import (
    get_candidate_cv,
)
MAX_PROFILE_SOURCE_CHARACTERS = 50_000
PROFILE_EXTRACTION_LOCK = Lock()
PRESENT_DATE_VALUES = {
    "present",
    "current",
    "currently",
    "now",
    "ongoing",
}
MONTH_NAME_PATTERN = re.compile(
    (
        r"\b(?:jan(?:uary)?|feb(?:ruary)?|"
        r"mar(?:ch)?|apr(?:il)?|may|"
        r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|"
        r"sep(?:tember)?|sept(?:ember)?|"
        r"oct(?:ober)?|nov(?:ember)?|"
        r"dec(?:ember)?)\b"
    ),
    flags=re.IGNORECASE,
)
NUMERIC_MONTH_YEAR_PATTERN = re.compile(
    (
        r"(?:\b(?:0?[1-9]|1[0-2])"
        r"[-/.]\d{4}\b)"
        r"|"
        r"(?:\b\d{4}[-/.]"
        r"(?:0?[1-9]|1[0-2])\b)"
    )
)
class CandidateProfileNotFoundError(
    LookupError
):
    pass
class CandidateProfilePrerequisiteError(
    ValueError
):
    pass
class CandidateProfileExtractionError(
    RuntimeError
):
    pass
SECTION_ALIASES = {
    "summary": {
        "summary",
        "professional summary",
        "career summary",
        "profile",
        "professional profile",
        "career objective",
        "objective",
        "about me",
    },
    "work_experience": {
        "experience",
        "work experience",
        "work experiences",
        "professional experience",
        "employment history",
        "career history",
        "internship experience",
        "key professional experience",
        "key professional experiences",
        "professional experiences",
        "work exprrience",
        "work exprriences",
    },
    "education": {
        "education",
        "educational qualification",
        "educational qualifications",
        "academic qualification",
        "academic qualifications",
        "academic background",
    },
    "skills": {
        "skills",
        "technical skills",
        "non technical skills",
        "core skills",
        "key skills",
        "core competencies",
        "tools and technologies",
        "technical proficiency",
    },
    "projects": {
        "projects",
        "project",
        "academic projects",
        "personal projects",
        "professional projects",
        "selected projects",
    },
    "certifications": {
        "certification",
        "certifications",
        "courses and certifications",
        "training and certifications",
        "professional certifications",
        "certifications & professional training",
        "certifications and professional training",
        "certification & professional training",
        "certification and professional training",
    },
    "languages": {
        "language",
        "languages",
        "language proficiency",
    },
    "references": {
        "reference",
        "references",
    },
    "interests": {
        "interests",
        "hobbies",
        "activities",
        "extracurricular activities",
    },
}
TARGET_PROFILE_SECTIONS = (
    "work_experience",
    "education",
    "skills",
    "projects",
    "certifications",
)
SECTION_DISPLAY_NAMES = {
    "work_experience": "WORK EXPERIENCE",
    "education": "EDUCATION",
    "skills": "SKILLS",
    "projects": "PROJECTS",
    "certifications": "CERTIFICATIONS",
}
SECTION_CHARACTER_LIMITS = {
    "work_experience": 3500,
    "education": 1800,
    "skills": 1800,
    "projects": 2200,
    "certifications": 1800,
}
CONTACT_SIGNAL_PATTERN = re.compile(
    (
        r"@"
        r"|https?://"
        r"|www\."
        r"|linkedin"
        r"|github"
        r"|portfolio"
        r"|\b\d{7,}\b"
    ),
    flags=re.IGNORECASE,
)
def normalize_profile_source_line(
    value: str,
) -> str:
    normalized_value = (
        value
        .replace("\u2022", " ")
        .replace("\u25cf", " ")
        .replace("\u25aa", " ")
        .replace("\uf0b7", " ")
        .replace("\t", " ")
    )
    return re.sub(
        r"\s+",
        " ",
        normalized_value,
    ).strip(
        " |:-"
    )
def normalize_section_heading(
    value: str,
) -> str:
    normalized_value = re.sub(
        r"[^a-z0-9+#& ]+",
        " ",
        value.casefold(),
    )
    return re.sub(
        r"\s+",
        " ",
        normalized_value,
    ).strip()
def detect_profile_section(
    line: str,
) -> str | None:
    heading = normalize_section_heading(
        line
    )
    if not heading:
        return None
    for (
        section_name,
        aliases,
    ) in SECTION_ALIASES.items():
        if heading in aliases:
            return section_name
    return None
def deduplicate_profile_lines(
    lines: list[str],
) -> list[str]:
    unique_lines: list[str] = []
    seen_lines: set[str] = set()
    for line in lines:
        normalized_key = line.casefold()
        if normalized_key in seen_lines:
            continue
        seen_lines.add(
            normalized_key
        )
        unique_lines.append(
            line
        )
    return unique_lines
def build_compact_candidate_source(
    pages: list[CandidateCVPage],
) -> str:
    all_lines: list[str] = []
    for page in pages:
        for raw_line in page.text.splitlines():
            line = normalize_profile_source_line(
                raw_line
            )
            if line:
                all_lines.append(
                    line
                )
    if not all_lines:
        return ""
    header_lines: list[str] = []
    for line in all_lines[:40]:
        if len(header_lines) < 4:
            header_lines.append(
                line
            )
        if CONTACT_SIGNAL_PATTERN.search(
            line
        ):
            header_lines.append(
                line
            )
    header_lines = (
        deduplicate_profile_lines(
            header_lines
        )
    )
    section_lines: dict[
        str,
        list[str],
    ] = {
        section_name: []
        for section_name
        in TARGET_PROFILE_SECTIONS
    }
    current_section: str | None = None
    for line in all_lines:
        detected_section = (
            detect_profile_section(
                line
            )
        )
        if detected_section is not None:
            current_section = (
                detected_section
            )
            continue
        if (
            current_section
            in section_lines
        ):
            section_lines[
                current_section
            ].append(
                line
            )
    evidence_blocks: list[str] = []
    if header_lines:
        evidence_blocks.append(
            "[CANDIDATE HEADER AND CONTACT]\n"
            + "\n".join(
                header_lines
            )[:1200]
        )
    for section_name in (
        TARGET_PROFILE_SECTIONS
    ):
        lines = deduplicate_profile_lines(
            section_lines[
                section_name
            ]
        )
        if not lines:
            continue
        section_text = "\n".join(
            lines
        )
        character_limit = (
            SECTION_CHARACTER_LIMITS[
                section_name
            ]
        )
        evidence_blocks.append(
            (
                f"[{SECTION_DISPLAY_NAMES[section_name]}]\n"
                f"{section_text[:character_limit]}"
            )
        )
    if len(evidence_blocks) <= 1:
        fallback_text = "\n".join(
            deduplicate_profile_lines(
                all_lines
            )
        )
        return (
            "[CV TEXT]\n"
            + fallback_text[
                :MAX_PROFILE_SOURCE_CHARACTERS
            ]
        )
    return "\n\n".join(
        evidence_blocks
    )
def build_candidate_profile_source(
    database: Session,
    candidate_id: int,
) -> str:
    candidate = get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    if candidate.status != "ready":
        raise CandidateProfilePrerequisiteError(
            "The candidate CV must be processed "
            "successfully before profile extraction."
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
    pages = list(
        database.scalars(
            statement
        ).all()
    )
    if not any(
        page.text.strip()
        for page in pages
    ):
        raise CandidateProfilePrerequisiteError(
            "No selectable CV text is available "
            "for structured profile extraction."
        )
    source_text = (
        build_compact_candidate_source(
            pages
        )
    )
    if not source_text.strip():
        raise CandidateProfilePrerequisiteError(
            "No relevant CV information was found "
            "for structured profile extraction."
        )
    if (
        len(source_text)
        > MAX_PROFILE_SOURCE_CHARACTERS
    ):
        raise CandidateProfilePrerequisiteError(
            "The extracted CV text is too large "
            "for structured profile extraction."
        )
    print(
        "[PERF] Candidate profile source: "
        f"candidate_id={candidate_id} | "
        f"compact_chars={len(source_text)}",
        flush=True,
    )
    return source_text

def parse_month_value(
    value: str | None,
    allow_present: bool = False,
) -> tuple[int, int] | None:
    if value is None:
        return None
    normalized_value = value.strip()
    if not normalized_value:
        return None
    if (
        allow_present
        and normalized_value.casefold()
        in PRESENT_DATE_VALUES
    ):
        current_date = datetime.now(
            timezone.utc
        )
        return (
            current_date.year,
            current_date.month,
        )
    has_month = bool(
        MONTH_NAME_PATTERN.search(
            normalized_value
        )
        or NUMERIC_MONTH_YEAR_PATTERN.search(
            normalized_value
        )
    )
    if not has_month:
        return None
    try:
        parsed_value = date_parser.parse(
            normalized_value,
            fuzzy=True,
            default=datetime(
                2000,
                1,
                1,
            ),
        )
    except (
        ValueError,
        TypeError,
        OverflowError,
    ):
        return None
    return (
        parsed_value.year,
        parsed_value.month,
    )
def format_month_duration(
    total_months: int,
) -> str:
    years, months = divmod(
        total_months,
        12,
    )
    parts: list[str] = []
    if years:
        parts.append(
            (
                f"{years} year"
                if years == 1
                else f"{years} years"
            )
        )
    if months:
        parts.append(
            (
                f"{months} month"
                if months == 1
                else f"{months} months"
            )
        )
    return " ".join(parts)
def calculate_experience_duration(
    start_date: str | None,
    end_date: str | None,
) -> str:
    start_month = parse_month_value(
        start_date
    )
    end_month = parse_month_value(
        end_date,
        allow_present=True,
    )
    if (
        start_month is None
        or end_month is None
    ):
        return "Not confirmed"
    start_year, start_month_number = (
        start_month
    )
    end_year, end_month_number = (
        end_month
    )
    total_months = (
        (end_year - start_year) * 12
        + end_month_number
        - start_month_number
        + 1
    )
    if total_months <= 0:
        return "Not confirmed"
    return format_month_duration(
        total_months
    )
def add_calculated_durations(
    profile_data: CandidateProfileData,
) -> CandidateProfileData:
    updated_profile = (
        profile_data.model_copy(
            deep=True
        )
    )
    for experience in (
        updated_profile.work_experience
    ):
        experience.duration = (
            calculate_experience_duration(
                start_date=(
                    experience.start_date
                ),
                end_date=(
                    experience.end_date
                ),
            )
        )
    return updated_profile
def extract_candidate_profile(
    database: Session,
    candidate_id: int,
) -> CandidateProfile:
    source_text = (
        build_candidate_profile_source(
            database=database,
            candidate_id=candidate_id,
        )
    )
    deterministic_data = (
        parse_candidate_profile(
            source_text
        )
    )
    extraction_model_name = (
        "deterministic-parser-v5"
    )
    if profile_needs_ai_fallback(
        deterministic_data
    ):
        try:
            with PROFILE_EXTRACTION_LOCK:
                ai_data = (
                    generate_candidate_profile(
                        source_text
                    )
                )
        except CandidateProfileAIError as error:
            raise CandidateProfileExtractionError(
                str(error)
            ) from error
        extracted_data = (
            merge_candidate_profiles(
                deterministic_profile=(
                    deterministic_data
                ),
                ai_profile=ai_data,
            )
        )
        extraction_model_name = (
            "deterministic-parser-v5"
            f"+{settings.ollama_chat_model}"
        )
    else:
        extracted_data = (
            deterministic_data
        )
    profile_data = (
        add_calculated_durations(
            extracted_data
        )
    )
    profile_payload = (
        profile_data.model_dump(
            mode="json"
        )
    )
    statement = (
        select(CandidateProfile)
        .where(
            CandidateProfile.candidate_cv_id
            == candidate_id
        )
    )
    profile = database.scalar(
        statement
    )
    if profile is None:
        profile = CandidateProfile(
            candidate_cv_id=candidate_id,
            candidate_name=(
                profile_payload[
                    "candidate_name"
                ]
            ),
            contact_information=(
                profile_payload[
                    "contact_information"
                ]
            ),
            latest_completed_education=(
                profile_payload[
                    "latest_completed_education"
                ]
            ),
            work_experience=(
                profile_payload[
                    "work_experience"
                ]
            ),
            skills=profile_payload[
                "skills"
            ],
            projects=profile_payload[
                "projects"
            ],
            certifications=(
                profile_payload[
                    "certifications"
                ]
            ),
            extraction_model=(
                extraction_model_name
            ),
        )
        database.add(profile)
    else:
        profile.candidate_name = (
            profile_payload[
                "candidate_name"
            ]
        )
        profile.contact_information = (
            profile_payload[
                "contact_information"
            ]
        )
        profile.latest_completed_education = (
            profile_payload[
                "latest_completed_education"
            ]
        )
        profile.work_experience = (
            profile_payload[
                "work_experience"
            ]
        )
        profile.skills = profile_payload[
            "skills"
        ]
        profile.projects = profile_payload[
            "projects"
        ]
        profile.certifications = (
            profile_payload[
                "certifications"
            ]
        )
        profile.extraction_model = (
            extraction_model_name
        )
    try:
        database.commit()
        database.refresh(profile)
    except Exception:
        database.rollback()
        raise
    return profile
def get_candidate_profile(
    database: Session,
    candidate_id: int,
) -> CandidateProfile:
    get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    statement = (
        select(CandidateProfile)
        .where(
            CandidateProfile.candidate_cv_id
            == candidate_id
        )
    )
    profile = database.scalar(
        statement
    )
    if profile is None:
        raise CandidateProfileNotFoundError(
            "A structured profile has not "
            "been extracted for this candidate."
        )
    return profile
