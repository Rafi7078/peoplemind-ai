
from collections.abc import Generator
from io import BytesIO
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from pypdf import PdfWriter
from sqlalchemy import create_engine, select
from sqlalchemy.orm import (
    Session,
    sessionmaker,
)
from sqlalchemy.pool import StaticPool
from backend.app.core.config import settings
from backend.app.core.security import (
    create_access_token,
)
from backend.app.db.database import (
    Base,
    get_db,
)
from backend.app.main import app
from backend.app.models.candidate_cv import CandidateCV
from backend.app.models.file_blob import FileBlob
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
def prepare_candidate_environment(
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
    email = "candidate-admin@example.com"
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
def create_blank_pdf() -> bytes:
    output = BytesIO()
    writer = PdfWriter()
    writer.add_blank_page(
        width=612,
        height=792,
    )
    writer.write(output)
    return output.getvalue()
def upload_candidate(
    client: TestClient,
    headers: dict[str, str],
):
    return client.post(
        "/api/candidates/upload",
        headers=headers,
        files={
            "file": (
                "Candidate_QA_CV.pdf",
                create_blank_pdf(),
                "application/pdf",
            )
        },
    )
def test_candidate_upload_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            "/api/candidates/upload",
            files={
                "file": (
                    "Candidate.pdf",
                    create_blank_pdf(),
                    "application/pdf",
                )
            },
        )
    assert response.status_code == 401
def test_admin_can_upload_and_list_candidate_cv():
    headers = create_admin_headers()
    with TestClient(app) as client:
        upload_response = upload_candidate(
            client,
            headers,
        )
        list_response = client.get(
            "/api/candidates",
            headers=headers,
        )
    assert upload_response.status_code == 201
    assert list_response.status_code == 200
    assert (
        upload_response.json()[
            "original_name"
        ]
        == "Candidate_QA_CV.pdf"
    )
    assert len(
        list_response.json()
    ) == 1
def test_duplicate_candidate_cv_is_rejected():
    headers = create_admin_headers()
    with TestClient(app) as client:
        first_response = upload_candidate(
            client,
            headers,
        )
        duplicate_response = (
            upload_candidate(
                client,
                headers,
            )
        )
    assert first_response.status_code == 201
    assert (
        duplicate_response.status_code
        == 409
    )
def test_candidate_processing_requires_authentication():
    with TestClient(app) as client:
        response = client.post(
            "/api/candidates/1/process"
        )
    assert response.status_code == 401
def test_admin_can_process_blank_candidate_cv():
    headers = create_admin_headers()
    with TestClient(app) as client:
        upload_response = upload_candidate(
            client,
            headers,
        )
        candidate_id = (
            upload_response.json()["id"]
        )
        process_response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/process"
            ),
            headers=headers,
        )
        pages_response = client.get(
            (
                f"/api/candidates/"
                f"{candidate_id}/pages"
            ),
            headers=headers,
        )
    assert process_response.status_code == 200
    assert (
        process_response.json()["status"]
        == "needs_ocr"
    )
    assert (
        process_response.json()[
            "page_count"
        ]
        == 1
    )
    assert pages_response.status_code == 200
    assert len(
        pages_response.json()
    ) == 1
def test_missing_candidate_processing_returns_404():
    headers = create_admin_headers()
    with TestClient(app) as client:
        response = client.post(
            "/api/candidates/9999/process",
            headers=headers,
        )
    assert response.status_code == 404

def test_candidate_file_requires_authentication():
    with TestClient(app) as client:
        response = client.get(
            "/api/candidates/1/file"
        )
    assert response.status_code == 401
def test_admin_can_open_original_candidate_cv_inline():
    headers = create_admin_headers()
    with TestClient(app) as client:
        upload_response = upload_candidate(
            client,
            headers,
        )
        candidate_id = (
            upload_response.json()["id"]
        )
        file_response = client.get(
            (
                f"/api/candidates/"
                f"{candidate_id}/file"
            ),
            headers=headers,
        )
    assert file_response.status_code == 200
    assert (
        file_response.headers[
            "content-type"
        ]
        == "application/pdf"
    )
    assert file_response.headers[
        "content-disposition"
    ].startswith("inline;")
    assert file_response.content.startswith(
        b"%PDF-"
    )

def test_database_storage_restores_candidate_file(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "database",
    )
    headers = create_admin_headers()
    with TestClient(app) as client:
        upload_response = upload_candidate(
            client,
            headers,
        )
        assert upload_response.status_code == 201
        candidate_id = (
            upload_response.json()["id"]
        )
        with TestingSessionLocal() as database:
            candidate = database.get(
                CandidateCV,
                candidate_id,
            )
            assert candidate is not None
            candidate_path = Path(
                candidate.file_path
            )
            assert candidate_path.exists()
            blob = database.scalar(
                select(FileBlob).where(
                    FileBlob.storage_key
                    == (
                        "candidates/"
                        f"{candidate.stored_name}"
                    )
                )
            )
            assert blob is not None
            original_bytes = (
                candidate_path.read_bytes()
            )
            assert (
                blob.content
                == original_bytes
            )
            candidate_path.unlink()
        file_response = client.get(
            (
                f"/api/candidates/"
                f"{candidate_id}/file"
            ),
            headers=headers,
        )
    assert file_response.status_code == 200
    assert file_response.content == original_bytes
def test_database_storage_restores_candidate_before_processing(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "database",
    )
    headers = create_admin_headers()
    with TestClient(app) as client:
        upload_response = upload_candidate(
            client,
            headers,
        )
        assert upload_response.status_code == 201
        candidate_id = (
            upload_response.json()["id"]
        )
        with TestingSessionLocal() as database:
            candidate = database.get(
                CandidateCV,
                candidate_id,
            )
            assert candidate is not None
            Path(
                candidate.file_path
            ).unlink()
        process_response = client.post(
            (
                f"/api/candidates/"
                f"{candidate_id}/process"
            ),
            headers=headers,
        )
    assert process_response.status_code == 200
    assert (
        process_response.json()["page_count"]
        == 1
    )
def test_database_storage_delete_removes_candidate_blob(
    monkeypatch: pytest.MonkeyPatch,
):
    monkeypatch.setattr(
        settings,
        "file_storage_backend",
        "database",
    )
    headers = create_admin_headers()
    with TestClient(app) as client:
        upload_response = upload_candidate(
            client,
            headers,
        )
        assert upload_response.status_code == 201
        candidate_id = (
            upload_response.json()["id"]
        )
        with TestingSessionLocal() as database:
            blob = database.scalar(
                select(FileBlob)
            )
            assert blob is not None
        delete_response = client.delete(
            (
                f"/api/candidates/"
                f"{candidate_id}"
            ),
            headers=headers,
        )
        assert delete_response.status_code == 204
        with TestingSessionLocal() as database:
            remaining_blob = database.scalar(
                select(FileBlob)
            )
            assert remaining_blob is None
