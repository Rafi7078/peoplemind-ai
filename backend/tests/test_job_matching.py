
from collections.abc import Generator
from hashlib import sha256
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import (
    create_engine,
    func,
    select,
)
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool
from backend.app.core.security import (
    create_access_token,
)
from backend.app.db.database import (
    Base,
    get_db,
)
from backend.app.main import app
from backend.app.models.candidate_cv import (
    CandidateCV,
)
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
from backend.app.models.job_profile import (
    JobProfile,
)
from backend.app.models.user import User
from backend.app.services import (
    candidate_service,
)
test_engine = create_engine(
    "sqlite://",
    connect_args={
        "check_same_thread": False,
    },
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)
def override_get_db() -> Generator[
    Session,
    None,
    None,
]:
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()
@pytest.fixture(autouse=True)
def prepare_job_match_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    Base.metadata.drop_all(
        bind=test_engine
    )
    Base.metadata.create_all(
        bind=test_engine
    )
    app.dependency_overrides[
        get_db
    ] = override_get_db
    monkeypatch.setattr(
        candidate_service.settings,
        "candidate_upload_dir",
        str(tmp_path),
    )
    yield
    app.dependency_overrides.pop(
        get_db,
        None,
    )
def create_admin_headers() -> dict[
    str,
    str,
]:
    email = "match-admin@example.com"
    with TestingSessionLocal() as database:
        user = User(
            email=email,
            hashed_password="not-used",
            is_active=True,
            is_admin=True,
        )
        database.add(user)
        database.commit()
    token = create_access_token(
        subject=email
    )
    return {
        "Authorization": f"Bearer {token}"
    }
def get_admin(
    database: Session,
) -> User:
    user = database.scalar(
        select(User).where(
            User.email
            == "match-admin@example.com"
        )
    )
    assert user is not None
    return user
def create_job() -> int:
    with TestingSessionLocal() as database:
        user = get_admin(database)
        job = JobProfile(
            title="Software QA Engineer",
            department="Engineering",
            location="Dhaka",
            employment_type="Full-time",
            description=(
                "We need a Software QA Engineer. "
                "Required skills include manual "
                "testing, API testing, regression "
                "testing, SQL, Postman, Jira and "
                "Selenium. Minimum 1 year of "
                "experience is required. A "
                "bachelor's degree is required."
            ),
            status="active",
            created_by_id=user.id,
        )
        database.add(job)
        database.commit()
        return job.id
def create_candidate(
    tmp_path: Path,
    job_id: int,
    key: str,
    strong_match: bool,
    assigned: bool = True,
    with_profile: bool = True,
) -> tuple[int, Path]:
    candidate_path = (
        tmp_path
        / f"candidate-{key}.pdf"
    )
    candidate_path.write_bytes(
        b"%PDF-1.4 Job match test"
    )
    with TestingSessionLocal() as database:
        user = get_admin(database)
        candidate = CandidateCV(
            original_name=(
                f"Candidate-{key}.pdf"
            ),
            stored_name=(
                candidate_path.name
            ),
            file_path=str(
                candidate_path
            ),
            sha256=sha256(
                key.encode("utf-8")
            ).hexdigest(),
            size_bytes=1000,
            mime_type="application/pdf",
            status="ready",
            page_count=1,
            uploaded_by_id=user.id,
        )
        database.add(candidate)
        database.flush()
        if strong_match:
            page_text = (
                "Software QA Engineer with "
                "manual testing, API testing, "
                "regression testing, SQL, "
                "Postman, Jira and Selenium."
            )
        else:
            page_text = (
                "Graphic designer with Adobe "
                "Photoshop and illustration "
                "experience."
            )
        database.add(
            CandidateCVPage(
                candidate_cv_id=(
                    candidate.id
                ),
                page_number=1,
                text=page_text,
                char_count=len(
                    page_text
                ),
            )
        )
        if with_profile:
            if strong_match:
                profile = CandidateProfile(
                    candidate_cv_id=(
                        candidate.id
                    ),
                    candidate_name=(
                        "Candidate Strong"
                    ),
                    contact_information={
                        "email": (
                            "strong@example.com"
                        ),
                        "phone": (
                            "01700000000"
                        ),
                    },
                    latest_completed_education={
                        (
                            "degree_or_qualification"
                        ): (
                            "Bachelor of Science "
                            "in Computer Science"
                        ),
                        "institution": (
                            "Example University"
                        ),
                        "completion_year": "2025",
                        "cgpa_or_gpa": "3.50",
                    },
                    work_experience=[
                        {
                            "company": (
                                "Example Technology"
                            ),
                            "job_title": (
                                "Software QA Engineer"
                            ),
                            "start_date": (
                                "January 2024"
                            ),
                            "end_date": (
                                "December 2025"
                            ),
                            "duration": "2 years",
                        }
                    ],
                    skills={
                        "technical_skills": [
                            "Manual Testing",
                            "API Testing",
                            "Regression Testing",
                            "SQL",
                        ],
                        "tools_and_platforms": [
                            "Postman",
                            "Jira",
                            "Selenium",
                        ],
                        "operational_skills": [
                            "Defect Management"
                        ],
                    },
                    projects=[
                        {
                            "project_title": (
                                "Automated Regression "
                                "Testing Framework"
                            ),
                            "technologies": [
                                "Selenium",
                                "Python",
                            ],
                        }
                    ],
                    certifications=[
                        {
                            "certification_title": (
                                "Software Testing "
                                "Foundation"
                            ),
                            (
                                "issuing_organization"
                            ): "Example Institute",
                            "completion_date": "2025",
                        }
                    ],
                    extraction_model=(
                        "deterministic-parser-v5"
                    ),
                )
            else:
                profile = CandidateProfile(
                    candidate_cv_id=(
                        candidate.id
                    ),
                    candidate_name=(
                        "Candidate Weak"
                    ),
                    contact_information={
                        "email": (
                            "weak@example.com"
                        ),
                    },
                    latest_completed_education={
                        (
                            "degree_or_qualification"
                        ): (
                            "Bachelor of Business "
                            "Administration"
                        ),
                        "institution": (
                            "Example University"
                        ),
                        "completion_year": "2024",
                        "cgpa_or_gpa": "3.20",
                    },
                    work_experience=[
                        {
                            "company": (
                                "Creative Studio"
                            ),
                            "job_title": (
                                "Graphic Designer"
                            ),
                            "start_date": (
                                "January 2022"
                            ),
                            "end_date": (
                                "December 2024"
                            ),
                            "duration": "3 years",
                        }
                    ],
                    skills={
                        "technical_skills": [
                            "Illustration"
                        ],
                        "tools_and_platforms": [
                            "Adobe Photoshop"
                        ],
                        "operational_skills": [
                            "Brand Design"
                        ],
                    },
                    projects=[
                        {
                            "project_title": (
                                "Brand Identity Design"
                            ),
                            "technologies": [
                                "Adobe Photoshop"
                            ],
                        }
                    ],
                    certifications=[],
                    extraction_model=(
                        "deterministic-parser-v5"
                    ),
                )
            database.add(profile)
        if assigned:
            database.add(
                JobCandidateAssignment(
                    job_profile_id=job_id,
                    candidate_cv_id=(
                        candidate.id
                    ),
                    assigned_by_id=user.id,
                )
            )
        database.commit()
        return (
            candidate.id,
            candidate_path,
        )
def analyze_endpoint(
    job_id: int,
    candidate_id: int,
) -> str:
    return (
        f"/api/jobs/{job_id}/"
        f"candidates/{candidate_id}/"
        "match/analyze"
    )
def read_endpoint(
    job_id: int,
    candidate_id: int,
) -> str:
    return (
        f"/api/jobs/{job_id}/"
        f"candidates/{candidate_id}/"
        "match"
    )
def test_job_match_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            (
                "/api/jobs/1/candidates/"
                "1/match/analyze"
            )
        )
    assert response.status_code == 401
def test_job_match_requires_assignment(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="unassigned",
        strong_match=True,
        assigned=False,
    )
    with TestClient(app) as client:
        response = client.post(
            analyze_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
    assert response.status_code == 409
def test_job_match_requires_structured_profile(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="no-profile",
        strong_match=True,
        with_profile=False,
    )
    with TestClient(app) as client:
        response = client.post(
            analyze_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
    assert response.status_code == 409
def test_admin_can_analyze_and_read_strong_match(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="strong",
        strong_match=True,
    )
    with TestClient(app) as client:
        analyze_response = client.post(
            analyze_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
        read_response = client.get(
            read_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
    assert (
        analyze_response.status_code
        == 200
    )
    assert (
        read_response.status_code
        == 200
    )
    result = analyze_response.json()
    assert result["score"] >= 85
    assert result["rating"] in {
        "Strong match",
        "Good match",
    }
    assert len(
        result["checks"]
    ) == 5
    assert (
        result["engine_version"]
        == "deterministic-job-match-v1.1"
    )
    assert (
        result["matched_requirements"]
    )
    result_text = str(result).casefold()
    assert "strong@example.com" not in (
        result_text
    )
    assert "01700000000" not in (
        result_text
    )
def test_reanalysis_updates_existing_result(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="reanalyze",
        strong_match=True,
    )
    endpoint = analyze_endpoint(
        job_id,
        candidate_id,
    )
    with TestClient(app) as client:
        first_response = client.post(
            endpoint,
            headers=headers,
        )
        second_response = client.post(
            endpoint,
            headers=headers,
        )
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert (
        first_response.json()["id"]
        == second_response.json()["id"]
    )
    with TestingSessionLocal() as database:
        result_count = database.scalar(
            select(
                func.count(
                    JobMatchResult.id
                )
            )
        )
    assert result_count == 1
def test_missing_job_match_returns_404(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="not-analyzed",
        strong_match=True,
    )
    with TestClient(app) as client:
        response = client.get(
            read_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
    assert response.status_code == 404
def test_job_ranking_orders_candidates_by_score(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    strong_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="rank-strong",
        strong_match=True,
    )
    weak_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="rank-weak",
        strong_match=False,
    )
    with TestClient(app) as client:
        strong_response = client.post(
            analyze_endpoint(
                job_id,
                strong_id,
            ),
            headers=headers,
        )
        weak_response = client.post(
            analyze_endpoint(
                job_id,
                weak_id,
            ),
            headers=headers,
        )
        ranking_response = client.get(
            (
                f"/api/jobs/"
                f"{job_id}/matches"
            ),
            headers=headers,
        )
    assert strong_response.status_code == 200
    assert weak_response.status_code == 200
    assert ranking_response.status_code == 200
    ranking = ranking_response.json()
    assert len(ranking) == 2
    assert (
        ranking[0][
            "candidate_cv_id"
        ]
        == strong_id
    )
    assert (
        ranking[0]["score"]
        > ranking[1]["score"]
    )
def test_job_update_invalidates_matches(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="job-update",
        strong_match=True,
    )
    with TestClient(app) as client:
        analyze_response = client.post(
            analyze_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
        update_response = client.patch(
            f"/api/jobs/{job_id}",
            headers=headers,
            json={
                "description": (
                    "Updated job requirements "
                    "now emphasize Python, SQL, "
                    "Power BI and data analysis."
                )
            },
        )
        read_response = client.get(
            read_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
    assert analyze_response.status_code == 200
    assert update_response.status_code == 200
    assert read_response.status_code == 404
def test_assignment_removal_invalidates_match(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="remove-assignment",
        strong_match=True,
    )
    assignment_endpoint = (
        f"/api/jobs/{job_id}/"
        f"candidates/{candidate_id}"
    )
    with TestClient(app) as client:
        analyze_response = client.post(
            analyze_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
        remove_response = client.delete(
            assignment_endpoint,
            headers=headers,
        )
        read_response = client.get(
            read_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
    assert analyze_response.status_code == 200
    assert remove_response.status_code == 204
    assert read_response.status_code == 404
def test_permanent_candidate_delete_removes_match(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    (
        candidate_id,
        candidate_path,
    ) = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="delete-candidate",
        strong_match=True,
    )
    with TestClient(app) as client:
        analyze_response = client.post(
            analyze_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
        delete_response = client.delete(
            (
                f"/api/candidates/"
                f"{candidate_id}"
            ),
            headers=headers,
        )
    assert analyze_response.status_code == 200
    assert delete_response.status_code == 204
    assert not candidate_path.exists()
    with TestingSessionLocal() as database:
        result_count = database.scalar(
            select(
                func.count(
                    JobMatchResult.id
                )
            )
        )
    assert result_count == 0
def test_name_and_contact_do_not_affect_score(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        job_id=job_id,
        key="protected-fields",
        strong_match=True,
    )
    endpoint = analyze_endpoint(
        job_id,
        candidate_id,
    )
    with TestClient(app) as client:
        first_response = client.post(
            endpoint,
            headers=headers,
        )
    first_score = (
        first_response.json()["score"]
    )
    with TestingSessionLocal() as database:
        profile = database.scalar(
            select(CandidateProfile)
            .where(
                CandidateProfile
                .candidate_cv_id
                == candidate_id
            )
        )
        assert profile is not None
        profile.candidate_name = (
            "Completely Different Name"
        )
        profile.contact_information = {
            "email": "different@example.com",
            "phone": "01999999999",
            "linkedin": (
                "https://linkedin.com/"
                "in/different"
            ),
        }
        database.commit()
    with TestClient(app) as client:
        second_response = client.post(
            endpoint,
            headers=headers,
        )
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert (
        second_response.json()["score"]
        == first_score
    )

def test_data_annotation_role_and_unscored_education():
    from backend.app.services.job_match_service import (
        build_job_match_analysis,
    )
    candidate_data = {
        "structured_skills": [
            "Data Annotation",
            "CVAT",
            "Problem Solving",
        ],
        "work_titles": [
            "Data Annotation Analyst",
        ],
        "projects": [
            "Image Annotation Quality Project",
            "CVAT",
        ],
        "certifications": [],
        "raw_text": (
            "Data annotation using CVAT, "
            "quality review and problem solving."
        ),
        "candidate_degree": "",
        "work_experience_count": 1,
        "project_count": 1,
        "certification_count": 0,
        "total_experience_months": 12,
    }
    result = build_job_match_analysis(
        job_title=(
            "Senior Data Annotation "
            "Analyst - CVAT Team"
        ),
        job_description=(
            "The role requires data annotation, "
            "CVAT and problem-solving skills."
        ),
        candidate_data=candidate_data,
    )
    assert (
        "Data Annotation"
        in result["requirements"][
            "job_role_groups"
        ]
    )
    education_check = next(
        check
        for check in result["checks"]
        if check["check_id"]
        == "education-requirement"
    )
    assert (
        education_check["status"]
        == "not_specified"
    )
    assert (
        education_check[
            "points_awarded"
        ]
        == 0
    )
    assert (
        education_check["max_points"]
        == 0
    )
    assert result["score"] >= 80
