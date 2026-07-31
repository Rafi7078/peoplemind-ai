
from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
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
from backend.app.models.user import User
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
def prepare_job_environment() -> (
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
    email = "job-admin@example.com"
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
def valid_job_payload() -> dict:
    return {
        "title": "Software QA Engineer",
        "department": "Engineering",
        "location": "Dhaka",
        "employment_type": "Full-time",
        "description": (
            "We are looking for a QA Engineer "
            "with manual testing, API testing, "
            "SQL and defect-management experience."
        ),
        "status": "active",
    }
def test_create_job_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            "/api/jobs",
            json=valid_job_payload(),
        )
    assert response.status_code == 401
def test_admin_can_create_list_and_read_job():
    headers = create_admin_headers()
    with TestClient(app) as client:
        create_response = client.post(
            "/api/jobs",
            headers=headers,
            json=valid_job_payload(),
        )
        list_response = client.get(
            "/api/jobs",
            headers=headers,
        )
        job_id = create_response.json()[
            "id"
        ]
        read_response = client.get(
            f"/api/jobs/{job_id}",
            headers=headers,
        )
    assert create_response.status_code == 201
    assert list_response.status_code == 200
    assert read_response.status_code == 200
    assert (
        create_response.json()["title"]
        == "Software QA Engineer"
    )
    assert len(
        list_response.json()
    ) == 1
def test_missing_job_returns_404():
    headers = create_admin_headers()
    with TestClient(app) as client:
        response = client.get(
            "/api/jobs/9999",
            headers=headers,
        )
    assert response.status_code == 404
