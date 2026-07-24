from collections.abc import Generator
from io import BytesIO
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
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
def blank_pdf_bytes(page_count: int = 2) -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    for _ in range(page_count):
        writer.add_blank_page(
            width=612,
            height=792,
        )
    writer.write(output)
    return output.getvalue()
def upload_pdf(
    client: TestClient,
    headers: dict[str, str],
    filename: str,
    content: bytes,
):
    return client.post(
        "/api/documents/upload",
        headers=headers,
        files={
            "file": (
                filename,
                content,
                "application/pdf",
            )
        },
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
        response = upload_pdf(
            client=client,
            headers=headers,
            filename="leave-policy.pdf",
            content=sample_pdf_bytes(),
        )
    assert response.status_code == 201
    response_body = response.json()
    assert response_body["original_name"] == "leave-policy.pdf"
    assert response_body["status"] == "uploaded"
    assert response_body["page_count"] is None
    assert response_body["size_bytes"] > 0
def test_duplicate_pdf_is_rejected() -> None:
    headers = create_admin_authorization_header()
    with TestClient(app) as client:
        first_response = upload_pdf(
            client=client,
            headers=headers,
            filename="policy.pdf",
            content=sample_pdf_bytes(),
        )
        second_response = upload_pdf(
            client=client,
            headers=headers,
            filename="same-policy.pdf",
            content=sample_pdf_bytes(),
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
    assert response.json()["detail"] == (
        "Only PDF files are allowed."
    )
def test_document_processing_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/1/process"
        )
    assert response.status_code == 401
def test_admin_can_process_blank_pdf() -> None:
    headers = create_admin_authorization_header()
    with TestClient(app) as client:
        upload_response = upload_pdf(
            client=client,
            headers=headers,
            filename="blank-policy.pdf",
            content=blank_pdf_bytes(page_count=2),
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]
        process_response = client.post(
            f"/api/documents/{document_id}/process",
            headers=headers,
        )
        pages_response = client.get(
            f"/api/documents/{document_id}/pages",
            headers=headers,
        )
    assert process_response.status_code == 200
    process_body = process_response.json()
    assert process_body["page_count"] == 2
    assert process_body["status"] == "needs_ocr"
    assert process_body["text_pages"] == 0
    assert process_body["total_characters"] == 0
    assert pages_response.status_code == 200
    assert len(pages_response.json()) == 2
def test_missing_document_processing_returns_404() -> None:
    headers = create_admin_authorization_header()
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/999/process",
            headers=headers,
        )
    assert response.status_code == 404
