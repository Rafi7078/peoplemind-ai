from collections.abc import Generator
from io import BytesIO
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.db.database import Base, get_db
from backend.app.main import app
from backend.app.models.document import Document
from backend.app.models.file_blob import FileBlob
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

def test_admin_can_open_original_pdf_inline() -> None:
    headers = create_admin_authorization_header()
    pdf_content = blank_pdf_bytes(
        page_count=1
    )
    with TestClient(app) as client:
        upload_response = upload_pdf(
            client=client,
            headers=headers,
            filename=(
                "Maternity Leave Policy "
                "- Bangladesh - Jul 2026.pdf"
            ),
            content=pdf_content,
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]
        file_response = client.get(
            f"/api/documents/{document_id}/file",
            headers=headers,
        )
    assert file_response.status_code == 200
    assert (
        file_response.headers["content-type"]
        == "application/pdf"
    )
    assert file_response.content == pdf_content
    content_disposition = file_response.headers[
        "content-disposition"
    ]
    assert content_disposition.startswith(
        "inline;"
    )
    assert (
        "Maternity%20Leave%20Policy%20"
        "-%20Bangladesh%20-%20Jul%202026.pdf"
        in content_disposition
    )
    assert (
        file_response.headers["cache-control"]
        == "private, no-store, max-age=0"
    )

def test_database_storage_restores_document_file(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "database",
    )
    headers = create_admin_authorization_header()
    pdf_content = blank_pdf_bytes(
        page_count=1
    )
    with TestClient(app) as client:
        upload_response = upload_pdf(
            client=client,
            headers=headers,
            filename="database-policy.pdf",
            content=pdf_content,
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]
        with TestingSessionLocal() as database:
            document = database.get(
                Document,
                document_id,
            )
            assert document is not None
            document_path = Path(
                document.file_path
            )
            assert document_path.exists()
            blob = database.scalar(
                select(FileBlob).where(
                    FileBlob.storage_key
                    == (
                        "documents/"
                        f"{document.stored_name}"
                    )
                )
            )
            assert blob is not None
            assert blob.content == pdf_content
            document_path.unlink()
        file_response = client.get(
            f"/api/documents/{document_id}/file",
            headers=headers,
        )
    assert file_response.status_code == 200
    assert file_response.content == pdf_content
def test_database_storage_restores_before_processing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "database",
    )
    headers = create_admin_authorization_header()
    with TestClient(app) as client:
        upload_response = upload_pdf(
            client=client,
            headers=headers,
            filename="restore-process.pdf",
            content=blank_pdf_bytes(
                page_count=1
            ),
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]
        with TestingSessionLocal() as database:
            document = database.get(
                Document,
                document_id,
            )
            assert document is not None
            Path(
                document.file_path
            ).unlink()
        process_response = client.post(
            f"/api/documents/{document_id}/process",
            headers=headers,
        )
    assert process_response.status_code == 200
    assert (
        process_response.json()["page_count"]
        == 1
    )
def test_database_storage_delete_removes_blob(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "database",
    )
    headers = create_admin_authorization_header()
    with TestClient(app) as client:
        upload_response = upload_pdf(
            client=client,
            headers=headers,
            filename="delete-database.pdf",
            content=blank_pdf_bytes(
                page_count=1
            ),
        )
        assert upload_response.status_code == 201
        document_id = upload_response.json()["id"]
        with TestingSessionLocal() as database:
            blob = database.scalar(
                select(FileBlob)
            )
            assert blob is not None
        delete_response = client.delete(
            f"/api/documents/{document_id}",
            headers=headers,
        )
        assert delete_response.status_code == 200
        with TestingSessionLocal() as database:
            remaining_blob = database.scalar(
                select(FileBlob)
            )
            assert remaining_blob is None
