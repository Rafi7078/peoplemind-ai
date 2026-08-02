
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
from backend.app.models.candidate_ats_result import (
    CandidateATSResult,
)
from backend.app.models.candidate_cv import (
    CandidateCV,
)
from backend.app.models.candidate_profile import (
    CandidateProfile,
)
from backend.app.models.job_candidate_assignment import (
    JobCandidateAssignment,
)
from backend.app.models.job_candidate_review import (
    JobCandidateReview,
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
def prepare_ranking_environment(
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
    email = "ranking-admin@example.com"
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
            == "ranking-admin@example.com"
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
                "Software QA role requiring "
                "manual testing, API testing, "
                "SQL and Selenium experience."
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
    *,
    match_score: int | None = None,
    ats_score: int | None = None,
    assigned: bool = True,
) -> tuple[int, Path]:
    candidate_path = (
        tmp_path
        / f"ranking-{key}.pdf"
    )
    candidate_path.write_bytes(
        b"%PDF-1.4 ranking test"
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
        database.add(
            CandidateProfile(
                candidate_cv_id=(
                    candidate.id
                ),
                candidate_name=(
                    f"Candidate {key.title()}"
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
            )
        )
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
        if match_score is not None:
            database.add(
                JobMatchResult(
                    job_profile_id=job_id,
                    candidate_cv_id=(
                        candidate.id
                    ),
                    score=match_score,
                    rating=(
                        "Strong match"
                        if match_score >= 85
                        else (
                            "Good match"
                            if match_score >= 70
                            else (
                                "Partial match"
                                if match_score >= 55
                                else "Limited match"
                            )
                        )
                    ),
                    recommendation=(
                        "human_review_required"
                    ),
                    category_scores={},
                    requirements={},
                    checks=[],
                    matched_requirements=[],
                    missing_requirements=[],
                    notes=[],
                    engine_version=(
                        "deterministic-job-match-v1.1"
                    ),
                )
            )
        if ats_score is not None:
            database.add(
                CandidateATSResult(
                    candidate_cv_id=(
                        candidate.id
                    ),
                    score=ats_score,
                    rating=(
                        "Excellent"
                        if ats_score >= 90
                        else "Good"
                    ),
                    risk_level="low",
                    category_scores={},
                    checks=[],
                    suggestions=[],
                    engine_version=(
                        "deterministic-ats-v1.1"
                    ),
                )
            )
        database.commit()
        return (
            candidate.id,
            candidate_path,
        )
def ranking_endpoint(
    job_id: int,
) -> str:
    return (
        f"/api/jobs/{job_id}/ranking"
    )
def review_endpoint(
    job_id: int,
    candidate_id: int,
) -> str:
    return (
        f"/api/jobs/{job_id}/"
        f"candidates/{candidate_id}/"
        "review"
    )
def save_review(
    client: TestClient,
    headers: dict[str, str],
    job_id: int,
    candidate_id: int,
    status_value: str,
    notes: str | None = None,
):
    return client.patch(
        review_endpoint(
            job_id,
            candidate_id,
        ),
        headers=headers,
        json={
            "status": status_value,
            "notes": notes,
        },
    )
def test_ranking_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/jobs/1/ranking"
        )
    assert response.status_code == 401
def test_ranking_includes_analyzed_and_unanalyzed_candidates(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    high_id, _ = create_candidate(
        tmp_path,
        job_id,
        "high",
        match_score=91,
    )
    medium_id, _ = create_candidate(
        tmp_path,
        job_id,
        "medium",
        match_score=72,
    )
    pending_id, _ = create_candidate(
        tmp_path,
        job_id,
        "pending",
        match_score=None,
    )
    with TestClient(app) as client:
        response = client.get(
            ranking_endpoint(job_id),
            headers=headers,
        )
    assert response.status_code == 200
    ranking = response.json()
    assert [
        item["candidate"]["id"]
        for item in ranking
    ] == [
        high_id,
        medium_id,
        pending_id,
    ]
    assert [
        item["rank"]
        for item in ranking
    ] == [
        1,
        2,
        None,
    ]
    assert (
        ranking[2][
            "analysis_status"
        ]
        == "not_analyzed"
    )
    assert (
        ranking[2][
            "review_status"
        ]
        == "not_reviewed"
    )
def test_ats_score_does_not_control_ranking(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    better_match_id, _ = (
        create_candidate(
            tmp_path,
            job_id,
            "better-match",
            match_score=82,
            ats_score=35,
        )
    )
    high_ats_id, _ = (
        create_candidate(
            tmp_path,
            job_id,
            "high-ats",
            match_score=58,
            ats_score=99,
        )
    )
    with TestClient(app) as client:
        response = client.get(
            ranking_endpoint(job_id),
            headers=headers,
        )
    ranking = response.json()
    assert (
        ranking[0]["candidate"]["id"]
        == better_match_id
    )
    assert (
        ranking[1]["candidate"]["id"]
        == high_ats_id
    )
    assert ranking[0]["ats_score"] == 35
    assert ranking[1]["ats_score"] == 99
def test_admin_can_save_and_read_hr_review(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path,
        job_id,
        "review",
        match_score=88,
    )
    with TestClient(app) as client:
        save_response = save_review(
            client,
            headers,
            job_id,
            candidate_id,
            "shortlisted",
            (
                "Strong evidence. Invite for "
                "the technical interview."
            ),
        )
        read_response = client.get(
            review_endpoint(
                job_id,
                candidate_id,
            ),
            headers=headers,
        )
        ranking_response = client.get(
            ranking_endpoint(job_id),
            headers=headers,
        )
    assert save_response.status_code == 200
    assert read_response.status_code == 200
    saved_review = save_response.json()
    assert (
        saved_review["status"]
        == "shortlisted"
    )
    assert (
        "technical interview"
        in saved_review["notes"]
    )
    ranking_item = (
        ranking_response.json()[0]
    )
    assert (
        ranking_item["review_status"]
        == "shortlisted"
    )
    assert (
        ranking_item["review"]["notes"]
        == saved_review["notes"]
    )
def test_review_update_reuses_existing_record(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path,
        job_id,
        "update-review",
        match_score=75,
    )
    with TestClient(app) as client:
        first_response = save_review(
            client,
            headers,
            job_id,
            candidate_id,
            "in_review",
            "Initial review.",
        )
        second_response = save_review(
            client,
            headers,
            job_id,
            candidate_id,
            "on_hold",
            "Waiting for verification.",
        )
    assert first_response.status_code == 200
    assert second_response.status_code == 200
    assert (
        first_response.json()["id"]
        == second_response.json()["id"]
    )
    with TestingSessionLocal() as database:
        review_count = database.scalar(
            select(
                func.count(
                    JobCandidateReview.id
                )
            )
        )
    assert review_count == 1
def test_invalid_review_status_is_rejected(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path,
        job_id,
        "invalid-status",
    )
    with TestClient(app) as client:
        response = save_review(
            client,
            headers,
            job_id,
            candidate_id,
            "automatically_hired",
            "This status must not exist.",
        )
    assert response.status_code == 422
def test_review_requires_job_assignment(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path,
        job_id,
        "unassigned",
        assigned=False,
    )
    with TestClient(app) as client:
        response = save_review(
            client,
            headers,
            job_id,
            candidate_id,
            "in_review",
        )
    assert response.status_code == 404
def test_review_status_does_not_change_ranking(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    high_id, _ = create_candidate(
        tmp_path,
        job_id,
        "high-not-selected",
        match_score=90,
    )
    low_id, _ = create_candidate(
        tmp_path,
        job_id,
        "low-shortlisted",
        match_score=60,
    )
    with TestClient(app) as client:
        save_review(
            client,
            headers,
            job_id,
            high_id,
            "not_selected",
        )
        save_review(
            client,
            headers,
            job_id,
            low_id,
            "shortlisted",
        )
        response = client.get(
            ranking_endpoint(job_id),
            headers=headers,
        )
    ranking = response.json()
    assert (
        ranking[0]["candidate"]["id"]
        == high_id
    )
    assert (
        ranking[1]["candidate"]["id"]
        == low_id
    )
def test_assignment_removal_deletes_review(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, _ = create_candidate(
        tmp_path,
        job_id,
        "remove-assignment",
        match_score=70,
    )
    with TestClient(app) as client:
        save_review(
            client,
            headers,
            job_id,
            candidate_id,
            "in_review",
        )
        remove_response = client.delete(
            (
                f"/api/jobs/{job_id}/"
                f"candidates/{candidate_id}"
            ),
            headers=headers,
        )
    assert remove_response.status_code == 204
    with TestingSessionLocal() as database:
        review_count = database.scalar(
            select(
                func.count(
                    JobCandidateReview.id
                )
            )
        )
    assert review_count == 0
def test_candidate_delete_removes_review(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, candidate_path = (
        create_candidate(
            tmp_path,
            job_id,
            "delete-candidate",
            match_score=80,
        )
    )
    with TestClient(app) as client:
        save_review(
            client,
            headers,
            job_id,
            candidate_id,
            "on_hold",
        )
        delete_response = client.delete(
            (
                f"/api/candidates/"
                f"{candidate_id}"
            ),
            headers=headers,
        )
    assert delete_response.status_code == 204
    assert not candidate_path.exists()
    with TestingSessionLocal() as database:
        review_count = database.scalar(
            select(
                func.count(
                    JobCandidateReview.id
                )
            )
        )
    assert review_count == 0
def test_job_delete_removes_reviews_and_preserves_candidate(
    tmp_path: Path,
):
    headers = create_admin_headers()
    job_id = create_job()
    candidate_id, candidate_path = (
        create_candidate(
            tmp_path,
            job_id,
            "delete-job",
            match_score=85,
        )
    )
    with TestClient(app) as client:
        save_review(
            client,
            headers,
            job_id,
            candidate_id,
            "shortlisted",
        )
        delete_response = client.delete(
            f"/api/jobs/{job_id}",
            headers=headers,
        )
    assert delete_response.status_code == 204
    assert candidate_path.exists()
    with TestingSessionLocal() as database:
        review_count = database.scalar(
            select(
                func.count(
                    JobCandidateReview.id
                )
            )
        )
        candidate = database.get(
            CandidateCV,
            candidate_id,
        )
    assert review_count == 0
    assert candidate is not None
