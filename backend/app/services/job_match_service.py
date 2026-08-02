
import re
from sqlalchemy import (
    delete,
    select,
)
from sqlalchemy.orm import Session
from backend.app.models.candidate_cv_page import (
    CandidateCVPage,
)
from backend.app.models.candidate_profile import (
    CandidateProfile,
)
from backend.app.models.job_candidate_assignment import (
    JobCandidateAssignment,
)
from backend.app.models.job_match_result import (
    JobMatchResult,
)
from backend.app.services.candidate_service import (
    get_candidate_cv,
)
from backend.app.services.job_profile_service import (
    get_job_profile,
)
JOB_MATCH_ENGINE_VERSION = (
    "deterministic-job-match-v1.1"
)
class JobMatchPrerequisiteError(
    ValueError
):
    pass
class JobMatchResultNotFoundError(
    LookupError
):
    pass
SKILL_CATALOG: dict[
    str,
    tuple[str, ...],
] = {
    "manual_testing": (
        "manual testing",
        "software testing",
        "test execution",
        "test cases",
        "test case design",
    ),
    "automation_testing": (
        "automation testing",
        "automated testing",
        "test automation",
        "automation framework",
    ),
    "api_testing": (
        "api testing",
        "rest api testing",
        "web service testing",
    ),
    "regression_testing": (
        "regression testing",
        "regression test",
    ),
    "functional_testing": (
        "functional testing",
        "functional test",
    ),
    "performance_testing": (
        "performance testing",
        "load testing",
        "stress testing",
    ),
    "defect_management": (
        "defect management",
        "bug tracking",
        "defect tracking",
        "bug reporting",
    ),
    "selenium": (
        "selenium",
        "selenium webdriver",
    ),
    "playwright": (
        "playwright",
    ),
    "cypress": (
        "cypress",
    ),
    "postman": (
        "postman",
    ),
    "jira": (
        "jira",
    ),
    "jmeter": (
        "jmeter",
        "apache jmeter",
    ),
    "python": (
        "python",
    ),
    "sql": (
        "sql",
        "structured query language",
    ),
    "excel": (
        "excel",
        "microsoft excel",
        "ms excel",
    ),
    "power_bi": (
        "power bi",
        "powerbi",
    ),
    "tableau": (
        "tableau",
    ),
    "data_analysis": (
        "data analysis",
        "data analytics",
        "data analyst",
    ),
    "data_visualization": (
        "data visualization",
        "data visualisation",
        "dashboard development",
    ),
    "statistics": (
        "statistics",
        "statistical analysis",
    ),
    "pandas": (
        "pandas",
    ),
    "numpy": (
        "numpy",
    ),
    "data_annotation": (
        "data annotation",
        "data annotator",
        "data labeling",
        "data labelling",
        "image annotation",
        "video annotation",
        "bounding box annotation",
        "object annotation",
    ),
    "cvat": (
        "cvat",
        "computer vision annotation tool",
    ),
    "annotation_quality": (
        "annotation quality",
        "annotation review",
        "label quality",
        "label review",
        "quality review",
        "annotation audit",
    ),
    "machine_learning": (
        "machine learning",
        "ml modeling",
        "predictive modeling",
    ),
    "javascript": (
        "javascript",
    ),
    "typescript": (
        "typescript",
    ),
    "react": (
        "react",
        "react.js",
        "reactjs",
    ),
    "node_js": (
        "node.js",
        "nodejs",
    ),
    "fastapi": (
        "fastapi",
    ),
    "django": (
        "django",
    ),
    "flask": (
        "flask",
    ),
    "java": (
        "java",
    ),
    "dotnet": (
        ".net",
        "dotnet",
        "asp.net",
    ),
    "git": (
        "git",
        "version control",
    ),
    "github": (
        "github",
    ),
    "docker": (
        "docker",
        "containerization",
    ),
    "kubernetes": (
        "kubernetes",
        "k8s",
    ),
    "linux": (
        "linux",
    ),
    "aws": (
        "aws",
        "amazon web services",
    ),
    "azure": (
        "azure",
        "microsoft azure",
    ),
    "gcp": (
        "gcp",
        "google cloud platform",
    ),
    "cybersecurity": (
        "cybersecurity",
        "cyber security",
        "information security",
    ),
    "network_security": (
        "network security",
    ),
    "penetration_testing": (
        "penetration testing",
        "pentesting",
        "vulnerability assessment",
    ),
    "project_management": (
        "project management",
    ),
    "agile": (
        "agile",
        "scrum",
    ),
    "communication": (
        "communication skills",
        "written communication",
        "verbal communication",
    ),
    "problem_solving": (
        "problem solving",
        "analytical thinking",
    ),
    "recruitment": (
        "recruitment",
        "talent acquisition",
        "candidate sourcing",
    ),
    "hr_operations": (
        "hr operations",
        "human resources operations",
        "employee management",
    ),
    "digital_marketing": (
        "digital marketing",
        "online marketing",
    ),
    "seo": (
        "seo",
        "search engine optimization",
    ),
    "content_marketing": (
        "content marketing",
        "content strategy",
    ),
}
ROLE_GROUPS: dict[
    str,
    tuple[str, ...],
] = {
    "quality_assurance": (
        "quality assurance",
        "qa engineer",
        "qa analyst",
        "software qa",
        "software tester",
        "test engineer",
        "test analyst",
        "sqa",
    ),
    "data_annotation": (
        "data annotation analyst",
        "data annotation specialist",
        "data annotator",
        "annotation analyst",
        "image annotator",
        "video annotator",
        "data annotation",
        "cvat team",
    ),
    "data_analytics": (
        "data analyst",
        "data analytics",
        "business intelligence",
        "bi analyst",
        "reporting analyst",
    ),
    "data_science": (
        "data scientist",
        "machine learning engineer",
        "ml engineer",
    ),
    "software_engineering": (
        "software engineer",
        "software developer",
        "backend developer",
        "frontend developer",
        "full stack developer",
        "web developer",
    ),
    "cybersecurity": (
        "cybersecurity",
        "security analyst",
        "security engineer",
        "penetration tester",
        "soc analyst",
    ),
    "human_resources": (
        "human resources",
        "hr executive",
        "hr officer",
        "recruiter",
        "talent acquisition",
    ),
    "marketing": (
        "marketing",
        "digital marketer",
        "marketing executive",
        "social media manager",
    ),
    "project_management": (
        "project manager",
        "project coordinator",
        "scrum master",
    ),
    "finance_accounting": (
        "accountant",
        "finance officer",
        "financial analyst",
        "accounts executive",
    ),
}
TITLE_STOP_WORDS = {
    "a",
    "an",
    "and",
    "associate",
    "for",
    "in",
    "intern",
    "junior",
    "lead",
    "manager",
    "of",
    "officer",
    "senior",
    "specialist",
    "the",
    "with",
}
EDUCATION_LEVEL_ALIASES: dict[
    str,
    tuple[str, ...],
] = {
    "phd": (
        "phd",
        "doctorate",
        "doctoral degree",
    ),
    "masters": (
        "master's degree",
        "masters degree",
        "master degree",
        "msc",
        "m.sc",
        "mba",
    ),
    "bachelors": (
        "bachelor's degree",
        "bachelors degree",
        "bachelor degree",
        "bsc",
        "b.sc",
        "bba",
        "b.tech",
        "btech",
    ),
    "diploma": (
        "diploma",
    ),
    "degree": (
        "university degree",
        "academic degree",
        "graduate degree",
    ),
}
MINIMUM_EXPERIENCE_PATTERN = re.compile(
    (
        r"\b(?:minimum|min\.?|at least)?\s*"
        r"(?P<years>\d+(?:\.\d+)?)"
        r"\s*\+?\s*(?:years?|yrs?)"
        r"(?:\s+of\s+experience)?\b"
    ),
    flags=re.IGNORECASE,
)
DURATION_YEAR_PATTERN = re.compile(
    r"(?P<years>\d+)\s*years?",
    flags=re.IGNORECASE,
)
DURATION_MONTH_PATTERN = re.compile(
    r"(?P<months>\d+)\s*months?",
    flags=re.IGNORECASE,
)
def normalize_text(
    value: str | None,
) -> str:
    if not value:
        return ""
    normalized_value = re.sub(
        r"[^a-z0-9+#./ ]+",
        " ",
        value.casefold(),
    )
    return re.sub(
        r"\s+",
        " ",
        normalized_value,
    ).strip()
def contains_phrase(
    normalized_text: str,
    phrase: str,
) -> bool:
    normalized_phrase = normalize_text(
        phrase
    )
    if not normalized_phrase:
        return False
    pattern = (
        r"(?<![a-z0-9])"
        + re.escape(
            normalized_phrase
        ).replace(
            r"\ ",
            r"\s+",
        )
        + r"(?![a-z0-9])"
    )
    return bool(
        re.search(
            pattern,
            normalized_text,
        )
    )
def contains_any_phrase(
    normalized_text: str,
    phrases: tuple[str, ...],
) -> bool:
    return any(
        contains_phrase(
            normalized_text,
            phrase,
        )
        for phrase in phrases
    )
def display_name(
    value: str,
) -> str:
    return value.replace(
        "_",
        " ",
    ).title()
def extract_job_skills(
    job_text: str,
) -> list[str]:
    normalized_job_text = normalize_text(
        job_text
    )
    return sorted(
        skill_name
        for (
            skill_name,
            aliases,
        ) in SKILL_CATALOG.items()
        if contains_any_phrase(
            normalized_job_text,
            aliases,
        )
    )
def detect_role_groups(
    value: str,
) -> list[str]:
    normalized_value = normalize_text(
        value
    )
    return sorted(
        group_name
        for (
            group_name,
            aliases,
        ) in ROLE_GROUPS.items()
        if contains_any_phrase(
            normalized_value,
            aliases,
        )
    )
def extract_title_tokens(
    value: str,
) -> set[str]:
    return {
        token
        for token in normalize_text(
            value
        ).split()
        if (
            len(token) >= 3
            and token
            not in TITLE_STOP_WORDS
        )
    }
def parse_duration_months(
    value: str | None,
) -> int:
    if not value:
        return 0
    year_match = (
        DURATION_YEAR_PATTERN.search(
            value
        )
    )
    month_match = (
        DURATION_MONTH_PATTERN.search(
            value
        )
    )
    years = (
        int(
            year_match.group(
                "years"
            )
        )
        if year_match
        else 0
    )
    months = (
        int(
            month_match.group(
                "months"
            )
        )
        if month_match
        else 0
    )
    return (
        years * 12
        + months
    )
def extract_minimum_experience_years(
    job_text: str,
) -> float | None:
    match = (
        MINIMUM_EXPERIENCE_PATTERN
        .search(job_text)
    )
    if match is None:
        return None
    return float(
        match.group("years")
    )
def extract_education_requirement(
    job_text: str,
) -> str | None:
    normalized_job_text = (
        normalize_text(job_text)
    )
    for education_level in (
        "phd",
        "masters",
        "bachelors",
        "diploma",
        "degree",
    ):
        aliases = (
            EDUCATION_LEVEL_ALIASES[
                education_level
            ]
        )
        if contains_any_phrase(
            normalized_job_text,
            aliases,
        ):
            return education_level
    return None
def education_matches(
    education_requirement: str,
    candidate_degree: str,
) -> bool:
    normalized_degree = (
        normalize_text(
            candidate_degree
        )
    )
    if (
        education_requirement
        == "degree"
    ):
        return bool(normalized_degree)
    return contains_any_phrase(
        normalized_degree,
        EDUCATION_LEVEL_ALIASES[
            education_requirement
        ],
    )
def create_check(
    check_id: str,
    category: str,
    title: str,
    status: str,
    points_awarded: int,
    maximum_points: int,
    message: str,
    evidence: list[str] | None = None,
) -> dict:
    return {
        "check_id": check_id,
        "category": category,
        "title": title,
        "status": status,
        "points_awarded": (
            points_awarded
        ),
        "max_points": maximum_points,
        "message": message,
        "evidence": evidence or [],
    }
def ratio_status(
    ratio: float,
) -> str:
    if ratio >= 0.75:
        return "match"
    if ratio >= 0.40:
        return "partial"
    return "missing"
def rating_from_score(
    score: int,
) -> str:
    if score >= 85:
        return "Strong match"
    if score >= 70:
        return "Good match"
    if score >= 55:
        return "Partial match"
    return "Limited match"
def recommendation_from_score(
    score: int,
) -> str:
    if score >= 85:
        return (
            "strong_match_for_review"
        )
    if score >= 70:
        return (
            "good_match_for_review"
        )
    if score >= 55:
        return (
            "partial_match_review_required"
        )
    return (
        "limited_evidence_review_required"
    )
def get_candidate_source_data(
    database: Session,
    candidate_id: int,
    profile: CandidateProfile,
) -> dict:
    skills_payload = (
        profile.skills
        if isinstance(
            profile.skills,
            dict,
        )
        else {}
    )
    structured_skill_values: list[
        str
    ] = []
    for values in (
        skills_payload.values()
    ):
        if isinstance(values, list):
            structured_skill_values.extend(
                str(value)
                for value in values
                if value
            )
    work_experience = (
        profile.work_experience
        if isinstance(
            profile.work_experience,
            list,
        )
        else []
    )
    projects = (
        profile.projects
        if isinstance(
            profile.projects,
            list,
        )
        else []
    )
    certifications = (
        profile.certifications
        if isinstance(
            profile.certifications,
            list,
        )
        else []
    )
    work_titles = [
        str(
            experience.get(
                "job_title",
                "",
            )
        )
        for experience
        in work_experience
        if isinstance(
            experience,
            dict,
        )
    ]
    project_values: list[str] = []
    for project in projects:
        if not isinstance(
            project,
            dict,
        ):
            continue
        project_title = project.get(
            "project_title"
        )
        if project_title:
            project_values.append(
                str(project_title)
            )
        technologies = project.get(
            "technologies",
            [],
        )
        if isinstance(
            technologies,
            list,
        ):
            project_values.extend(
                str(value)
                for value in technologies
                if value
            )
    certification_values: list[
        str
    ] = []
    for certification in certifications:
        if not isinstance(
            certification,
            dict,
        ):
            continue
        for key in (
            "certification_title",
            "issuing_organization",
        ):
            value = certification.get(
                key
            )
            if value:
                certification_values.append(
                    str(value)
                )
    page_statement = (
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
            page_statement
        ).all()
    )
    raw_text = "\n".join(
        page.text
        for page in pages
        if page.text.strip()
    )
    education_payload = (
        profile.latest_completed_education
        if isinstance(
            profile.latest_completed_education,
            dict,
        )
        else {}
    )
    candidate_degree = str(
        education_payload.get(
            "degree_or_qualification",
            "",
        )
        or ""
    )
    total_experience_months = sum(
        parse_duration_months(
            str(
                experience.get(
                    "duration",
                    "",
                )
                or ""
            )
        )
        for experience
        in work_experience
        if isinstance(
            experience,
            dict,
        )
    )
    return {
        "structured_skills": (
            structured_skill_values
        ),
        "work_titles": work_titles,
        "projects": project_values,
        "certifications": (
            certification_values
        ),
        "raw_text": raw_text,
        "candidate_degree": (
            candidate_degree
        ),
        "work_experience_count": (
            len(work_experience)
        ),
        "project_count": len(projects),
        "certification_count": (
            len(certifications)
        ),
        "total_experience_months": (
            total_experience_months
        ),
    }
def build_skill_evidence(
    job_skills: list[str],
    candidate_data: dict,
) -> tuple[
    list[str],
    list[str],
    dict[str, list[str]],
]:
    source_values = {
        "structured skills": (
            candidate_data[
                "structured_skills"
            ]
        ),
        "work titles": (
            candidate_data[
                "work_titles"
            ]
        ),
        "projects": (
            candidate_data[
                "projects"
            ]
        ),
        "certifications": (
            candidate_data[
                "certifications"
            ]
        ),
        "CV text": [
            candidate_data[
                "raw_text"
            ]
        ],
    }
    normalized_sources = {
        source_name: normalize_text(
            "\n".join(values)
        )
        for (
            source_name,
            values,
        ) in source_values.items()
    }
    matched_skills: list[str] = []
    missing_skills: list[str] = []
    evidence_by_skill: dict[
        str,
        list[str],
    ] = {}
    for skill_name in job_skills:
        aliases = SKILL_CATALOG[
            skill_name
        ]
        evidence_sources = [
            source_name
            for (
                source_name,
                normalized_source,
            ) in normalized_sources.items()
            if contains_any_phrase(
                normalized_source,
                aliases,
            )
        ]
        if evidence_sources:
            matched_skills.append(
                skill_name
            )
            evidence_by_skill[
                skill_name
            ] = evidence_sources
        else:
            missing_skills.append(
                skill_name
            )
    return (
        matched_skills,
        missing_skills,
        evidence_by_skill,
    )
def build_job_match_analysis(
    job_title: str,
    job_description: str,
    candidate_data: dict,
) -> dict:
    job_text = (
        f"{job_title}\n"
        f"{job_description}"
    )
    job_skills = extract_job_skills(
        job_text
    )
    (
        matched_skills,
        missing_skills,
        evidence_by_skill,
    ) = build_skill_evidence(
        job_skills=job_skills,
        candidate_data=candidate_data,
    )
    matched_requirements: list[str] = []
    missing_requirements: list[str] = []
    notes: list[str] = []
    # --------------------------------------------------------
    # SKILL MATCH ? 45 points
    # --------------------------------------------------------
    if job_skills:
        skill_ratio = (
            len(matched_skills)
            / len(job_skills)
        )
        skill_score = round(
            45 * skill_ratio
        )
        skill_status = ratio_status(
            skill_ratio
        )
        for skill_name in matched_skills:
            sources = evidence_by_skill[
                skill_name
            ]
            matched_requirements.append(
                (
                    f"{display_name(skill_name)} "
                    "matched in "
                    + ", ".join(sources)
                    + "."
                )
            )
        for skill_name in missing_skills:
            missing_requirements.append(
                (
                    f"{display_name(skill_name)} "
                    "was requested by the job "
                    "but was not confirmed."
                )
            )
        skill_message = (
            f"Matched {len(matched_skills)} "
            f"of {len(job_skills)} "
            "recognized job skill requirements."
        )
        skill_evidence = [
            (
                f"{display_name(skill_name)}: "
                + ", ".join(
                    evidence_by_skill[
                        skill_name
                    ]
                )
            )
            for skill_name
            in matched_skills
        ]
        if missing_skills:
            skill_evidence.append(
                "Missing: "
                + ", ".join(
                    display_name(
                        skill_name
                    )
                    for skill_name
                    in missing_skills
                )
            )
    else:
        skill_score = 0
        skill_status = "not_specified"
        skill_message = (
            "The job description did not "
            "contain recognized skill "
            "requirements for reliable scoring."
        )
        skill_evidence = []
        notes.append(
            "Add explicit required skills to the "
            "job description for a stronger and "
            "more reliable match analysis."
        )
    skill_maximum = (
        45
        if job_skills
        else 0
    )
    # --------------------------------------------------------
    # ROLE RELEVANCE ? 20 points
    # --------------------------------------------------------
    job_role_groups = (
        detect_role_groups(
            job_title
        )
    )
    candidate_role_text = "\n".join(
        candidate_data["work_titles"]
        + candidate_data["projects"]
    )
    candidate_role_groups = (
        detect_role_groups(
            candidate_role_text
        )
    )
    matched_role_groups = sorted(
        set(job_role_groups)
        & set(candidate_role_groups)
    )
    job_title_tokens = (
        extract_title_tokens(
            job_title
        )
    )
    candidate_title_tokens: set[
        str
    ] = set()
    for candidate_title in (
        candidate_data["work_titles"]
    ):
        candidate_title_tokens.update(
            extract_title_tokens(
                candidate_title
            )
        )
    title_overlap = (
        job_title_tokens
        & candidate_title_tokens
    )
    title_overlap_ratio = (
        len(title_overlap)
        / max(
            len(job_title_tokens),
            1,
        )
    )
    if matched_role_groups:
        role_score = 20
        role_status = "match"
        role_message = (
            "Candidate role evidence matches "
            "the job role family."
        )
        role_evidence = [
            (
                "Matched role family: "
                + ", ".join(
                    display_name(group)
                    for group
                    in matched_role_groups
                )
            )
        ]
    elif title_overlap_ratio >= 0.50:
        role_score = 16
        role_status = "match"
        role_message = (
            "Candidate work titles have strong "
            "keyword overlap with the job title."
        )
        role_evidence = [
            (
                "Overlapping title terms: "
                + ", ".join(
                    sorted(title_overlap)
                )
            )
        ]
    elif title_overlap:
        role_score = 10
        role_status = "partial"
        role_message = (
            "Candidate work titles have partial "
            "overlap with the job title."
        )
        role_evidence = [
            (
                "Overlapping title terms: "
                + ", ".join(
                    sorted(title_overlap)
                )
            )
        ]
    elif (
        candidate_data[
            "work_experience_count"
        ]
        > 0
    ):
        role_score = 5
        role_status = "missing"
        role_message = (
            "Work experience exists, but a "
            "related role was not confirmed."
        )
        role_evidence = [
            "Candidate work titles: "
            + (
                ", ".join(
                    candidate_data[
                        "work_titles"
                    ]
                )
                or "not confirmed"
            )
        ]
    else:
        role_score = 0
        role_status = "missing"
        role_message = (
            "No relevant work-role evidence "
            "was confirmed."
        )
        role_evidence = []
    if role_score >= 16:
        matched_requirements.append(
            (
                "Role relevance was confirmed "
                "from work-title evidence."
            )
        )
    elif job_role_groups:
        missing_requirements.append(
            (
                "A clearly related job role was "
                "not confirmed."
            )
        )
    # --------------------------------------------------------
    # EXPERIENCE REQUIREMENT ? 15 points
    # --------------------------------------------------------
    minimum_experience_years = (
        extract_minimum_experience_years(
            job_description
        )
    )
    total_experience_months = int(
        candidate_data[
            "total_experience_months"
        ]
    )
    total_experience_years = (
        total_experience_months
        / 12
    )
    has_related_role = (
        role_score >= 16
    )
    if (
        minimum_experience_years
        is not None
    ):
        required_months = (
            minimum_experience_years
            * 12
        )
        experience_ratio = min(
            (
                total_experience_months
                / required_months
                if required_months > 0
                else 1
            ),
            1,
        )
        if has_related_role:
            experience_score = round(
                15 * experience_ratio
            )
        else:
            experience_score = round(
                5 * experience_ratio
            )
        experience_status = (
            "match"
            if (
                experience_ratio >= 1
                and has_related_role
            )
            else (
                "partial"
                if experience_score > 0
                else "missing"
            )
        )
        experience_message = (
            "The job requests at least "
            f"{minimum_experience_years:g} "
            "year(s) of experience."
        )
        experience_evidence = [
            (
                "Confirmed structured duration: "
                f"{total_experience_years:.1f} "
                "year(s)"
            ),
            (
                "Related role evidence: "
                f"{'yes' if has_related_role else 'no'}"
            ),
        ]
        if (
            experience_ratio >= 1
            and has_related_role
        ):
            matched_requirements.append(
                (
                    "Minimum relevant experience "
                    "requirement was met."
                )
            )
        else:
            missing_requirements.append(
                (
                    "Minimum relevant experience "
                    "requirement was not fully "
                    "confirmed."
                )
            )
    else:
        if has_related_role:
            experience_score = 15
            experience_status = "match"
            experience_message = (
                "No explicit minimum duration "
                "was stated, and related work "
                "experience was confirmed."
            )
        elif (
            candidate_data[
                "work_experience_count"
            ]
            > 0
        ):
            experience_score = 10
            experience_status = "partial"
            experience_message = (
                "No explicit minimum duration "
                "was stated. General work "
                "experience was confirmed."
            )
        elif (
            candidate_data[
                "project_count"
            ]
            > 0
        ):
            experience_score = 5
            experience_status = "partial"
            experience_message = (
                "No work experience was confirmed, "
                "but project evidence is available."
            )
        else:
            experience_score = 0
            experience_status = "missing"
            experience_message = (
                "No work or project experience "
                "was confirmed."
            )
        experience_evidence = [
            (
                "Structured work records: "
                f"{candidate_data['work_experience_count']}"
            ),
            (
                "Confirmed structured duration: "
                f"{total_experience_years:.1f} "
                "year(s)"
            ),
        ]
        notes.append(
            "The job description does not state "
            "a minimum experience duration."
        )
    # --------------------------------------------------------
    # EDUCATION REQUIREMENT ? 10 points
    # --------------------------------------------------------
    education_requirement = (
        extract_education_requirement(
            job_description
        )
    )
    candidate_degree = str(
        candidate_data[
            "candidate_degree"
        ]
    )
    if education_requirement is None:
        education_score = 0
        education_maximum = 0
        education_status = (
            "not_specified"
        )
        education_message = (
            "The job description does not state "
            "a specific education level. This "
            "category is excluded from the "
            "overall score."
        )
        education_evidence = [
            (
                "Candidate education: "
                + (
                    candidate_degree
                    or "not confirmed"
                )
            )
        ]
    elif (
        candidate_degree
        and education_matches(
            education_requirement,
            candidate_degree,
        )
    ):
        education_maximum = 10
        education_score = 10
        education_status = "match"
        education_message = (
            "The candidate education matches "
            "the stated education level."
        )
        education_evidence = [
            (
                "Required level: "
                + display_name(
                    education_requirement
                )
            ),
            (
                "Candidate education: "
                + candidate_degree
            ),
        ]
        matched_requirements.append(
            (
                "Education requirement matched: "
                + display_name(
                    education_requirement
                )
                + "."
            )
        )
    elif candidate_degree:
        education_maximum = 10
        education_score = 5
        education_status = "partial"
        education_message = (
            "Candidate education exists, but the "
            "requested level was not clearly "
            "confirmed."
        )
        education_evidence = [
            (
                "Required level: "
                + display_name(
                    education_requirement
                )
            ),
            (
                "Candidate education: "
                + candidate_degree
            ),
        ]
        missing_requirements.append(
            (
                "Requested education level was "
                "not fully confirmed."
            )
        )
    else:
        education_maximum = 10
        education_score = 0
        education_status = "missing"
        education_message = (
            "The job states an education "
            "requirement, but candidate education "
            "was not confirmed."
        )
        education_evidence = [
            (
                "Required level: "
                + display_name(
                    education_requirement
                )
            )
        ]
        missing_requirements.append(
            (
                "Candidate education evidence "
                "was not confirmed."
            )
        )
    # --------------------------------------------------------
    # SUPPORTING EVIDENCE ? 10 points
    # --------------------------------------------------------
    project_skill_matches = [
        skill_name
        for skill_name
        in matched_skills
        if (
            "projects"
            in evidence_by_skill.get(
                skill_name,
                [],
            )
        )
    ]
    certification_skill_matches = [
        skill_name
        for skill_name
        in matched_skills
        if (
            "certifications"
            in evidence_by_skill.get(
                skill_name,
                [],
            )
        )
    ]
    if job_skills:
        project_points = round(
            6
            * (
                len(project_skill_matches)
                / len(job_skills)
            )
        )
        if (
            project_points == 0
            and candidate_data[
                "project_count"
            ]
            > 0
        ):
            project_points = 1
        if certification_skill_matches:
            certification_points = 4
        elif (
            candidate_data[
                "certification_count"
            ]
            > 0
        ):
            certification_points = 1
        else:
            certification_points = 0
    else:
        project_points = (
            4
            if candidate_data[
                "project_count"
            ]
            > 0
            else 0
        )
        certification_points = (
            2
            if candidate_data[
                "certification_count"
            ]
            > 0
            else 0
        )
    supporting_score = min(
        project_points
        + certification_points,
        10,
    )
    if supporting_score >= 7:
        supporting_status = "match"
    elif supporting_score > 0:
        supporting_status = "partial"
    else:
        supporting_status = "missing"
    supporting_message = (
        "Projects and certifications were "
        "checked for supporting job evidence."
    )
    supporting_evidence = [
        (
            "Project records: "
            f"{candidate_data['project_count']}"
        ),
        (
            "Certification records: "
            f"{candidate_data['certification_count']}"
        ),
        (
            "Job skills confirmed in projects: "
            + (
                ", ".join(
                    display_name(skill)
                    for skill
                    in project_skill_matches
                )
                or "none"
            )
        ),
        (
            "Job skills confirmed in "
            "certifications: "
            + (
                ", ".join(
                    display_name(skill)
                    for skill
                    in certification_skill_matches
                )
                or "none"
            )
        ),
    ]
    category_scores = {
        "skill_match": skill_score,
        "role_relevance": role_score,
        "experience_requirement": (
            experience_score
        ),
        "education_requirement": (
            education_score
        ),
        "supporting_evidence": (
            supporting_score
        ),
    }
    raw_score = sum(
        category_scores.values()
    )
    applicable_maximum = (
        skill_maximum
        + 20
        + 15
        + education_maximum
        + 10
    )
    score = (
        round(
            (
                raw_score
                / applicable_maximum
            )
            * 100
        )
        if applicable_maximum > 0
        else 0
    )
    checks = [
        create_check(
            check_id="skill-match",
            category="Skill match",
            title=(
                "Required and preferred "
                "skill evidence"
            ),
            status=skill_status,
            points_awarded=skill_score,
            maximum_points=(
                skill_maximum
            ),
            message=skill_message,
            evidence=skill_evidence,
        ),
        create_check(
            check_id="role-relevance",
            category="Role relevance",
            title=(
                "Job-title and role-family "
                "relevance"
            ),
            status=role_status,
            points_awarded=role_score,
            maximum_points=20,
            message=role_message,
            evidence=role_evidence,
        ),
        create_check(
            check_id=(
                "experience-requirement"
            ),
            category=(
                "Experience requirement"
            ),
            title=(
                "Relevant experience duration"
            ),
            status=experience_status,
            points_awarded=(
                experience_score
            ),
            maximum_points=15,
            message=experience_message,
            evidence=experience_evidence,
        ),
        create_check(
            check_id=(
                "education-requirement"
            ),
            category=(
                "Education requirement"
            ),
            title=(
                "Education-level evidence"
            ),
            status=education_status,
            points_awarded=(
                education_score
            ),
            maximum_points=(
                education_maximum
            ),
            message=education_message,
            evidence=education_evidence,
        ),
        create_check(
            check_id=(
                "supporting-evidence"
            ),
            category=(
                "Supporting evidence"
            ),
            title=(
                "Projects and certifications"
            ),
            status=supporting_status,
            points_awarded=(
                supporting_score
            ),
            maximum_points=10,
            message=supporting_message,
            evidence=supporting_evidence,
        ),
    ]
    requirements = {
        "recognized_job_skills": [
            display_name(skill_name)
            for skill_name
            in job_skills
        ],
        "minimum_experience_years": (
            minimum_experience_years
        ),
        "education_requirement": (
            display_name(
                education_requirement
            )
            if education_requirement
            else None
        ),
        "job_role_groups": [
            display_name(group)
            for group
            in job_role_groups
        ],
    }
    notes.extend(
        [
            (
                "Overall score is normalized "
                "using only applicable job "
                "requirements. Unspecified "
                "categories do not provide "
                "free points."
            ),
            (
                "Protected attributes, candidate "
                "name and contact details are not "
                "used in the match score."
            ),
            (
                "This result supports human review "
                "and does not hire, reject or make "
                "a final recruitment decision."
            ),
            (
                "The original CV remains the "
                "authoritative evidence source."
            ),
        ]
    )
    return {
        "score": score,
        "rating": rating_from_score(
            score
        ),
        "recommendation": (
            recommendation_from_score(
                score
            )
        ),
        "category_scores": (
            category_scores
        ),
        "requirements": requirements,
        "checks": checks,
        "matched_requirements": (
            matched_requirements
        ),
        "missing_requirements": (
            missing_requirements
        ),
        "notes": notes,
    }
def get_assignment(
    database: Session,
    job_id: int,
    candidate_id: int,
) -> JobCandidateAssignment | None:
    statement = (
        select(
            JobCandidateAssignment
        )
        .where(
            JobCandidateAssignment
            .job_profile_id
            == job_id,
            JobCandidateAssignment
            .candidate_cv_id
            == candidate_id,
        )
    )
    return database.scalar(
        statement
    )
def analyze_job_candidate_match(
    database: Session,
    job_id: int,
    candidate_id: int,
) -> JobMatchResult:
    job = get_job_profile(
        database=database,
        job_id=job_id,
    )
    candidate = get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    if (
        get_assignment(
            database=database,
            job_id=job_id,
            candidate_id=candidate_id,
        )
        is None
    ):
        raise JobMatchPrerequisiteError(
            "The candidate must be assigned "
            "to this job before match analysis."
        )
    if candidate.status != "ready":
        raise JobMatchPrerequisiteError(
            "The candidate CV must be "
            "processed successfully before "
            "job-match analysis."
        )
    profile_statement = (
        select(CandidateProfile)
        .where(
            CandidateProfile.candidate_cv_id
            == candidate_id
        )
    )
    profile = database.scalar(
        profile_statement
    )
    if profile is None:
        raise JobMatchPrerequisiteError(
            "Extract the structured candidate "
            "profile before job-match analysis."
        )
    candidate_data = (
        get_candidate_source_data(
            database=database,
            candidate_id=candidate_id,
            profile=profile,
        )
    )
    analysis = build_job_match_analysis(
        job_title=job.title,
        job_description=(
            job.description
        ),
        candidate_data=(
            candidate_data
        ),
    )
    result_statement = (
        select(JobMatchResult)
        .where(
            JobMatchResult.job_profile_id
            == job_id,
            JobMatchResult.candidate_cv_id
            == candidate_id,
        )
    )
    result = database.scalar(
        result_statement
    )
    if result is None:
        result = JobMatchResult(
            job_profile_id=job_id,
            candidate_cv_id=(
                candidate_id
            ),
            score=analysis["score"],
            rating=analysis["rating"],
            recommendation=(
                analysis[
                    "recommendation"
                ]
            ),
            category_scores=(
                analysis[
                    "category_scores"
                ]
            ),
            requirements=(
                analysis[
                    "requirements"
                ]
            ),
            checks=analysis["checks"],
            matched_requirements=(
                analysis[
                    "matched_requirements"
                ]
            ),
            missing_requirements=(
                analysis[
                    "missing_requirements"
                ]
            ),
            notes=analysis["notes"],
            engine_version=(
                JOB_MATCH_ENGINE_VERSION
            ),
        )
        database.add(result)
    else:
        result.score = analysis["score"]
        result.rating = analysis["rating"]
        result.recommendation = (
            analysis["recommendation"]
        )
        result.category_scores = (
            analysis["category_scores"]
        )
        result.requirements = (
            analysis["requirements"]
        )
        result.checks = analysis["checks"]
        result.matched_requirements = (
            analysis[
                "matched_requirements"
            ]
        )
        result.missing_requirements = (
            analysis[
                "missing_requirements"
            ]
        )
        result.notes = analysis["notes"]
        result.engine_version = (
            JOB_MATCH_ENGINE_VERSION
        )
    try:
        database.commit()
        database.refresh(result)
    except Exception:
        database.rollback()
        raise
    return result
def get_job_match_result(
    database: Session,
    job_id: int,
    candidate_id: int,
) -> JobMatchResult:
    get_job_profile(
        database=database,
        job_id=job_id,
    )
    get_candidate_cv(
        database=database,
        candidate_id=candidate_id,
    )
    statement = (
        select(JobMatchResult)
        .where(
            JobMatchResult.job_profile_id
            == job_id,
            JobMatchResult.candidate_cv_id
            == candidate_id,
        )
    )
    result = database.scalar(
        statement
    )
    if result is None:
        raise JobMatchResultNotFoundError(
            "Job-match analysis has not been "
            "completed for this candidate "
            "and job."
        )
    return result
def list_job_match_results(
    database: Session,
    job_id: int,
) -> list[JobMatchResult]:
    get_job_profile(
        database=database,
        job_id=job_id,
    )
    statement = (
        select(JobMatchResult)
        .where(
            JobMatchResult.job_profile_id
            == job_id
        )
        .order_by(
            JobMatchResult.score.desc(),
            JobMatchResult.updated_at.desc(),
        )
    )
    return list(
        database.scalars(
            statement
        ).all()
    )
def invalidate_job_matches_for_job(
    database: Session,
    job_id: int,
) -> None:
    try:
        database.execute(
            delete(
                JobMatchResult
            ).where(
                JobMatchResult
                .job_profile_id
                == job_id
            )
        )
        database.commit()
    except Exception:
        database.rollback()
        raise
def invalidate_job_matches_for_candidate(
    database: Session,
    candidate_id: int,
) -> None:
    try:
        database.execute(
            delete(
                JobMatchResult
            ).where(
                JobMatchResult
                .candidate_cv_id
                == candidate_id
            )
        )
        database.commit()
    except Exception:
        database.rollback()
        raise
def invalidate_job_match_pair(
    database: Session,
    job_id: int,
    candidate_id: int,
) -> None:
    try:
        database.execute(
            delete(
                JobMatchResult
            ).where(
                JobMatchResult
                .job_profile_id
                == job_id,
                JobMatchResult
                .candidate_cv_id
                == candidate_id,
            )
        )
        database.commit()
    except Exception:
        database.rollback()
        raise
