
from collections.abc import Generator
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
from backend.app.models.candidate_ats_result import (
    CandidateATSResult,
)
from backend.app.models.candidate_cv import (
    CandidateCV,
)
from backend.app.models.candidate_cv_page import (
    CandidateCVPage,
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
def prepare_ats_environment(
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
    email = "ats-admin@example.com"
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
def complete_cv_text() -> str:
    achievement_lines = "\n".join(
        (
            "- Designed and executed manual "
            "and automated test cases for "
            "business-critical web applications."
        )
        for _ in range(8)
    )
    return (
        "SALMAN JAHAN RAFI\n"
        "Email: candidate@example.com\n"
        "Phone: +880 1700 000000\n"
        "LinkedIn: "
        "https://linkedin.com/in/candidate\n"
        "\n"
        "PROFESSIONAL SUMMARY\n"
        "Software quality assurance professional "
        "with experience in manual testing, API "
        "testing, regression testing and defect "
        "management.\n"
        "\n"
        "WORK EXPERIENCE\n"
        "Software QA Engineer\n"
        "Example Technology Limited\n"
        "March 2024 - Present\n"
        f"{achievement_lines}\n"
        "\n"
        "EDUCATION\n"
        "Bachelor of Science in Computer Science\n"
        "Example University\n"
        "2023\n"
        "\n"
        "TECHNICAL SKILLS\n"
        "Python, SQL, Playwright, Cypress, "
        "Selenium, Postman, Jira and Git\n"
        "\n"
        "PROJECTS\n"
        "Automated Regression Testing Framework\n"
        "- Created reusable browser automation "
        "tests with Playwright and Python.\n"
        "\n"
        "CERTIFICATIONS\n"
        "Software Testing Fundamentals - 2024\n"
    )
def create_candidate(
    tmp_path: Path,
    text: str | None,
    status_value: str = "ready",
) -> tuple[int, Path]:
    candidate_path = (
        tmp_path
        / (
            f"candidate-"
            f"{status_value}.pdf"
        )
    )
    candidate_path.write_bytes(
        b"%PDF-1.4 ATS test"
    )
    with TestingSessionLocal() as database:
        user = database.scalar(
            select(User).where(
                User.email
                == "ats-admin@example.com"
            )
        )
        assert user is not None
        candidate = CandidateCV(
            original_name="Candidate.pdf",
            stored_name=(
                candidate_path.name
            ),
            file_path=str(candidate_path),
            sha256="b" * 64,
            size_bytes=1000,
            mime_type="application/pdf",
            status=status_value,
            page_count=(
                1 if text is not None else None
            ),
            uploaded_by_id=user.id,
        )
        database.add(candidate)
        database.flush()
        if text is not None:
            database.add(
                CandidateCVPage(
                    candidate_cv_id=(
                        candidate.id
                    ),
                    page_number=1,
                    text=text,
                    char_count=len(text),
                )
            )
        database.commit()
        return (
            candidate.id,
            candidate_path,
        )
def test_ats_analysis_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            "/api/candidates/1/ats/analyze"
        )
    assert response.status_code == 401
def test_ats_analysis_requires_ready_cv(
    tmp_path: Path,
):
    headers = create_admin_headers()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        text=None,
        status_value="uploaded",
    )
    with TestClient(app) as client:
        response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/ats/analyze"
            ),
            headers=headers,
        )
    assert response.status_code == 409
def test_admin_can_analyze_and_read_ats_result(
    tmp_path: Path,
):
    headers = create_admin_headers()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        text=complete_cv_text(),
    )
    with TestClient(app) as client:
        analyze_response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/ats/analyze"
            ),
            headers=headers,
        )
        read_response = client.get(
            (
                f"/api/candidates/"
                f"{candidate_id}/ats"
            ),
            headers=headers,
        )
    assert analyze_response.status_code == 200
    assert read_response.status_code == 200
    result = analyze_response.json()
    assert result["candidate_cv_id"] == candidate_id
    assert 0 <= result["score"] <= 100
    assert len(result["checks"]) == 6
    assert result["engine_version"] == (
        "deterministic-ats-v1.1"
    )
def test_reanalysis_updates_existing_result(
    tmp_path: Path,
):
    headers = create_admin_headers()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        text=complete_cv_text(),
    )
    endpoint = (
        f"/api/candidates/"
        f"{candidate_id}/ats/analyze"
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
                    CandidateATSResult.id
                )
            )
        )
    assert result_count == 1
def test_missing_ats_result_returns_404(
    tmp_path: Path,
):
    headers = create_admin_headers()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        text=complete_cv_text(),
    )
    with TestClient(app) as client:
        response = client.get(
            (
                f"/api/candidates/"
                f"{candidate_id}/ats"
            ),
            headers=headers,
        )
    assert response.status_code == 404
def test_complete_cv_receives_good_score(
    tmp_path: Path,
):
    headers = create_admin_headers()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        text=complete_cv_text(),
    )
    with TestClient(app) as client:
        response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/ats/analyze"
            ),
            headers=headers,
        )
    result = response.json()
    assert response.status_code == 200
    assert result["score"] >= 70
    assert result["rating"] in {
        "Good",
        "Excellent",
    }
def test_sparse_cv_has_actionable_warnings(
    tmp_path: Path,
):
    headers = create_admin_headers()
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        text=(
            "CANDIDATE NAME\n"
            "Brief profile text."
        ),
    )
    with TestClient(app) as client:
        response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/ats/analyze"
            ),
            headers=headers,
        )
    result = response.json()
    assert response.status_code == 200
    assert result["score"] < 70
    assert len(result["suggestions"]) >= 3
    assert any(
        check["status"] in {
            "warning",
            "fail",
        }
        for check in result["checks"]
    )
def test_permanent_candidate_delete_removes_ats_result(
    tmp_path: Path,
):
    headers = create_admin_headers()
    candidate_id, candidate_path = (
        create_candidate(
            tmp_path=tmp_path,
            text=complete_cv_text(),
        )
    )
    with TestClient(app) as client:
        analyze_response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/ats/analyze"
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
                    CandidateATSResult.id
                )
            )
        )
    assert result_count == 0

def test_suspicious_link_and_page_marker_reduce_score(
    tmp_path: Path,
):
    headers = create_admin_headers()
    calibrated_text = (
        complete_cv_text()
        .replace(
            (
                "https://linkedin.com/"
                "in/candidate"
            ),
            (
                "https://linkedin.com/"
                "in/candidate01700000000"
            ),
        )
        .replace(
            "- Designed",
            "Designed",
        )
        + "\n2 | P a g e\n"
    )
    candidate_id, _ = create_candidate(
        tmp_path=tmp_path,
        text=calibrated_text,
    )
    with TestClient(app) as client:
        response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/ats/analyze"
            ),
            headers=headers,
        )
    result = response.json()
    assert response.status_code == 200
    assert result["score"] < 95
    assert (
        result["category_scores"][
            "contact_information"
        ]
        < 15
    )
    assert (
        result["category_scores"][
            "layout_and_parsing"
        ]
        < 10
    )
    assert any(
        (
            "professional profile URL"
            in suggestion
        )
        for suggestion
        in result["suggestions"]
    )
    assert any(
        (
            "page numbering"
            in suggestion
        )
        for suggestion
        in result["suggestions"]
    )

def test_strict_ats_rating_boundaries():
    from backend.app.services.candidate_ats_service import (
        rating_from_score,
        risk_level_from_score,
    )
    assert rating_from_score(
        90
    ) == "Excellent"
    assert risk_level_from_score(
        90
    ) == "low"
    assert rating_from_score(
        89
    ) == "Good"
    assert risk_level_from_score(
        89
    ) == "low-to-moderate"
    assert rating_from_score(
        74
    ) == "Needs improvement"
    assert rating_from_score(
        54
    ) == "Poor"
