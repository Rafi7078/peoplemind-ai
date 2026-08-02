
import re
from datetime import (
    datetime,
    timezone,
)
from sqlalchemy import select
from sqlalchemy.orm import Session
from backend.app.models.candidate_ats_result import (
    CandidateATSResult,
)
from backend.app.models.candidate_cv_page import (
    CandidateCVPage,
)
from backend.app.services.candidate_service import (
    get_candidate_cv,
)
ATS_ENGINE_VERSION = (
    "deterministic-ats-v1.1"
)
class CandidateATSNotFoundError(
    LookupError
):
    pass
class CandidateATSPrerequisiteError(
    ValueError
):
    pass
EMAIL_PATTERN = re.compile(
    (
        r"\b[A-Z0-9._%+-]+"
        r"@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    ),
    flags=re.IGNORECASE,
)
PHONE_PATTERN = re.compile(
    (
        r"(?<!\d)"
        r"(?:\+?\d[\d\s().-]{7,}\d)"
        r"(?!\d)"
    )
)
PROFESSIONAL_LINK_PATTERN = re.compile(
    (
        r"linkedin\.com"
        r"|github\.com"
        r"|portfolio"
        r"|behance\.net"
        r"|dribbble\.com"
    ),
    flags=re.IGNORECASE,
)
SUSPICIOUS_PROFESSIONAL_LINK_PATTERN = re.compile(
    (
        r"(?:linkedin\.com|github\.com|"
        r"behance\.net|dribbble\.com)"
        r"[^\s]*\d{7,}"
    ),
    flags=re.IGNORECASE,
)
PAGE_MARKER_PATTERN = re.compile(
    (
        r"^\s*\d+\s*\|\s*"
        r"p\s*a\s*g\s*e\s*$"
    ),
    flags=(
        re.IGNORECASE
        | re.MULTILINE
    ),
)
YEAR_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}\b"
)
MONTH_TOKEN = (
    r"(?:jan(?:uary)?"
    r"|feb(?:ruary)?"
    r"|mar(?:ch)?"
    r"|apr(?:il)?"
    r"|may"
    r"|jun(?:e)?"
    r"|jul(?:y)?"
    r"|aug(?:ust)?"
    r"|sep(?:tember)?"
    r"|sept(?:ember)?"
    r"|oct(?:ober)?"
    r"|nov(?:ember)?"
    r"|dec(?:ember)?)"
)
DATE_RANGE_PATTERN = re.compile(
    (
        rf"\b(?:(?P<start_month>{MONTH_TOKEN})"
        rf"\s+)?"
        rf"(?P<start_year>(?:19|20)\d{{2}})"
        rf"\s*(?:-|\u2013|\u2014|to)\s*"
        rf"(?:"
        rf"(?:(?P<end_month>{MONTH_TOKEN})"
        rf"\s+)?"
        rf"(?P<end_year>(?:19|20)\d{{2}})"
        rf"|"
        rf"(?P<present>present|current|now)"
        rf")\b"
    ),
    flags=re.IGNORECASE,
)
MONTH_NUMBERS = {
    "jan": 1,
    "feb": 2,
    "mar": 3,
    "apr": 4,
    "may": 5,
    "jun": 6,
    "jul": 7,
    "aug": 8,
    "sep": 9,
    "oct": 10,
    "nov": 11,
    "dec": 12,
}
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
    "experience": {
        "experience",
        "work experience",
        "work experiences",
        "professional experience",
        "professional experiences",
        "employment history",
        "career history",
        "internship experience",
        "key professional experience",
        "key professional experiences",
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
        "core skills",
        "key skills",
        "core competencies",
        "tools and technologies",
        "technical proficiency",
    },
    "projects": {
        "project",
        "projects",
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
    },
}
def normalize_heading(
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
def detect_sections(
    lines: list[str],
) -> dict[str, bool]:
    normalized_lines = [
        normalize_heading(line)
        for line in lines
        if len(line.strip()) <= 80
    ]
    detected_sections: dict[
        str,
        bool,
    ] = {}
    for (
        section_name,
        aliases,
    ) in SECTION_ALIASES.items():
        detected_sections[
            section_name
        ] = any(
            line in aliases
            for line in normalized_lines
        )
    return detected_sections
def status_from_points(
    points_awarded: int,
    maximum_points: int,
) -> str:
    if maximum_points <= 0:
        return "pass"
    ratio = (
        points_awarded
        / maximum_points
    )
    if ratio >= 0.80:
        return "pass"
    if ratio >= 0.50:
        return "warning"
    return "fail"
def create_check(
    check_id: str,
    category: str,
    title: str,
    points_awarded: int,
    maximum_points: int,
    message: str,
    evidence: list[str] | None = None,
) -> dict:
    return {
        "check_id": check_id,
        "category": category,
        "title": title,
        "status": status_from_points(
            points_awarded,
            maximum_points,
        ),
        "points_awarded": (
            points_awarded
        ),
        "max_points": maximum_points,
        "message": message,
        "evidence": evidence or [],
    }
def rating_from_score(
    score: int,
) -> str:
    if score >= 90:
        return "Excellent"
    if score >= 75:
        return "Good"
    if score >= 55:
        return "Needs improvement"
    return "Poor"
def risk_level_from_score(
    score: int,
) -> str:
    if score >= 90:
        return "low"
    if score >= 75:
        return "low-to-moderate"
    if score >= 55:
        return "moderate"
    return "high"
def month_number(
    month_value: str | None,
) -> int:
    if not month_value:
        return 1
    return MONTH_NUMBERS.get(
        month_value[:3].casefold(),
        1,
    )
def inspect_date_ranges(
    text: str,
) -> tuple[int, int]:
    range_count = 0
    reversed_count = 0
    current_date = datetime.now(
        timezone.utc
    )
    for match in (
        DATE_RANGE_PATTERN.finditer(
            text
        )
    ):
        range_count += 1
        start_value = (
            int(
                match.group(
                    "start_year"
                )
            ),
            month_number(
                match.group(
                    "start_month"
                )
            ),
        )
        if match.group("present"):
            end_value = (
                current_date.year,
                current_date.month,
            )
        else:
            end_year = match.group(
                "end_year"
            )
            if end_year is None:
                continue
            end_value = (
                int(end_year),
                month_number(
                    match.group(
                        "end_month"
                    )
                ),
            )
        if start_value > end_value:
            reversed_count += 1
    return (
        range_count,
        reversed_count,
    )
def build_ats_analysis(
    pages: list[CandidateCVPage],
) -> dict:
    page_count = len(pages)
    text_pages = [
        page
        for page in pages
        if page.text.strip()
    ]
    combined_text = "\n".join(
        page.text.strip()
        for page in text_pages
    )
    lines = [
        line.strip()
        for line
        in combined_text.splitlines()
        if line.strip()
    ]
    total_characters = len(
        combined_text
    )
    word_count = len(
        re.findall(
            r"\b[\w+#.-]+\b",
            combined_text,
        )
    )
    text_page_count = len(
        text_pages
    )
    average_characters = (
        total_characters
        // max(
            text_page_count,
            1,
        )
    )
    # --------------------------------------------------------
    # MACHINE READABILITY ? 25 points
    # --------------------------------------------------------
    if total_characters >= 1000:
        character_points = 15
    elif total_characters >= 500:
        character_points = 12
    elif total_characters >= 250:
        character_points = 8
    elif total_characters >= 100:
        character_points = 5
    else:
        character_points = 2
    page_coverage_ratio = (
        text_page_count
        / max(page_count, 1)
    )
    if page_coverage_ratio == 1:
        coverage_points = 5
    elif page_coverage_ratio >= 0.75:
        coverage_points = 3
    else:
        coverage_points = 0
    if average_characters >= 350:
        density_points = 5
    elif average_characters >= 150:
        density_points = 3
    else:
        density_points = 1
    readability_score = (
        character_points
        + coverage_points
        + density_points
    )
    # --------------------------------------------------------
    # CONTACT COMPLETENESS ? 15 points
    # --------------------------------------------------------
    has_email = bool(
        EMAIL_PATTERN.search(
            combined_text
        )
    )
    has_phone = bool(
        PHONE_PATTERN.search(
            combined_text
        )
    )
    has_professional_link = bool(
        PROFESSIONAL_LINK_PATTERN.search(
            combined_text
        )
    )
    has_suspicious_professional_link = bool(
        SUSPICIOUS_PROFESSIONAL_LINK_PATTERN
        .search(
            combined_text
        )
    )
    professional_link_points = (
        0
        if not has_professional_link
        else (
            2
            if has_suspicious_professional_link
            else 4
        )
    )
    contact_score = (
        (6 if has_email else 0)
        + (5 if has_phone else 0)
        + professional_link_points
    )
    # --------------------------------------------------------
    # STANDARD SECTIONS ? 20 points
    # --------------------------------------------------------
    detected_sections = (
        detect_sections(lines)
    )
    has_experience_or_projects = (
        detected_sections["experience"]
        or detected_sections["projects"]
    )
    section_score = (
        (
            6
            if has_experience_or_projects
            else 0
        )
        + (
            5
            if detected_sections[
                "education"
            ]
            else 0
        )
        + (
            5
            if detected_sections["skills"]
            else 0
        )
        + (
            4
            if (
                detected_sections["summary"]
                or detected_sections[
                    "certifications"
                ]
                or detected_sections[
                    "projects"
                ]
            )
            else 0
        )
    )
    # --------------------------------------------------------
    # CONTENT STRUCTURE ? 20 points
    # --------------------------------------------------------
    if 250 <= word_count <= 1200:
        length_points = 6
    elif 150 <= word_count <= 1800:
        length_points = 4
    else:
        length_points = 2
    bullet_lines = [
        line
        for line in lines
        if line.lstrip().startswith(
            (
                "-",
                "*",
                "?",
                "?",
                "?",
                "?",
            )
        )
    ]
    if len(bullet_lines) >= 4:
        bullet_points = 5
    elif len(bullet_lines) >= 2:
        bullet_points = 3
    elif len(bullet_lines) == 1:
        bullet_points = 1
    else:
        bullet_points = 0
    detected_section_count = sum(
        1
        for value
        in detected_sections.values()
        if value
    )
    if detected_section_count >= 4:
        organization_points = 5
    elif detected_section_count >= 3:
        organization_points = 4
    elif detected_section_count >= 2:
        organization_points = 2
    else:
        organization_points = 0
    (
        date_range_count,
        reversed_date_range_count,
    ) = inspect_date_ranges(
        combined_text
    )
    year_values = [
        int(value)
        for value
        in YEAR_PATTERN.findall(
            combined_text
        )
    ]
    if date_range_count >= 1:
        date_structure_points = 4
    elif len(year_values) >= 2:
        date_structure_points = 2
    else:
        date_structure_points = 0
    content_structure_score = (
        length_points
        + bullet_points
        + organization_points
        + date_structure_points
    )
    # --------------------------------------------------------
    # DATE CONSISTENCY ? 10 points
    # --------------------------------------------------------
    current_year = datetime.now(
        timezone.utc
    ).year
    impossible_years = sorted({
        year
        for year in year_values
        if (
            year < 1950
            or year > current_year + 1
        )
    })
    if not year_values:
        date_consistency_score = 3
    else:
        date_consistency_score = 10
        if impossible_years:
            date_consistency_score -= 5
        if reversed_date_range_count:
            date_consistency_score -= 5
        date_consistency_score = max(
            date_consistency_score,
            0,
        )
    # --------------------------------------------------------
    # LAYOUT AND PARSING RISK ? 10 points
    # --------------------------------------------------------
    corrupted_character_count = sum(
        combined_text.count(
            marker
        )
        for marker in (
            "?",
            "\x00",
            "\ufeff",
            "\ufffe",
        )
    )
    page_marker_count = len(
        PAGE_MARKER_PATTERN.findall(
            combined_text
        )
    )
    if corrupted_character_count == 0:
        corruption_points = 4
    elif corrupted_character_count <= 2:
        corruption_points = 2
    else:
        corruption_points = 0
    long_line_count = sum(
        1
        for line in lines
        if len(line) > 250
    )
    long_line_ratio = (
        long_line_count
        / max(len(lines), 1)
    )
    if long_line_ratio <= 0.05:
        line_length_points = 3
    elif long_line_ratio <= 0.20:
        line_length_points = 1
    else:
        line_length_points = 0
    short_fragment_count = sum(
        1
        for line in lines
        if len(line) <= 2
    )
    short_fragment_ratio = (
        short_fragment_count
        / max(len(lines), 1)
    )
    if short_fragment_ratio <= 0.05:
        fragment_points = 3
    elif short_fragment_ratio <= 0.15:
        fragment_points = 1
    else:
        fragment_points = 0
    layout_score = max(
        (
            corruption_points
            + line_length_points
            + fragment_points
            - min(
                page_marker_count,
                2,
            )
        ),
        0,
    )
    category_scores = {
        "machine_readability": (
            readability_score
        ),
        "contact_information": (
            contact_score
        ),
        "standard_sections": (
            section_score
        ),
        "content_structure": (
            content_structure_score
        ),
        "date_consistency": (
            date_consistency_score
        ),
        "layout_and_parsing": (
            layout_score
        ),
    }
    total_score = sum(
        category_scores.values()
    )
    checks = [
        create_check(
            check_id=(
                "machine-readability"
            ),
            category=(
                "Machine readability"
            ),
            title=(
                "Selectable and extractable text"
            ),
            points_awarded=(
                readability_score
            ),
            maximum_points=25,
            message=(
                f"Extracted {total_characters} "
                f"characters from "
                f"{text_page_count} of "
                f"{page_count} page(s)."
            ),
            evidence=[
                (
                    "Average extracted characters "
                    f"per text page: "
                    f"{average_characters}"
                ),
            ],
        ),
        create_check(
            check_id=(
                "contact-information"
            ),
            category=(
                "Contact information"
            ),
            title=(
                "ATS-readable contact details"
            ),
            points_awarded=(
                contact_score
            ),
            maximum_points=15,
            message=(
                "Contact fields were checked "
                "for an email address, phone "
                "number and professional link."
            ),
            evidence=[
                f"Email: {'found' if has_email else 'missing'}",
                f"Phone: {'found' if has_phone else 'missing'}",
                (
                    "Professional link: "
                    + (
                        "missing"
                        if not has_professional_link
                        else (
                            "found, but URL looks suspicious"
                            if has_suspicious_professional_link
                            else "found"
                        )
                    )
                ),
            ],
        ),
        create_check(
            check_id=(
                "standard-sections"
            ),
            category=(
                "Standard sections"
            ),
            title=(
                "Recognizable CV section headings"
            ),
            points_awarded=(
                section_score
            ),
            maximum_points=20,
            message=(
                "Standard section headings help "
                "ATS software identify CV content."
            ),
            evidence=[
                (
                    f"{section}: "
                    f"{'found' if found else 'missing'}"
                )
                for (
                    section,
                    found,
                ) in detected_sections.items()
            ],
        ),
        create_check(
            check_id=(
                "content-structure"
            ),
            category=(
                "Content structure"
            ),
            title=(
                "Organized and scannable content"
            ),
            points_awarded=(
                content_structure_score
            ),
            maximum_points=20,
            message=(
                f"Detected {word_count} words, "
                f"{len(bullet_lines)} bullet-style "
                f"lines and "
                f"{detected_section_count} "
                "recognized sections."
            ),
            evidence=[
                (
                    "Date ranges detected: "
                    f"{date_range_count}"
                ),
            ],
        ),
        create_check(
            check_id=(
                "date-consistency"
            ),
            category=(
                "Date consistency"
            ),
            title=(
                "Chronological date validation"
            ),
            points_awarded=(
                date_consistency_score
            ),
            maximum_points=10,
            message=(
                "Employment and education years "
                "were checked for impossible or "
                "reversed values."
            ),
            evidence=[
                (
                    "Impossible years: "
                    + (
                        ", ".join(
                            str(year)
                            for year
                            in impossible_years
                        )
                        if impossible_years
                        else "none"
                    )
                ),
                (
                    "Reversed date ranges: "
                    f"{reversed_date_range_count}"
                ),
            ],
        ),
        create_check(
            check_id=(
                "layout-and-parsing"
            ),
            category=(
                "Layout and parsing"
            ),
            title=(
                "Extracted text layout quality"
            ),
            points_awarded=(
                layout_score
            ),
            maximum_points=10,
            message=(
                "The extracted text was checked "
                "for corruption, extremely long "
                "lines and fragmented content."
            ),
            evidence=[
                (
                    "Corrupted characters: "
                    f"{corrupted_character_count}"
                ),
                (
                    "Very long lines: "
                    f"{long_line_count}"
                ),
                (
                    "Short fragments: "
                    f"{short_fragment_count}"
                ),
                (
                    "Decorative page markers: "
                    f"{page_marker_count}"
                ),
            ],
        ),
    ]
    suggestions: list[str] = []
    if total_characters < 500:
        suggestions.append(
            "Use a selectable-text PDF and "
            "ensure the CV contains enough "
            "machine-readable content."
        )
    if not has_email:
        suggestions.append(
            "Add a professional email address "
            "as plain text near the top of the CV."
        )
    if not has_phone:
        suggestions.append(
            "Add a phone number as plain text "
            "instead of placing it only inside "
            "an image or icon."
        )
    if not has_professional_link:
        suggestions.append(
            "Add a readable LinkedIn, GitHub "
            "or portfolio URL when relevant."
        )
    elif has_suspicious_professional_link:
        suggestions.append(
            "Review the professional profile URL. "
            "It appears to contain a long number "
            "and may be malformed."
        )
    missing_core_sections: list[str] = []
    if not has_experience_or_projects:
        missing_core_sections.append(
            "Work Experience or Projects"
        )
    if not detected_sections[
        "education"
    ]:
        missing_core_sections.append(
            "Education"
        )
    if not detected_sections["skills"]:
        missing_core_sections.append(
            "Skills"
        )
    if missing_core_sections:
        suggestions.append(
            "Use clear standard headings for: "
            + ", ".join(
                missing_core_sections
            )
            + "."
        )
    if len(bullet_lines) < 2:
        suggestions.append(
            "Use concise bullet points for "
            "experience, achievements and "
            "project details."
        )
    if impossible_years:
        suggestions.append(
            "Correct impossible or future years: "
            + ", ".join(
                str(year)
                for year in impossible_years
            )
            + "."
        )
    if reversed_date_range_count:
        suggestions.append(
            "Review date ranges where the start "
            "date appears later than the end date."
        )
    if page_marker_count:
        suggestions.append(
            "Use simple automatic page numbering. "
            "Decorative spaced page labels can "
            "create ATS parsing noise."
        )
    if layout_score < 7:
        suggestions.append(
            "Simplify complex layout elements "
            "such as text boxes, multi-column "
            "content, decorative icons or tables."
        )
    if not suggestions:
        suggestions.append(
            "No major ATS compatibility issue "
            "was detected. Continue using clear "
            "headings and selectable text."
        )
    return {
        "score": total_score,
        "rating": rating_from_score(
            total_score
        ),
        "risk_level": (
            risk_level_from_score(
                total_score
            )
        ),
        "category_scores": (
            category_scores
        ),
        "checks": checks,
        "suggestions": suggestions,
    }
def analyze_candidate_ats(
    database: Session,
    candidate_id: int,
) -> CandidateATSResult:
    candidate = get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    if candidate.status != "ready":
        raise CandidateATSPrerequisiteError(
            "The candidate CV must be "
            "processed successfully before "
            "ATS analysis."
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
        raise CandidateATSPrerequisiteError(
            "No selectable CV text is available "
            "for ATS analysis."
        )
    analysis = build_ats_analysis(
        pages
    )
    result_statement = (
        select(CandidateATSResult)
        .where(
            CandidateATSResult
            .candidate_cv_id
            == candidate_id
        )
    )
    result = database.scalar(
        result_statement
    )
    if result is None:
        result = CandidateATSResult(
            candidate_cv_id=candidate_id,
            score=analysis["score"],
            rating=analysis["rating"],
            risk_level=(
                analysis["risk_level"]
            ),
            category_scores=(
                analysis[
                    "category_scores"
                ]
            ),
            checks=analysis["checks"],
            suggestions=(
                analysis["suggestions"]
            ),
            engine_version=(
                ATS_ENGINE_VERSION
            ),
        )
        database.add(result)
    else:
        result.score = analysis["score"]
        result.rating = analysis["rating"]
        result.risk_level = (
            analysis["risk_level"]
        )
        result.category_scores = (
            analysis[
                "category_scores"
            ]
        )
        result.checks = analysis["checks"]
        result.suggestions = (
            analysis["suggestions"]
        )
        result.engine_version = (
            ATS_ENGINE_VERSION
        )
    try:
        database.commit()
        database.refresh(result)
    except Exception:
        database.rollback()
        raise
    return result
def get_candidate_ats_result(
    database: Session,
    candidate_id: int,
) -> CandidateATSResult:
    get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    statement = (
        select(CandidateATSResult)
        .where(
            CandidateATSResult
            .candidate_cv_id
            == candidate_id
        )
    )
    result = database.scalar(
        statement
    )
    if result is None:
        raise CandidateATSNotFoundError(
            "ATS analysis has not been "
            "completed for this candidate."
        )
    return result
