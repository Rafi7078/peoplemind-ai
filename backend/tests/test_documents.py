from collections.abc import Generator
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.db.database import Base, get_db
from backend.app.main import app
from backend.app.models.user import User
test_engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=test_engine,
    autoflush=False,
    expire_on_commit=False,
)
def override_get_db() -> Generator[Session, None, None]:
    database = TestingSessionLocal()
    try:
        yield database
    finally:
        database.close()
@pytest.fixture(autouse=True)
def prepare_test_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    monkeypatch.setattr(
        settings,
        "document_upload_dir",
        str(tmp_path / "uploads"),
    )
    yield
    app.dependency_overrides.pop(get_db, None)
def create_admin_authorization_header() -> dict[str, str]:
    email = "document-admin@example.com"
    with TestingSessionLocal() as database:
        admin = User(
            email=email,
            hashed_password="not-used-in-this-test",
            is_active=True,
            is_admin=True,
        )
        database.add(admin)
        database.commit()
    token = create_access_token(subject=email)
    return {
        "Authorization": f"Bearer {token}",
    }
def sample_pdf_bytes() -> bytes:
    return (
        b"%PDF-1.4\n"
        b"% PeopleMind AI test document\n"
        b"1 0 obj\n"
        b"<< /Type /Catalog >>\n"
        b"endobj\n"
        b"%%EOF"
    )
def test_document_upload_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/upload",
            files={
                "file": (
                    "policy.pdf",
                    sample_pdf_bytes(),
                    "application/pdf",
                )
            },
        )
    assert response.status_code == 401
def test_admin_can_upload_pdf() -> None:
    headers = create_admin_authorization_header()
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/upload",
            headers=headers,
            files={
                "file": (
                    "leave-policy.pdf",
                    sample_pdf_bytes(),
                    "application/pdf",
                )
            },
        )
    assert response.status_code == 201
    response_body = response.json()
    assert response_body["original_name"] == "leave-policy.pdf"
    assert response_body["status"] == "uploaded"
    assert response_body["page_count"] is None
    assert response_body["size_bytes"] > 0
def test_duplicate_pdf_is_rejected() -> None:
    headers = create_admin_authorization_header()
    upload = {
        "file": (
            "policy.pdf",
            sample_pdf_bytes(),
            "application/pdf",
        )
    }
    with TestClient(app) as client:
        first_response = client.post(
            "/api/documents/upload",
            headers=headers,
            files=upload,
        )
        second_response = client.post(
            "/api/documents/upload",
            headers=headers,
            files={
                "file": (
                    "same-policy.pdf",
                    sample_pdf_bytes(),
                    "application/pdf",
                )
            },
        )
    assert first_response.status_code == 201
    assert second_response.status_code == 409
def test_non_pdf_file_is_rejected() -> None:
    headers = create_admin_authorization_header()
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/upload",
            headers=headers,
            files={
                "file": (
                    "notes.txt",
                    b"Not a PDF",
                    "text/plain",
                )
            },
        )
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files are allowed."
