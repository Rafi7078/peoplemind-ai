
import re
from datetime import (
    datetime,
    timezone,
)
from backend.app.schemas.candidate_profile import (
    CandidateCertification,
    CandidateContactInformation,
    CandidateLatestEducation,
    CandidateProfileData,
    CandidateProject,
    CandidateSkills,
    CandidateWorkExperience,
)
SECTION_PATTERN = re.compile(
    r"^\[([A-Z][A-Z ]+)\]\s*$",
    flags=re.MULTILINE,
)
EMAIL_PATTERN = re.compile(
    (
        r"\b[A-Z0-9._%+-]+"
        r"@[A-Z0-9.-]+\.[A-Z]{2,}\b"
    ),
    flags=re.IGNORECASE,
)
BANGLADESH_PHONE_PATTERN = re.compile(
    (
        r"(?<!\d)"
        r"(?:\+?88[- ]?)?"
        r"(01[3-9][-\s]?\d{8})"
        r"(?!\d)"
    )
)
GENERIC_PHONE_PATTERN = re.compile(
    (
        r"(?<!\d)"
        r"(\+?\d[\d ()-]{6,}\d)"
        r"(?!\d)"
    )
)
URL_PATTERN = re.compile(
    r"\b(?:https?://|www\.)[^\s]+",
    flags=re.IGNORECASE,
)
YEAR_PATTERN = re.compile(
    r"\b(?:19|20)\d{2}\b"
)
QUALIFICATION_PATTERN = re.compile(
    (
        r"\b(?:"
        r"doctor(?:ate|al)?|ph\.?d|"
        r"master(?:'s)?|m\.?s\.?c|mba|"
        r"bachelor(?:'s)?|b\.?s\.?c|bice|"
        r"diploma|associate|"
        r"higher secondary certificate|hsc|"
        r"secondary school certificate|ssc"
        r")\b"
    ),
    flags=re.IGNORECASE,
)
ONGOING_PATTERN = re.compile(
    (
        r"\b(?:ongoing|in progress|expected|"
        r"current|currently|running)\b"
    ),
    flags=re.IGNORECASE,
)
GPA_PATTERN = re.compile(
    (
        r"\b(?:CGPA|GPA)\s*:?\s*"
        r"([0-9.]+"
        r"(?:\s*(?:/|out of|on scale of)"
        r"\s*[0-9.]+)?)"
    ),
    flags=re.IGNORECASE,
)
DATE_RANGE_PATTERN = re.compile(
    (
        r"(?:Tenure\s*:\s*)?"
        r"("
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|"
        r"Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:tember)?|Sept(?:ember)?|"
        r"Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+\d{4}"
        r"|\d{4}"
        r")"
        r"\s*[??-]\s*"
        r"("
        r"Present|Current|Ongoing|"
        r"(?:Jan(?:uary)?|Feb(?:ruary)?|"
        r"Mar(?:ch)?|Apr(?:il)?|May|"
        r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
        r"Sep(?:tember)?|Sept(?:ember)?|"
        r"Oct(?:ober)?|Nov(?:ember)?|"
        r"Dec(?:ember)?)\s+\d{4}"
        r"|\d{4}"
        r")"
    ),
    flags=re.IGNORECASE,
)
DESCRIPTION_START_PATTERN = re.compile(
    (
        r"^(?:developed|built|implemented|"
        r"designed|created|performed|"
        r"analyzed|analysed|topic modeling|"
        r"in this|this project|the project|"
        r"worked|completed|gained|learned|"
        r"training)\b"
    ),
    flags=re.IGNORECASE,
)
TECHNOLOGY_TERMS = (
    "Cisco Packet Tracer",
    "Microsoft Excel",
    "Jupyter Notebook",
    "Google Colab",
    "Scikit-learn",
    "Power BI",
    "PostgreSQL",
    "JavaScript",
    "TypeScript",
    "Playwright",
    "Matplotlib",
    "WordPress",
    "Selenium",
    "Seaborn",
    "Cypress",
    "XGBoost",
    "Pandas",
    "NumPy",
    "MySQL",
    "Python",
    "K-Means",
    "HTML",
    "CSS",
    "PHP",
    "SQL",
    "Java",
    "C++",
    "CNN",
    "NLP",
    "SVM",
    "R",
)
TOOL_TERMS = {
    "Cisco Packet Tracer",
    "Microsoft Excel",
    "Jupyter Notebook",
    "Google Colab",
    "Scikit-learn",
    "Power BI",
    "PostgreSQL",
    "Playwright",
    "Matplotlib",
    "WordPress",
    "Selenium",
    "Seaborn",
    "Cypress",
    "XGBoost",
    "Pandas",
    "NumPy",
    "MySQL",
}
OPERATIONAL_TERMS = (
    "Software Development Lifecycle",
    "SDLC",
    "Project Management",
    "Manual Testing",
    "Functional Testing",
    "Validation Testing",
    "Regression Testing",
    "UI Testing",
    "Bug Tracking",
    "Issue Management",
    "Data Annotation",
    "Quality Review",
    "Problem-Solving",
    "Analytical Skills",
    "Teamwork",
    "Collaboration",
    "Agile",
    "Scrum",
    "Integrity & Professional Ethics",
)
PAGE_MARKER_PATTERN = re.compile(
    (
        r"^(?:"
        r"\d+\s*\|\s*p\s*a\s*g\s*e"
        r"|page\s+\d+(?:\s+of\s+\d+)?"
        r")$"
    ),
    flags=re.IGNORECASE,
)
TITLE_STOP_WORDS = {
    "a",
    "an",
    "and",
    "as",
    "at",
    "back",
    "for",
    "in",
    "of",
    "on",
    "the",
    "to",
    "using",
    "with",
}

def looks_like_compact_title(
    value: str,
) -> bool:
    line = clean_value(
        value
    )
    if not line:
        return False
    if PAGE_MARKER_PATTERN.fullmatch(
        line
    ):
        return False
    if URL_PATTERN.search(
        line
    ):
        return False
    if line.endswith(
        (".", ";")
    ):
        return False
    if len(line) > 145:
        return False
    # Wrapped description lines usually start
    # with a lowercase character.
    first_character = line[0]
    if not (
        first_character.isupper()
        or first_character.isdigit()
    ):
        return False
    words = re.findall(
        r"[A-Za-z0-9+#&'-]+",
        line,
    )
    if not words or len(words) > 20:
        return False
    significant_words = [
        word
        for word in words
        if word.casefold()
        not in TITLE_STOP_WORDS
    ]
    if not significant_words:
        return False
    title_like_words = sum(
        1
        for word in significant_words
        if (
            word[0].isupper()
            or word.isupper()
            or any(
                character.isupper()
                for character
                in word[1:]
            )
        )
    )
    return (
        title_like_words
        / len(significant_words)
        >= 0.45
    )

def remove_phone_suffix_from_url(
    url: str,
    phone: str | None,
) -> str:
    cleaned_url = url.rstrip(
        ".,);]}"
    )
    if not phone:
        return cleaned_url
    phone_digits = re.sub(
        r"\D",
        "",
        phone,
    )
    if (
        len(phone_digits) >= 7
        and cleaned_url.endswith(
            phone_digits
        )
    ):
        cleaned_url = cleaned_url[
            :-len(phone_digits)
        ].rstrip(
            "/-_"
        )
    return cleaned_url


def clean_value(
    value: str,
) -> str:
    return re.sub(
        r"\s+",
        " ",
        value,
    ).strip(
        " \t\r\n|,;:-"
    )
def deduplicate(
    values: list[str],
) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in values:
        cleaned_value = clean_value(
            value
        )
        if not cleaned_value:
            continue
        key = cleaned_value.casefold()
        if key in seen:
            continue
        seen.add(key)
        result.append(
            cleaned_value
        )
    return result
def split_profile_sections(
    source_text: str,
) -> dict[str, str]:
    matches = list(
        SECTION_PATTERN.finditer(
            source_text
        )
    )
    sections: dict[str, str] = {}
    for index, match in enumerate(
        matches
    ):
        section_name = (
            match.group(1)
            .casefold()
            .replace(" ", "_")
        )
        content_start = match.end()
        content_end = (
            matches[index + 1].start()
            if index + 1 < len(matches)
            else len(source_text)
        )
        sections[section_name] = (
            source_text[
                content_start:content_end
            ].strip()
        )
    return sections
def extract_candidate_name(
    header_text: str,
) -> str | None:
    for raw_line in (
        header_text.splitlines()
    ):
        line = clean_value(
            raw_line
        )
        if not line:
            continue
        if re.match(
            (
                r"^(?:address|phone|mobile|"
                r"email|linkedin|github|"
                r"portfolio)\s*:"
            ),
            line,
            flags=re.IGNORECASE,
        ):
            continue
        if EMAIL_PATTERN.search(line):
            continue
        if URL_PATTERN.search(line):
            continue
        if len(line) <= 100:
            return line
    return None

def extract_contact_information(
    header_text: str,
) -> CandidateContactInformation:
    email_match = EMAIL_PATTERN.search(
        header_text
    )
    phone_search_text = (
        URL_PATTERN.sub(
            " ",
            EMAIL_PATTERN.sub(
                " ",
                header_text,
            ),
        )
    )
    phone_match = (
        BANGLADESH_PHONE_PATTERN.search(
            phone_search_text
        )
        or GENERIC_PHONE_PATTERN.search(
            phone_search_text
        )
    )
    phone = (
        clean_value(
            phone_match.group(0)
        )
        if phone_match is not None
        else None
    )
    urls = [
        remove_phone_suffix_from_url(
            url=url,
            phone=phone,
        )
        for url in URL_PATTERN.findall(
            header_text
        )
    ]
    linkedin = next(
        (
            url
            for url in urls
            if "linkedin"
            in url.casefold()
        ),
        None,
    )
    github = next(
        (
            url
            for url in urls
            if "github"
            in url.casefold()
        ),
        None,
    )
    portfolio = next(
        (
            url
            for url in urls
            if any(
                token
                in url.casefold()
                for token in (
                    "portfolio",
                    "vercel.app",
                    "netlify.app",
                    "github.io",
                )
            )
        ),
        None,
    )
    return CandidateContactInformation(
        email=(
            email_match.group(0)
            if email_match is not None
            else None
        ),
        phone=phone,
        linkedin=linkedin,
        github=github,
        portfolio=portfolio,
    )

def split_education_records(
    education_text: str,
) -> list[list[str]]:
    lines = [
        clean_value(line)
        for line
        in education_text.splitlines()
        if clean_value(line)
    ]
    records: list[list[str]] = []
    current_record: list[str] = []
    for line in lines:
        if QUALIFICATION_PATTERN.search(
            line
        ):
            if current_record:
                records.append(
                    current_record
                )
            current_record = [
                line
            ]
            continue
        if current_record:
            current_record.append(
                line
            )
    if current_record:
        records.append(
            current_record
        )
    return records
def extract_degree_and_institution(
    record_lines: list[str],
) -> tuple[
    str | None,
    str | None,
]:
    first_line = record_lines[0]
    qualification_match = (
        QUALIFICATION_PATTERN.search(
            first_line
        )
    )
    degree = re.sub(
        YEAR_PATTERN,
        "",
        first_line,
    )
    institution: str | None = None
    if (
        qualification_match is not None
        and qualification_match.start() > 0
    ):
        prefix = clean_value(
            first_line[
                :qualification_match.start()
            ]
        )
        suffix = clean_value(
            first_line[
                qualification_match.start():
            ]
        )
        if prefix:
            institution = prefix.rstrip(
                ","
            )
        degree = suffix
    for line in record_lines[1:]:
        if (
            GPA_PATTERN.search(line)
            or YEAR_PATTERN.fullmatch(line)
            or re.match(
                (
                    r"^(?:group|major|"
                    r"department)\s*:"
                ),
                line,
                flags=re.IGNORECASE,
            )
        ):
            continue
        institution = (
            institution
            or line
        )
        break
    return (
        clean_value(degree) or None,
        (
            clean_value(institution)
            if institution
            else None
        ),
    )
def extract_latest_completed_education(
    education_text: str,
) -> CandidateLatestEducation | None:
    current_year = datetime.now(
        timezone.utc
    ).year
    candidates: list[
        tuple[
            int,
            CandidateLatestEducation,
        ]
    ] = []
    for record_lines in (
        split_education_records(
            education_text
        )
    ):
        record_text = "\n".join(
            record_lines
        )
        if ONGOING_PATTERN.search(
            record_text
        ):
            continue
        years = [
            int(value)
            for value
            in YEAR_PATTERN.findall(
                record_text
            )
            if int(value) <= current_year
        ]
        if not years:
            continue
        completion_year = max(
            years
        )
        degree, institution = (
            extract_degree_and_institution(
                record_lines
            )
        )
        gpa_match = GPA_PATTERN.search(
            record_text
        )
        candidates.append(
            (
                completion_year,
                CandidateLatestEducation(
                    degree_or_qualification=(
                        degree
                    ),
                    institution=(
                        institution
                    ),
                    completion_year=str(
                        completion_year
                    ),
                    cgpa_or_gpa=(
                        gpa_match.group(1)
                        if gpa_match
                        is not None
                        else None
                    ),
                ),
            )
        )
    if not candidates:
        return None
    candidates.sort(
        key=lambda item: item[0],
        reverse=True,
    )
    return candidates[0][1]




def extract_work_experience(
    experience_text: str,
) -> list[
    CandidateWorkExperience
]:
    lines = [
        clean_value(line)
        for line
        in experience_text.splitlines()
        if clean_value(line)
    ]
    date_token_pattern = re.compile(
        (
            r"\b(?:"
            r"(?:Jan(?:uary)?|Feb(?:ruary)?|"
            r"Mar(?:ch)?|Apr(?:il)?|May|"
            r"Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|"
            r"Sep(?:tember)?|Sept(?:ember)?|"
            r"Oct(?:ober)?|Nov(?:ember)?|"
            r"Dec(?:ember)?)"
            r"\s+\d{4}"
            r"|(?:19|20)\d{2}"
            r"|Present"
            r"|Current"
            r"|Ongoing"
            r"|Now"
            r")\b"
        ),
        flags=re.IGNORECASE,
    )
    title_signal_pattern = re.compile(
        (
            r"\b(?:intern|engineer|analyst|"
            r"developer|manager|officer|"
            r"executive|assistant|specialist|"
            r"consultant|designer|lead|"
            r"administrator|coordinator|"
            r"trainee|quality assurance|"
            r"data annotation)\b"
        ),
        flags=re.IGNORECASE,
    )
    detail_pattern = re.compile(
        (
            r"^(?:worked|working|gained|"
            r"contributing|performing|"
            r"documenting|developed|"
            r"implemented|prepared|"
            r"collaborated|reviewing|"
            r"annotating|identifying|"
            r"responsible|assisted|"
            r"activity)\b"
        ),
        flags=re.IGNORECASE,
    )
    def is_role(
        value: str | None,
    ) -> bool:
        return bool(
            value
            and title_signal_pattern.search(
                value
            )
        )
    def is_detail(
        value: str | None,
    ) -> bool:
        if not value:
            return True
        return bool(
            detail_pattern.search(value)
            or len(value) > 170
        )
    def nearby_line(
        index: int,
    ) -> str | None:
        if (
            index < 0
            or index >= len(lines)
        ):
            return None
        value = lines[index]
        if is_detail(value):
            return None
        return value
    experiences: list[
        CandidateWorkExperience
    ] = []
    seen_records: set[
        tuple[str, str, str, str]
    ] = set()
    for index, line in enumerate(
        lines
    ):
        date_matches = list(
            date_token_pattern.finditer(
                line
            )
        )
        if len(date_matches) < 2:
            continue
        date_values = [
            clean_value(
                match.group(0)
            )
            for match in date_matches[:2]
        ]
        residual = (
            date_token_pattern.sub(
                " ",
                line,
            )
        )
        residual = re.sub(
            (
                r"^(?:Tenure|Duration)"
                r"\s*:?\s*"
            ),
            "",
            residual,
            flags=re.IGNORECASE,
        )
        residual = re.sub(
            (
                r"^[\s|:?\-\u2013\u2014]+"
                r"|[\s|:?\-\u2013\u2014]+$"
            ),
            "",
            residual,
        )
        residual = clean_value(
            residual
        )
        previous_two = nearby_line(
            index - 2
        )
        previous_one = nearby_line(
            index - 1
        )
        next_one = nearby_line(
            index + 1
        )
        next_two = nearby_line(
            index + 2
        )
        company: str | None = None
        job_title: str | None = None
        if residual:
            residual_is_role = is_role(
                residual
            )
            next_is_role = is_role(
                next_one
            )
            if (
                residual_is_role
                and next_one
                and not next_is_role
            ):
                # Example:
                # Data Annotation Analyst Feb 2026 - Present
                # Rooya
                job_title = residual
                company = next_one
            elif (
                residual_is_role
                and next_one
                and next_is_role
            ):
                # Example:
                # Trust Bank PLC (Web Developer) Dec 2024 - Feb 2025
                # Intern - In-House Software Development Team
                company = residual
                job_title = next_one
            elif (
                not residual_is_role
                and next_one
                and is_role(next_one)
            ):
                # Example:
                # Dream71 Bangladesh Mar 2026 - Jul 2026
                # QA Engineer
                company = residual
                job_title = next_one
            elif (
                residual_is_role
                and previous_one
            ):
                job_title = residual
                company = previous_one
        else:
            if (
                previous_two
                and previous_one
                and is_role(previous_one)
            ):
                # Standard format:
                # Company
                # Job title
                # Tenure dates
                company = previous_two
                job_title = previous_one
            elif (
                next_one
                and next_two
                and is_role(next_two)
            ):
                # Date line appears before company/title.
                company = next_one
                job_title = next_two
        if (
            not company
            or not job_title
        ):
            continue
        start_date = date_values[0]
        end_date = date_values[1]
        record_key = (
            company.casefold(),
            job_title.casefold(),
            start_date.casefold(),
            end_date.casefold(),
        )
        if record_key in seen_records:
            continue
        seen_records.add(
            record_key
        )
        experiences.append(
            CandidateWorkExperience(
                company=company,
                job_title=job_title,
                start_date=start_date,
                end_date=end_date,
                duration=None,
            )
        )
    return experiences

def contains_term(
    text: str,
    term: str,
) -> bool:
    return bool(
        re.search(
            (
                r"(?<![A-Za-z0-9])"
                + re.escape(term)
                + r"(?![A-Za-z0-9])"
            ),
            text,
            flags=re.IGNORECASE,
        )
    )
def split_skill_values(
    value: str,
) -> list[str]:
    return [
        clean_value(item)
        for item in re.split(
            r"\s*[,;|]\s*",
            value,
        )
        if clean_value(item)
    ]

def extract_skills(
    skills_text: str,
) -> CandidateSkills:
    technical: list[str] = []
    tools: list[str] = []
    operational: list[str] = []
    tool_names = {
        "power bi",
        "git",
        "google colab",
        "google collab",
        "jupyter notebook",
        "ms excel",
        "microsoft excel",
        "word",
        "powerpoint",
        "wordpress",
        "jira",
        "trello",
        "cisco packet tracer",
        "canva",
        "figma",
        "adobe suite",
        "playwright",
        "selenium",
        "cypress",
    }
    skill_replacements = {
        "performing calculations":
            "Excel calculations",
        "creating pivot tables":
            "Pivot tables",
        "and visualizing data using charts":
            "Data visualization charts",
        "visualizing data using charts":
            "Data visualization charts",
    }
    lines = [
        clean_value(line)
        for line
        in skills_text.splitlines()
        if clean_value(line)
    ]
    for line in lines:
        if re.search(
            r"\blanguage skills?\b",
            line,
            flags=re.IGNORECASE,
        ):
            continue
        segments = re.split(
            (
                r"\s+-\s+"
                r"(?=[A-Za-z]"
                r"[A-Za-z &/()]+:)"
            ),
            line,
        )
        for segment in segments:
            if ":" not in segment:
                continue
            label, value = segment.split(
                ":",
                1,
            )
            normalized_label = (
                label.casefold()
            )
            values = [
                skill_replacements.get(
                    item.casefold(),
                    item,
                )
                for item in split_skill_values(
                    value
                )
            ]
            if (
                "excel for data work"
                in normalized_label
            ):
                tools.append(
                    "Microsoft Excel"
                )
            if any(
                token
                in normalized_label
                for token in (
                    "tool",
                    "platform",
                    "cms",
                    "bug tracking",
                    "automation testing",
                )
            ):
                tools.extend(
                    values
                )
            elif any(
                token
                in normalized_label
                for token in (
                    "project management",
                    "teamwork",
                    "collaboration",
                    "integrity",
                    "ethics",
                    "analytical",
                    "problem",
                    "lifecycle",
                    "agile",
                    "scrum",
                )
            ):
                operational.extend(
                    values
                )
            else:
                technical.extend(
                    values
                )
    for term in TECHNOLOGY_TERMS:
        if not contains_term(
            skills_text,
            term,
        ):
            continue
        if term.casefold() in tool_names:
            tools.append(
                term
            )
        else:
            technical.append(
                term
            )
    for term in OPERATIONAL_TERMS:
        if contains_term(
            skills_text,
            term,
        ):
            operational.append(
                term
            )
    technical = deduplicate(
        technical
    )
    tools = deduplicate(
        tools
    )
    operational = deduplicate(
        operational
    )
    tool_keys = {
        item.casefold()
        for item in tools
    }
    technical = [
        item
        for item in technical
        if item.casefold()
        not in tool_keys
    ]
    operational_keys = {
        item.casefold()
        for item in operational
    }
    technical = [
        item
        for item in technical
        if item.casefold()
        not in operational_keys
    ]
    return CandidateSkills(
        technical_skills=technical,
        tools_and_platforms=tools,
        operational_skills=operational,
    )

def extract_technologies(
    text: str,
) -> list[str]:
    return deduplicate(
        [
            term
            for term in TECHNOLOGY_TERMS
            if contains_term(
                text,
                term,
            )
        ]
    )
def is_description_line(
    line: str,
) -> bool:
    if DESCRIPTION_START_PATTERN.search(
        line
    ):
        return True
    if len(line) > 150:
        return True
    if (
        len(line) > 85
        and line.endswith(
            (".", ";")
        )
    ):
        return True
    return False

def extract_projects(
    projects_text: str,
) -> list[CandidateProject]:
    lines = [
        clean_value(line)
        for line
        in projects_text.splitlines()
        if clean_value(line)
    ]
    projects: list[
        CandidateProject
    ] = []
    title_parts: list[str] = []
    description_lines: list[str] = []
    description_started = False
    def flush_project() -> None:
        nonlocal title_parts
        nonlocal description_lines
        nonlocal description_started
        if not title_parts:
            description_lines = []
            description_started = False
            return
        raw_title = clean_value(
            " ".join(
                title_parts
            )
        )
        title = raw_title
        explicit_technologies: list[
            str
        ] = []
        if "|" in raw_title:
            tokens = [
                clean_value(token)
                for token
                in raw_title.split("|")
                if clean_value(token)
            ]
            if tokens:
                title = tokens[0]
                explicit_technologies = (
                    tokens[1:]
                )
        project_text = "\n".join(
            [
                raw_title,
                *description_lines,
            ]
        )
        technologies = deduplicate(
            [
                *explicit_technologies,
                *extract_technologies(
                    project_text
                ),
            ]
        )
        if title:
            projects.append(
                CandidateProject(
                    project_title=title,
                    technologies=(
                        technologies
                    ),
                )
            )
        title_parts = []
        description_lines = []
        description_started = False
    for line in lines:
        if PAGE_MARKER_PATTERN.fullmatch(
            line
        ):
            continue
        if re.match(
            (
                r"^(?:github|project link|"
                r"repository|link)\s*:"
            ),
            line,
            flags=re.IGNORECASE,
        ):
            description_lines.append(
                line
            )
            flush_project()
            continue
        if not title_parts:
            title_parts = [
                line
            ]
            continue
        if not description_started:
            if is_description_line(
                line
            ):
                description_started = True
                description_lines.append(
                    line
                )
                continue
            if looks_like_compact_title(
                line
            ):
                title_parts.append(
                    line
                )
                continue
            description_started = True
            description_lines.append(
                line
            )
            continue
        if (
            looks_like_compact_title(
                line
            )
            and not is_description_line(
                line
            )
        ):
            flush_project()
            title_parts = [
                line
            ]
            continue
        description_lines.append(
            line
        )
    flush_project()
    unique_projects: list[
        CandidateProject
    ] = []
    seen_titles: set[str] = set()
    for project in projects:
        title_key = (
            project.project_title
            or ""
        ).casefold()
        if (
            not title_key
            or title_key in seen_titles
        ):
            continue
        seen_titles.add(
            title_key
        )
        unique_projects.append(
            project
        )
    return unique_projects[:20]


def extract_certifications(
    certifications_text: str,
) -> list[
    CandidateCertification
]:
    lines = [
        clean_value(line)
        for line
        in certifications_text.splitlines()
        if clean_value(line)
    ]
    certifications: list[
        CandidateCertification
    ] = []
    current_title: str | None = None
    current_issuer: str | None = None
    current_date: str | None = None
    def flush_certification() -> None:
        nonlocal current_title
        nonlocal current_issuer
        nonlocal current_date
        if current_title:
            certifications.append(
                CandidateCertification(
                    certification_title=(
                        current_title
                    ),
                    issuing_organization=(
                        current_issuer
                    ),
                    completion_date=(
                        current_date
                    ),
                )
            )
        current_title = None
        current_issuer = None
        current_date = None
    for line in lines:
        if PAGE_MARKER_PATTERN.fullmatch(
            line
        ):
            continue
        if re.match(
            (
                r"^(?:credential|credentials)"
                r"\s+id\s*:"
            ),
            line,
            flags=re.IGNORECASE,
        ):
            continue
        if re.match(
            (
                r"^(?:github|certificate link|"
                r"verification link|link)\s*:"
            ),
            line,
            flags=re.IGNORECASE,
        ):
            continue
        institute_match = re.match(
            (
                r"^(?:institute|issuer|"
                r"issued by|organization)"
                r"\s*:\s*(.+)$"
            ),
            line,
            flags=re.IGNORECASE,
        )
        if institute_match is not None:
            current_issuer = clean_value(
                institute_match.group(1)
            )
            continue
        if (
            is_description_line(line)
            or not looks_like_compact_title(
                line
            )
        ):
            continue
        flush_certification()
        title = line
        issuer: str | None = None
        dash_parts = re.split(
            r"\s+[??-]\s+",
            line,
            maxsplit=1,
        )
        if len(dash_parts) == 2:
            title = clean_value(
                dash_parts[0]
            )
            issuer = clean_value(
                dash_parts[1]
            )
        year_match = YEAR_PATTERN.search(
            line
        )
        current_title = title
        current_issuer = issuer
        current_date = (
            year_match.group(0)
            if year_match is not None
            else None
        )
    flush_certification()
    unique_certifications: list[
        CandidateCertification
    ] = []
    seen_titles: set[str] = set()
    for certification in certifications:
        title_key = (
            certification
            .certification_title
            or ""
        ).casefold()
        if (
            not title_key
            or title_key in seen_titles
        ):
            continue
        seen_titles.add(
            title_key
        )
        unique_certifications.append(
            certification
        )
    return unique_certifications[:30]

def parse_candidate_profile(
    source_text: str,
) -> CandidateProfileData:
    sections = split_profile_sections(
        source_text
    )
    header = sections.get(
        "candidate_header_and_contact",
        "",
    )
    return CandidateProfileData(
        candidate_name=(
            extract_candidate_name(
                header
            )
        ),
        contact_information=(
            extract_contact_information(
                header
            )
        ),
        latest_completed_education=(
            extract_latest_completed_education(
                sections.get(
                    "education",
                    "",
                )
            )
        ),
        work_experience=(
            extract_work_experience(
                sections.get(
                    "work_experience",
                    "",
                )
            )
        ),
        skills=extract_skills(
            sections.get(
                "skills",
                "",
            )
        ),
        projects=extract_projects(
            sections.get(
                "projects",
                "",
            )
        ),
        certifications=(
            extract_certifications(
                sections.get(
                    "certifications",
                    "",
                )
            )
        ),
    )
def profile_needs_ai_fallback(
    profile: CandidateProfileData,
) -> bool:
    has_skills = bool(
        profile.skills.technical_skills
        or profile.skills.tools_and_platforms
        or profile.skills.operational_skills
    )
    has_content = bool(
        profile.latest_completed_education
        or profile.work_experience
        or has_skills
        or profile.projects
        or profile.certifications
    )
    return not (
        profile.candidate_name
        and has_content
    )
def merge_candidate_profiles(
    deterministic_profile: (
        CandidateProfileData
    ),
    ai_profile: CandidateProfileData,
) -> CandidateProfileData:
    deterministic_has_skills = bool(
        deterministic_profile
        .skills
        .technical_skills
        or deterministic_profile
        .skills
        .tools_and_platforms
        or deterministic_profile
        .skills
        .operational_skills
    )
    return CandidateProfileData(
        candidate_name=(
            deterministic_profile
            .candidate_name
            or ai_profile.candidate_name
        ),
        contact_information=(
            CandidateContactInformation(
                email=(
                    deterministic_profile
                    .contact_information
                    .email
                    or ai_profile
                    .contact_information
                    .email
                ),
                phone=(
                    deterministic_profile
                    .contact_information
                    .phone
                    or ai_profile
                    .contact_information
                    .phone
                ),
                linkedin=(
                    deterministic_profile
                    .contact_information
                    .linkedin
                    or ai_profile
                    .contact_information
                    .linkedin
                ),
                github=(
                    deterministic_profile
                    .contact_information
                    .github
                    or ai_profile
                    .contact_information
                    .github
                ),
                portfolio=(
                    deterministic_profile
                    .contact_information
                    .portfolio
                    or ai_profile
                    .contact_information
                    .portfolio
                ),
            )
        ),
        latest_completed_education=(
            deterministic_profile
            .latest_completed_education
            or ai_profile
            .latest_completed_education
        ),
        work_experience=(
            deterministic_profile
            .work_experience
            or ai_profile
            .work_experience
        ),
        skills=(
            deterministic_profile.skills
            if deterministic_has_skills
            else ai_profile.skills
        ),
        projects=(
            deterministic_profile.projects
            or ai_profile.projects
        ),
        certifications=(
            deterministic_profile
            .certifications
            or ai_profile.certifications
        ),
    )
