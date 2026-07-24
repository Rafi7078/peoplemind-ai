from collections.abc import Generator
from pathlib import Path
import chromadb
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
import backend.app.services.document_index_service as index_service
from backend.app.core.security import create_access_token
from backend.app.db.database import Base, get_db
from backend.app.main import app
from backend.app.models.document import Document
from backend.app.models.document_page import DocumentPage
from backend.app.models.user import User
from backend.app.services.chunking_service import (
    split_text_into_chunks,
)
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
def prepare_index_environment(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    chroma_client = chromadb.EphemeralClient()
    collection = chroma_client.get_or_create_collection(
        name="peoplemind_test_index",
    )
    monkeypatch.setattr(
        index_service,
        "get_vector_collection",
        lambda: collection,
    )
    monkeypatch.setattr(
        index_service,
        "embed_texts",
        lambda texts: [
            [1.0, 0.0, 0.0]
            for _ in texts
        ],
    )
    yield
    app.dependency_overrides.pop(get_db, None)
def create_ready_document() -> tuple[
    dict[str, str],
    int,
]:
    email = "index-admin@example.com"
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
            original_name="hr-policy.pdf",
            stored_name="hr-policy-stored.pdf",
            file_path="unused-in-index-test.pdf",
            sha256="b" * 64,
            size_bytes=500,
            mime_type="application/pdf",
            status="ready",
            page_count=1,
            uploaded_by_id=admin.id,
        )
        database.add(document)
        database.flush()
        text = (
            "Employees receive ten days of casual leave "
            "each calendar year. Sick leave requires a "
            "medical certificate when the absence exceeds "
            "two consecutive working days. "
        ) * 12
        database.add(
            DocumentPage(
                document_id=document.id,
                page_number=1,
                text=text,
                char_count=len(text),
            )
        )
        document_id = document.id
        database.commit()
    token = create_access_token(subject=email)
    return (
        {"Authorization": f"Bearer {token}"},
        document_id,
    )
def test_indexing_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/1/index"
        )
    assert response.status_code == 401
def test_chunking_respects_requested_size() -> None:
    text = "PeopleMind HR policy text " * 100
    chunks = split_text_into_chunks(
        text=text,
        chunk_size=300,
        overlap=50,
    )
    assert len(chunks) > 1
    assert all(len(chunk) <= 300 for chunk in chunks)
def test_admin_can_index_and_search_document() -> None:
    headers, document_id = create_ready_document()
    with TestClient(app) as client:
        index_response = client.post(
            f"/api/documents/{document_id}/index",
            headers=headers,
        )
        chunks_response = client.get(
            f"/api/documents/{document_id}/chunks",
            headers=headers,
        )
        search_response = client.post(
            "/api/documents/search",
            headers=headers,
            json={
                "query": "How many casual leave days?",
                "document_id": document_id,
                "top_k": 3,
            },
        )
    assert index_response.status_code == 200
    index_body = index_response.json()
    assert index_body["status"] == "indexed"
    assert index_body["chunk_count"] > 0
    assert index_body["vector_dimension"] == 3
    assert chunks_response.status_code == 200
    assert len(chunks_response.json()) > 0
    assert search_response.status_code == 200
    assert len(search_response.json()) > 0
    assert search_response.json()[0]["document_id"] == document_id
    assert search_response.json()[0]["page_number"] == 1
