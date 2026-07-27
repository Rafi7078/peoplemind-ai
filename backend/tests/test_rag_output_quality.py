import json
import backend.app.services.rag_stream_service as stream_service
from backend.app.services.rag_answer_service import (
    build_evidence_context,
    sanitize_policy_answer,
)
def sample_search_results():
    return [
        {
            "vector_id": (
                "document-12-page-1-chunk-1"
            ),
            "document_id": 12,
            "document_name": (
                "Holiday Policy - Jul 2025.pdf"
            ),
            "page_number": 1,
            "chunk_index": 1,
            "distance": 0.1,
            "text": (
                "Holiday requires manager approval."
            ),
        },
        {
            "vector_id": (
                "document-12-page-1-chunk-2"
            ),
            "document_id": 12,
            "document_name": (
                "Holiday Policy - Jul 2025.pdf"
            ),
            "page_number": 1,
            "chunk_index": 2,
            "distance": 0.2,
            "text": (
                "Holiday must be recorded "
                "in the tracking system."
            ),
        },
    ]
def test_policy_answer_sanitizer_removes_sentinel():
    answer = (
        "Holiday requires approval [S1].\n\n"
        "NO_SUPPORTING_POLICY"
    )
    assert sanitize_policy_answer(
        answer
    ) == (
        "Holiday requires approval [S1]."
    )
def test_evidence_context_merges_same_page_chunks():
    context, source_map = (
        build_evidence_context(
            sample_search_results()
        )
    )
    assert list(source_map) == ["S1"]
    assert (
        source_map["S1"]["chunk_indices"]
        == [1, 2]
    )
    assert (
        "Holiday requires manager approval."
        in context
    )
    assert (
        "Holiday must be recorded"
        in context
    )
def test_stream_hides_sentinel_and_deduplicates_citation(
    monkeypatch,
):
    monkeypatch.setattr(
        stream_service,
        "search_document_chunks",
        lambda **_: sample_search_results(),
    )
    monkeypatch.setattr(
        stream_service,
        "stream_grounded_answer_text",
        lambda **_: iter(
            [
                (
                    "Holiday requires manager "
                    "approval [S1].\n\n"
                ),
                "NO_SUPPORTING_",
                "POLICY",
            ]
        ),
    )
    events = [
        json.loads(event_line)
        for event_line in (
            stream_service
            .stream_document_answer(
                question=(
                    "Summarize the Holiday Policy."
                ),
                document_id=12,
                top_k=5,
            )
        )
    ]
    visible_text = "".join(
        event["text"]
        for event in events
        if event["event"] == "delta"
    )
    assert (
        "NO_SUPPORTING_POLICY"
        not in visible_text
    )
    final_event = next(
        event
        for event in events
        if event["event"] == "final"
    )
    final_data = final_event["data"]
    assert final_data["answer"] == (
        "Holiday requires manager approval [S1]."
    )
    assert len(
        final_data["citations"]
    ) == 1
    assert (
        final_data["citations"][0][
            "page_number"
        ]
        == 1
    )
def test_policy_answer_sanitizer_removes_source_appendix():
    answer = (
        "Holiday requires manager approval [S1].\n\n"
        "[Supporting sources: S1]"
    )
    assert sanitize_policy_answer(
        answer
    ) == (
        "Holiday requires manager approval [S1]."
    )

