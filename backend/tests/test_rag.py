from collections.abc import Generator
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool
import backend.app.api.routes.documents as document_routes
import backend.app.services.rag_answer_service as rag_service
from backend.app.core.security import create_access_token
from backend.app.db.database import Base, get_db
from backend.app.main import app
from backend.app.models.user import User
from backend.app.services.ollama_chat_service import (
    GroundedModelOutput,
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
def prepare_rag_environment() -> Generator[None, None, None]:
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.pop(get_db, None)
def create_authorization_header() -> dict[str, str]:
    email = "rag-admin@example.com"
    with TestingSessionLocal() as database:
        database.add(
            User(
                email=email,
                hashed_password="not-used",
                is_active=True,
                is_admin=True,
            )
        )
        database.commit()
    token = create_access_token(subject=email)
    return {
        "Authorization": f"Bearer {token}",
    }
def test_ask_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/ask",
            json={
                "question": "What is the leave policy?",
                "document_id": 1,
                "top_k": 5,
            },
        )
    assert response.status_code == 401
def test_rag_returns_fallback_without_evidence(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rag_service,
        "search_document_chunks",
        lambda **kwargs: [],
    )
    result = rag_service.answer_document_question(
        question="What is the leave policy?",
        document_id=1,
        top_k=5,
    )
    assert result["answer_found"] is False
    assert result["citations"] == []
    assert result["answer"] == rag_service.FALLBACK_ANSWER
def test_rag_maps_model_sources_to_citations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rag_service,
        "search_document_chunks",
        lambda **kwargs: [
            {
                "vector_id": "vector-1",
                "document_id": 1,
                "document_name": "hr-policy.pdf",
                "page_number": 3,
                "chunk_index": 1,
                "distance": 0.25,
                "text": (
                    "Employees receive ten casual leave "
                    "days each year."
                ),
            }
        ],
    )
    monkeypatch.setattr(
        rag_service,
        "generate_grounded_answer",
        lambda **kwargs: GroundedModelOutput(
            answerable=True,
            answer=(
                "Employees receive ten casual leave "
                "days each year [S1]."
            ),
            used_source_ids=["S1"],
        ),
    )
    result = rag_service.answer_document_question(
        question="How many casual leave days are provided?",
        document_id=1,
        top_k=5,
    )
    assert result["answer_found"] is True
    assert len(result["citations"]) == 1
    assert result["citations"][0]["page_number"] == 3
def test_admin_can_call_ask_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    headers = create_authorization_header()
    monkeypatch.setattr(
        document_routes.rag_answer_service,
        "answer_document_question",
        lambda **kwargs: {
            "question": kwargs["question"],
            "answer": "The website was deployed on Vercel [S1].",
            "answer_found": True,
            "citations": [
                {
                    "source_id": "S1",
                    "document_id": 1,
                    "document_name": "portfolio.pdf",
                    "page_number": 2,
                    "chunk_index": 2,
                    "text_preview": "Vercel deployment details.",
                }
            ],
            "retrieved_chunks": 1,
            "model": "qwen3:4b-instruct",
        },
    )
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/ask",
            headers=headers,
            json={
                "question": "Where was the website deployed?",
                "document_id": 1,
                "top_k": 5,
            },
        )
    assert response.status_code == 200
    assert response.json()["answer_found"] is True
    assert response.json()["citations"][0]["page_number"] == 2
