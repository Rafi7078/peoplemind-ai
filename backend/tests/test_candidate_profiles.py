
from collections.abc import Generator
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
from backend.app.models.user import User
from backend.app.schemas.candidate_profile import (
    CandidateCertification,
    CandidateContactInformation,
    CandidateLatestEducation,
    CandidateProfileData,
    CandidateProject,
    CandidateSkills,
    CandidateWorkExperience,
)
from backend.app.services import (
    candidate_profile_service,
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
def prepare_profile_environment() -> (
    Generator[None, None, None]
):
    Base.metadata.drop_all(
        bind=test_engine
    )
    Base.metadata.create_all(
        bind=test_engine
    )
    app.dependency_overrides[
        get_db
    ] = override_get_db
    yield
    app.dependency_overrides.pop(
        get_db,
        None,
    )
def create_admin_headers() -> dict[
    str,
    str,
]:
    email = "profile-admin@example.com"
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
def create_candidate(
    status_value: str = "ready",
) -> int:
    with TestingSessionLocal() as database:
        user = database.scalar(
            select(User).where(
                User.email
                == "profile-admin@example.com"
            )
        )
        assert user is not None
        candidate = CandidateCV(
            original_name="Candidate.pdf",
            stored_name=(
                f"candidate-{status_value}.pdf"
            ),
            file_path=(
                f"data/candidate_cvs/"
                f"candidate-{status_value}.pdf"
            ),
            sha256=(
                "a" * 63
                + (
                    "1"
                    if status_value == "ready"
                    else "2"
                )
            ),
            size_bytes=1000,
            mime_type="application/pdf",
            status=status_value,
            page_count=2,
            uploaded_by_id=user.id,
        )
        database.add(candidate)
        database.flush()
        if status_value == "ready":
            database.add_all(
                [
                    CandidateCVPage(
                        candidate_cv_id=(
                            candidate.id
                        ),
                        page_number=1,
                        text=(
                            "SALMAN JAHAN RAFI\n"
                            "WORK EXPERIENCES\n"
                            "Dream71 Bangladesh Limited\n"
                            "QA Engineer Intern\n"
                            "Tenure: March 2026 - "
                            "July 2026\n"
                            "EDUCATION\n"
                            "BSc in Information and "
                            "Communication Engineering\n"
                            "Bangladesh University of "
                            "Professionals\n"
                            "CGPA 3.59 out of 4.00\n"
                            "2025\n"
                        ),
                        char_count=250,
                    ),
                    CandidateCVPage(
                        candidate_cv_id=(
                            candidate.id
                        ),
                        page_number=2,
                        text=(
                            "TECHNICAL SKILLS\n"
                            "Python, SQL, Power BI\n"
                            "PROJECTS\n"
                            "HR Analytics Dashboard\n"
                            "Power BI\n"
                        ),
                        char_count=100,
                    ),
                ]
            )
        database.commit()
        return candidate.id
def fake_profile(
    candidate_name: str = (
        "SALMAN JAHAN RAFI"
    ),
) -> CandidateProfileData:
    return CandidateProfileData(
        candidate_name=candidate_name,
        contact_information=(
            CandidateContactInformation(
                email="candidate@example.com",
                phone="01700000000",
                linkedin=None,
                github=(
                    "https://github.com/example"
                ),
                portfolio=None,
            )
        ),
        latest_completed_education=(
            CandidateLatestEducation(
                degree_or_qualification=(
                    "BSc in Information and "
                    "Communication Engineering"
                ),
                institution=(
                    "Bangladesh University "
                    "of Professionals"
                ),
                completion_year="2025",
                cgpa_or_gpa=(
                    "3.59 out of 4.00"
                ),
            )
        ),
        work_experience=[
            CandidateWorkExperience(
                company=(
                    "Dream71 Bangladesh Limited"
                ),
                job_title=(
                    "QA Engineer Intern"
                ),
                start_date="March 2026",
                end_date="July 2026",
                duration=None,
            )
        ],
        skills=CandidateSkills(
            technical_skills=[
                "Python",
                "SQL",
            ],
            tools_and_platforms=[
                "Power BI",
            ],
            operational_skills=[
                "Data validation",
            ],
        ),
        projects=[
            CandidateProject(
                project_title=(
                    "HR Analytics Dashboard"
                ),
                technologies=[
                    "Power BI"
                ],
            )
        ],
        certifications=[
            CandidateCertification(
                certification_title=(
                    "Data Analytics Simulation"
                ),
                issuing_organization=(
                    "Deloitte"
                ),
                completion_date=None,
            )
        ],
    )
def test_profile_extraction_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            "/api/candidates/1/profile/extract"
        )
    assert response.status_code == 401
def test_profile_extraction_requires_ready_cv():
    headers = create_admin_headers()
    candidate_id = create_candidate(
        status_value="uploaded"
    )
    with TestClient(app) as client:
        response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/profile/extract"
            ),
            headers=headers,
        )
    assert response.status_code == 409
def test_admin_can_extract_and_read_profile(
    monkeypatch: pytest.MonkeyPatch,
):
    headers = create_admin_headers()
    candidate_id = create_candidate()
    monkeypatch.setattr(
        candidate_profile_service,
        "parse_candidate_profile",
        lambda cv_text: fake_profile(),
    )
    with TestClient(app) as client:
        extract_response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/profile/extract"
            ),
            headers=headers,
        )
        read_response = client.get(
            (
                f"/api/candidates/"
                f"{candidate_id}/profile"
            ),
            headers=headers,
        )
    assert extract_response.status_code == 200
    assert read_response.status_code == 200
    result = extract_response.json()
    assert (
        result["candidate_name"]
        == "SALMAN JAHAN RAFI"
    )
    assert (
        result[
            "latest_completed_education"
        ]["completion_year"]
        == "2025"
    )
    assert (
        result["work_experience"][0][
            "duration"
        ]
        == "5 months"
    )
    assert (
        result["projects"][0][
            "technologies"
        ]
        == ["Power BI"]
    )
def test_missing_profile_returns_404():
    headers = create_admin_headers()
    candidate_id = create_candidate()
    with TestClient(app) as client:
        response = client.get(
            (
                f"/api/candidates/"
                f"{candidate_id}/profile"
            ),
            headers=headers,
        )
    assert response.status_code == 404
def test_reextract_updates_existing_profile(
    monkeypatch: pytest.MonkeyPatch,
):
    headers = create_admin_headers()
    candidate_id = create_candidate()
    monkeypatch.setattr(
        candidate_profile_service,
        "parse_candidate_profile",
        lambda cv_text: fake_profile(
            "FIRST NAME"
        ),
    )
    with TestClient(app) as client:
        first_response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/profile/extract"
            ),
            headers=headers,
        )
        first_profile_id = (
            first_response.json()["id"]
        )
        monkeypatch.setattr(
            candidate_profile_service,
            "parse_candidate_profile",
            lambda cv_text: fake_profile(
                "UPDATED NAME"
            ),
        )
        second_response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/profile/extract"
            ),
            headers=headers,
        )
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert (
        second_response.json()["id"]
        == first_profile_id
    )
    assert (
        second_response.json()[
            "candidate_name"
        ]
        == "UPDATED NAME"
    )
    with TestingSessionLocal() as database:
        profile_count = database.scalar(
            select(
                func.count(
                    CandidateProfile.id
                )
            )
        )
    assert profile_count == 1
