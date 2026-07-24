import pytest
import backend.app.services.rag_answer_service as rag_service
from backend.app.services.ollama_chat_service import (
    GroundedModelOutput,
)
def test_recovers_source_id_from_answer_text(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        rag_service,
        "search_document_chunks",
        lambda **kwargs: [
            {
                "vector_id": "document-2-page-3-chunk-1",
                "document_id": 2,
                "document_name": (
                    "PeopleMind_Sample_HR_Policy.pdf"
                ),
                "page_number": 3,
                "chunk_index": 1,
                "distance": 0.68,
                "text": (
                    "Employees receive 10 days of casual "
                    "leave per calendar year."
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
                "An employee receives 10 days of casual "
                "leave each year [S1]."
            ),
            used_source_ids=[],
        ),
    )
    result = rag_service.answer_document_question(
        question=(
            "How many casual leave days does an "
            "employee receive each year?"
        ),
        document_id=2,
        top_k=5,
    )
    assert result["answer_found"] is True
    assert len(result["citations"]) == 1
    assert result["citations"][0]["source_id"] == "S1"
    assert result["citations"][0]["page_number"] == 3
