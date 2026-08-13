from collections.abc import Generator
from pathlib import Path
import chromadb
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
import backend.app.services.document_service as document_service
from backend.app.core.config import settings
from backend.app.core.security import create_access_token
from backend.app.db.database import Base, get_db
from backend.app.main import app
from backend.app.models.document import Document
from backend.app.models.document_chunk import DocumentChunk
from backend.app.models.document_page import DocumentPage
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
@pytest.fixture
def management_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
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
    chroma_client = (
        chromadb.EphemeralClient()
    )
    collection = (
        chroma_client
        .get_or_create_collection(
            name=(
                "peoplemind_document_"
                "management_test"
            ),
        )
    )
    monkeypatch.setattr(
        document_service,
        "get_vector_collection",
        lambda: collection,
    )
    monkeypatch.setattr(
        document_service.settings,
        "document_upload_dir",
        str(tmp_path),
    )
    yield tmp_path, collection
    app.dependency_overrides.pop(
        get_db,
        None,
    )
def create_indexed_document(
    upload_directory: Path,
    collection,
) -> tuple[
    dict[str, str],
    int,
    Path,
    str,
]:
    email = "management-admin@example.com"
    document_path = (
        upload_directory
        / "stored-policy.pdf"
    )
    document_path.write_bytes(
        b"%PDF-1.4\nPeopleMind test PDF"
    )
    vector_id = (
        "document-1-page-1-chunk-1"
    )
    with TestingSessionLocal() as database:
        admin = User(
            email=email,
            hashed_password="not-used",
            is_active=True,
            is_admin=True,
        )
        database.add(admin)
        database.flush()
        document = Document(
            original_name=(
                "Policy.pdf.pdf"
            ),
            stored_name=(
                "stored-policy.pdf"
            ),
            file_path=str(
                document_path
            ),
            sha256="d" * 64,
            size_bytes=(
                document_path.stat().st_size
            ),
            mime_type="application/pdf",
            status="indexed",
            page_count=1,
            uploaded_by_id=admin.id,
        )
        database.add(document)
        database.flush()
        database.add(
            DocumentPage(
                document_id=document.id,
                page_number=1,
                text="Employees must follow the policy.",
                char_count=33,
            )
        )
        vector_id = (
            f"document-{document.id}"
            "-page-1-chunk-1"
        )
        database.add(
            DocumentChunk(
                document_id=document.id,
                page_number=1,
                chunk_index=1,
                vector_id=vector_id,
                text=(
                    "Employees must follow "
                    "the policy."
                ),
                char_count=33,
            )
        )
        document_id = document.id
        database.commit()
    collection.upsert(
        ids=[vector_id],
        embeddings=[
            [1.0, 0.0, 0.0]
        ],
        documents=[
            "Employees must follow the policy."
        ],
        metadatas=[
            {
                "document_id": document_id,
                "document_name": (
                    "Policy.pdf.pdf"
                ),
                "page_number": 1,
                "chunk_index": 1,
            }
        ],
    )
    token = create_access_token(
        subject=email
    )
    return (
        {
            "Authorization": (
                f"Bearer {token}"
            )
        },
        document_id,
        document_path,
        vector_id,
    )
def test_rename_requires_authentication(
    management_environment,
) -> None:
    with TestClient(app) as client:
        response = client.patch(
            "/api/documents/1",
            json={
                "original_name": (
                    "Policy.pdf"
                )
            },
        )
    assert response.status_code == 401
def test_delete_requires_authentication(
    management_environment,
) -> None:
    with TestClient(app) as client:
        response = client.delete(
            "/api/documents/1"
        )
    assert response.status_code == 401
def test_admin_can_rename_document_and_vectors(
    management_environment,
) -> None:
    upload_directory, collection = (
        management_environment
    )
    (
        headers,
        document_id,
        document_path,
        vector_id,
    ) = create_indexed_document(
        upload_directory,
        collection,
    )
    with TestClient(app) as client:
        response = client.patch(
            f"/api/documents/{document_id}",
            headers=headers,
            json={
                "original_name": (
                    "Whistleblowing Policy "
                    "- Dec 2025.pdf"
                )
            },
        )
    assert response.status_code == 200
    body = response.json()
    assert body["original_name"] == (
        "Whistleblowing Policy "
        "- Dec 2025.pdf"
    )
    assert document_path.exists()
    with TestingSessionLocal() as database:
        document = database.get(
            Document,
            document_id,
        )
        assert document is not None
        assert document.original_name == (
            "Whistleblowing Policy "
            "- Dec 2025.pdf"
        )
        assert document.stored_name == (
            "stored-policy.pdf"
        )
    vector_record = collection.get(
        ids=[vector_id],
        include=["metadatas"],
    )
    metadata = (
        vector_record["metadatas"][0]
    )
    assert metadata["document_name"] == (
        "Whistleblowing Policy "
        "- Dec 2025.pdf"
    )
def test_repeated_pdf_extension_is_rejected(
    management_environment,
) -> None:
    upload_directory, collection = (
        management_environment
    )
    (
        headers,
        document_id,
        _,
        _,
    ) = create_indexed_document(
        upload_directory,
        collection,
    )
    with TestClient(app) as client:
        response = client.patch(
            f"/api/documents/{document_id}",
            headers=headers,
            json={
                "original_name": (
                    "Policy.pdf.pdf"
                )
            },
        )
    assert response.status_code == 422
def test_admin_can_delete_document_and_all_data(
    management_environment,
) -> None:
    upload_directory, collection = (
        management_environment
    )
    (
        headers,
        document_id,
        document_path,
        _,
    ) = create_indexed_document(
        upload_directory,
        collection,
    )
    with TestClient(app) as client:
        response = client.delete(
            f"/api/documents/{document_id}",
            headers=headers,
        )
    assert response.status_code == 200
    body = response.json()
    assert body == {
        "document_id": document_id,
        "deleted": True,
        "file_deleted": True,
    }
    assert not document_path.exists()
    assert collection.count() == 0
    with TestingSessionLocal() as database:
        assert database.get(
            Document,
            document_id,
        ) is None
        pages = list(
            database.scalars(
                select(DocumentPage).where(
                    DocumentPage.document_id
                    == document_id
                )
            ).all()
        )
        chunks = list(
            database.scalars(
                select(DocumentChunk).where(
                    DocumentChunk.document_id
                    == document_id
                )
            ).all()
        )
        assert pages == []
        assert chunks == []
def test_missing_document_management_returns_404(
    management_environment,
) -> None:
    upload_directory, collection = (
        management_environment
    )
    (
        headers,
        _,
        _,
        _,
    ) = create_indexed_document(
        upload_directory,
        collection,
    )
    with TestClient(app) as client:
        rename_response = client.patch(
            "/api/documents/9999",
            headers=headers,
            json={
                "original_name": (
                    "Missing Policy.pdf"
                )
            },
        )
        delete_response = client.delete(
            "/api/documents/9999",
            headers=headers,
        )
    assert rename_response.status_code == 404
    assert delete_response.status_code == 404

def test_pgvector_rename_does_not_use_chroma(
    management_environment,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload_directory, collection = (
        management_environment
    )
    (
        headers,
        document_id,
        _,
        _,
    ) = create_indexed_document(
        upload_directory,
        collection,
    )
    monkeypatch.setattr(
        settings,
        "vector_backend",
        "pgvector",
    )
    monkeypatch.setattr(
        document_service,
        "get_vector_collection",
        lambda: (
            (_ for _ in ()).throw(
                AssertionError(
                    "Chroma must not be used "
                    "for pgvector rename."
                )
            )
        ),
    )
    with TestClient(app) as client:
        response = client.patch(
            f"/api/documents/{document_id}",
            headers=headers,
            json={
                "original_name": (
                    "Renamed PGVector Policy.pdf"
                )
            },
        )
    assert response.status_code == 200
    assert (
        response.json()["original_name"]
        == "Renamed PGVector Policy.pdf"
    )
    with TestingSessionLocal() as database:
        document = database.get(
            Document,
            document_id,
        )
        assert document is not None
        assert (
            document.original_name
            == "Renamed PGVector Policy.pdf"
        )
def test_pgvector_delete_does_not_use_chroma(
    management_environment,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    upload_directory, collection = (
        management_environment
    )
    (
        headers,
        document_id,
        document_path,
        _,
    ) = create_indexed_document(
        upload_directory,
        collection,
    )
    monkeypatch.setattr(
        settings,
        "vector_backend",
        "pgvector",
    )
    monkeypatch.setattr(
        document_service,
        "get_vector_collection",
        lambda: (
            (_ for _ in ()).throw(
                AssertionError(
                    "Chroma must not be used "
                    "for pgvector delete."
                )
            )
        ),
    )
    delete_calls: list[int] = []
    monkeypatch.setattr(
        document_service,
        "delete_document_embeddings",
        lambda database, *, document_id: (
            delete_calls.append(
                document_id
            )
        ),
    )
    with TestClient(app) as client:
        response = client.delete(
            f"/api/documents/{document_id}",
            headers=headers,
        )
    assert response.status_code == 200
    assert delete_calls == [
        document_id
    ]
    assert not document_path.exists()
    with TestingSessionLocal() as database:
        assert database.get(
            Document,
            document_id,
        ) is None
        chunks = list(
            database.scalars(
                select(DocumentChunk).where(
                    DocumentChunk.document_id
                    == document_id
                )
            ).all()
        )
        pages = list(
            database.scalars(
                select(DocumentPage).where(
                    DocumentPage.document_id
                    == document_id
                )
            ).all()
        )
        assert chunks == []
        assert pages == []
