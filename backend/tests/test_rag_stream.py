import json
import pytest
from fastapi.testclient import TestClient
import backend.app.services.rag_stream_service as stream_service
from backend.app.main import app
def parse_events(
    chunks: list[str],
) -> list[dict]:
    events: list[dict] = []
    for chunk in chunks:
        for line in chunk.splitlines():
            if line.strip():
                events.append(
                    json.loads(line)
                )
    return events
def test_stream_endpoint_requires_authentication() -> None:
    with TestClient(app) as client:
        response = client.post(
            "/api/documents/ask/stream",
            json={
                "question": "Hello",
                "document_id": None,
                "top_k": 5,
            },
        )
    assert response.status_code == 401
def test_stream_greeting_returns_final_event(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    def fail_search(**kwargs):
        raise AssertionError(
            "Greeting must not run policy search."
        )
    monkeypatch.setattr(
        stream_service,
        "search_document_chunks",
        fail_search,
    )
    events = parse_events(
        list(
            stream_service.stream_document_answer(
                question="Hello",
                document_id=None,
                top_k=5,
            )
        )
    )
    assert len(events) == 1
    assert events[0]["event"] == "final"
    assert (
        events[0]["data"]["response_type"]
        == "conversation"
    )
def test_stream_policy_answer_and_final_citations(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        stream_service,
        "search_document_chunks",
        lambda **kwargs: [
            {
                "vector_id": "stream-vector-1",
                "document_id": 7,
                "document_name": (
                    "Maternity Leave Policy "
                    "- Bangladesh - Jul 2026.pdf"
                ),
                "page_number": 1,
                "chunk_index": 0,
                "distance": 0.10,
                "text": (
                    "Eligible employees receive "
                    "16 weeks of maternity leave."
                ),
            }
        ],
    )
    monkeypatch.setattr(
        stream_service,
        "stream_grounded_answer_text",
        lambda **kwargs: iter(
            [
                "Eligible employees receive ",
                "16 weeks of maternity leave ",
                "[S1].",
            ]
        ),
    )
    events = parse_events(
        list(
            stream_service.stream_document_answer(
                question=(
                    "How much maternity leave "
                    "is available?"
                ),
                document_id=None,
                top_k=5,
            )
        )
    )
    deltas = [
        event["text"]
        for event in events
        if event["event"] == "delta"
    ]
    final_event = next(
        event
        for event in events
        if event["event"] == "final"
    )
    assert "".join(deltas).endswith(
        "[S1]."
    )
    assert (
        final_event["data"]["response_type"]
        == "policy_guidance"
    )
    assert len(
        final_event["data"]["citations"]
    ) == 1
def test_stream_without_evidence_returns_fallback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        stream_service,
        "search_document_chunks",
        lambda **kwargs: [],
    )
    events = parse_events(
        list(
            stream_service.stream_document_answer(
                question=(
                    "Does the company provide "
                    "dental insurance?"
                ),
                document_id=None,
                top_k=5,
            )
        )
    )
    final_event = next(
        event
        for event in events
        if event["event"] == "final"
    )
    assert (
        final_event["data"]["response_type"]
        == "no_supporting_policy"
    )
    assert (
        final_event["data"]["citations"]
        == []
    )
