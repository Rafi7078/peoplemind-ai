
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
def prepare_management_environment(
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
    email = "management-admin@example.com"
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
def create_job_and_candidate(
    tmp_path: Path,
) -> tuple[int, int, int, Path]:
    candidate_path = (
        tmp_path / "candidate.pdf"
    )
    candidate_path.write_bytes(
        b"%PDF-1.4 test candidate"
    )
    with TestingSessionLocal() as database:
        user = database.scalar(
            select(User).where(
                User.email
                == "management-admin@example.com"
            )
        )
        assert user is not None
        job = JobProfile(
            title="Software QA Engineer",
            department="Engineering",
            location="Dhaka",
            employment_type="Full-time",
            description=(
                "A detailed Software QA Engineer "
                "job description for testing."
            ),
            status="active",
            created_by_id=user.id,
        )
        candidate = CandidateCV(
            original_name="Candidate.pdf",
            stored_name="candidate.pdf",
            file_path=str(candidate_path),
            sha256="a" * 64,
            size_bytes=100,
            mime_type="application/pdf",
            status="ready",
            page_count=1,
            uploaded_by_id=user.id,
        )
        database.add_all(
            [
                job,
                candidate,
            ]
        )
        database.commit()
        return (
            job.id,
            candidate.id,
            user.id,
            candidate_path,
        )
def test_assignment_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            "/api/jobs/1/candidates/1"
        )
    assert response.status_code == 401
def test_admin_can_assign_list_and_filter_candidate(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id, candidate_id, _, _ = (
        create_job_and_candidate(
            tmp_path
        )
    )
    with TestClient(app) as client:
        unassigned_before = client.get(
            "/api/candidates/unassigned",
            headers=headers,
        )
        assign_response = client.post(
            (
                f"/api/jobs/{job_id}/"
                f"candidates/{candidate_id}"
            ),
            headers=headers,
        )
        job_candidates = client.get(
            (
                f"/api/jobs/{job_id}/"
                "candidates"
            ),
            headers=headers,
        )
        unassigned_after = client.get(
            "/api/candidates/unassigned",
            headers=headers,
        )
    assert (
        len(unassigned_before.json())
        == 1
    )
    assert assign_response.status_code == 201
    assert (
        job_candidates.json()[0]["id"]
        == candidate_id
    )
    assert unassigned_after.json() == []
def test_duplicate_assignment_is_rejected(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id, candidate_id, _, _ = (
        create_job_and_candidate(
            tmp_path
        )
    )
    endpoint = (
        f"/api/jobs/{job_id}/"
        f"candidates/{candidate_id}"
    )
    with TestClient(app) as client:
        first_response = client.post(
            endpoint,
            headers=headers,
        )
        duplicate_response = client.post(
            endpoint,
            headers=headers,
        )
    assert first_response.status_code == 201
    assert (
        duplicate_response.status_code
        == 409
    )
def test_remove_from_job_preserves_candidate(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id, candidate_id, _, _ = (
        create_job_and_candidate(
            tmp_path
        )
    )
    endpoint = (
        f"/api/jobs/{job_id}/"
        f"candidates/{candidate_id}"
    )
    with TestClient(app) as client:
        client.post(
            endpoint,
            headers=headers,
        )
        remove_response = client.delete(
            endpoint,
            headers=headers,
        )
        all_candidates = client.get(
            "/api/candidates",
            headers=headers,
        )
        unassigned = client.get(
            "/api/candidates/unassigned",
            headers=headers,
        )
    assert remove_response.status_code == 204
    assert len(all_candidates.json()) == 1
    assert (
        unassigned.json()[0]["id"]
        == candidate_id
    )
def test_admin_can_edit_and_archive_job(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id, _, _, _ = (
        create_job_and_candidate(
            tmp_path
        )
    )
    with TestClient(app) as client:
        response = client.patch(
            f"/api/jobs/{job_id}",
            headers=headers,
            json={
                "title": (
                    "Senior Software QA Engineer"
                ),
                "status": "archived",
            },
        )
    assert response.status_code == 200
    assert (
        response.json()["title"]
        == "Senior Software QA Engineer"
    )
    assert (
        response.json()["status"]
        == "archived"
    )
def test_delete_job_preserves_candidate(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id, candidate_id, _, _ = (
        create_job_and_candidate(
            tmp_path
        )
    )
    with TestClient(app) as client:
        client.post(
            (
                f"/api/jobs/{job_id}/"
                f"candidates/{candidate_id}"
            ),
            headers=headers,
        )
        delete_response = client.delete(
            f"/api/jobs/{job_id}",
            headers=headers,
        )
        candidates_response = client.get(
            "/api/candidates",
            headers=headers,
        )
    assert delete_response.status_code == 204
    assert len(
        candidates_response.json()
    ) == 1
    with TestingSessionLocal() as database:
        assignment_count = database.scalar(
            select(
                func.count(
                    JobCandidateAssignment.id
                )
            )
        )
    assert assignment_count == 0
def test_permanent_candidate_delete_removes_related_data(
    tmp_path: Path,
):
    headers = create_admin_headers()
    (
        job_id,
        candidate_id,
        user_id,
        candidate_path,
    ) = create_job_and_candidate(
        tmp_path
    )
    with TestingSessionLocal() as database:
        database.add_all(
            [
                JobCandidateAssignment(
                    job_profile_id=job_id,
                    candidate_cv_id=(
                        candidate_id
                    ),
                    assigned_by_id=user_id,
                ),
                CandidateCVPage(
                    candidate_cv_id=(
                        candidate_id
                    ),
                    page_number=1,
                    text="Candidate text",
                    char_count=14,
                ),
                CandidateProfile(
                    candidate_cv_id=(
                        candidate_id
                    ),
                    candidate_name=(
                        "Candidate Name"
                    ),
                    contact_information={},
                    latest_completed_education=(
                        None
                    ),
                    work_experience=[],
                    skills={},
                    projects=[],
                    certifications=[],
                    extraction_model=(
                        "deterministic-parser-v5"
                    ),
                ),
            ]
        )
        database.commit()
    with TestClient(app) as client:
        response = client.delete(
            (
                f"/api/candidates/"
                f"{candidate_id}"
            ),
            headers=headers,
        )
    assert response.status_code == 204
    assert not candidate_path.exists()
    with TestingSessionLocal() as database:
        assert database.get(
            CandidateCV,
            candidate_id,
        ) is None
        assert database.scalar(
            select(
                func.count(
                    JobCandidateAssignment.id
                )
            )
        ) == 0
        assert database.scalar(
            select(
                func.count(
                    CandidateCVPage.id
                )
            )
        ) == 0
        assert database.scalar(
            select(
                func.count(
                    CandidateProfile.id
                )
            )
        ) == 0
def test_missing_management_resources_return_404():
    headers = create_admin_headers()
    with TestClient(app) as client:
        update_response = client.patch(
            "/api/jobs/9999",
            headers=headers,
            json={
                "status": "archived"
            },
        )
        delete_candidate_response = (
            client.delete(
                "/api/candidates/9999",
                headers=headers,
            )
        )
    assert update_response.status_code == 404
    assert (
        delete_candidate_response
        .status_code
        == 404
    )
