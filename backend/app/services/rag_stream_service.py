import json
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from backend.app.core.config import settings
from backend.app.services.conversation_router_service import (
    get_conversation_reply,
)
from backend.app.services.document_index_service import (
    DocumentSearchError,
    search_document_chunks,
)
from backend.app.services.ollama_chat_service import (
    ChatServiceError,
    NO_SUPPORTING_POLICY_SENTINEL,
    stream_grounded_answer_text,
)
from backend.app.services.rag_answer_service import (
    build_evidence_context,
    collect_valid_source_ids,
    conversation_response,
    fallback_response,
)
def stream_event(
    event: str,
    **payload: Any,
) -> str:
    return (
        json.dumps(
            {
                "event": event,
                **payload,
            },
            ensure_ascii=False,
        )
        + "\n"
    )
def build_citations(
    valid_source_ids: list[str],
    source_map: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    citations: list[dict[str, Any]] = []
    for source_id in valid_source_ids:
        source = source_map[source_id]
        citations.append(
            {
                "source_id": source_id,
                "document_id": (
                    source["document_id"]
                ),
                "document_name": (
                    source["document_name"]
                ),
                "page_number": (
                    source["page_number"]
                ),
                "chunk_index": (
                    source["chunk_index"]
                ),
                "text_preview": (
                    source["text"][:300]
                ),
            }
        )
    return citations
def stream_document_answer(
    question: str,
    document_id: int | None,
    top_k: int,
) -> Iterator[str]:
    normalized_question = question.strip()
    conversation_reply = get_conversation_reply(
        normalized_question
    )
    if conversation_reply is not None:
        yield stream_event(
            "final",
            data=conversation_response(
                question=normalized_question,
                answer=conversation_reply.answer,
            ),
        )
        return
    yield stream_event(
        "status",
        stage="searching",
        message="Searching company policies...",
    )
    try:
        search_results = search_document_chunks(
            query=normalized_question,
            document_id=document_id,
            top_k=top_k,
        )
    except DocumentSearchError:
        yield stream_event(
            "error",
            message=(
                "Company policy search is currently "
                "unavailable."
            ),
        )
        return
    evidence_context, source_map = (
        build_evidence_context(
            search_results
        )
    )
    if not source_map:
        yield stream_event(
            "final",
            data=fallback_response(
                question=normalized_question,
                retrieved_chunks=len(
                    search_results
                ),
            ),
        )
        return
    yield stream_event(
        "status",
        stage="generating",
        message="Generating policy guidance...",
    )
    answer_parts: list[str] = []
    pending_text = ""
    visible_stream_started = False
    try:
        for text_delta in (
            stream_grounded_answer_text(
                question=normalized_question,
                evidence_context=evidence_context,
            )
        ):
            answer_parts.append(text_delta)
            if visible_stream_started:
                yield stream_event(
                    "delta",
                    text=text_delta,
                )
                continue
            pending_text += text_delta
            normalized_pending = (
                pending_text.strip()
            )
            if not normalized_pending:
                continue
            sentinel_prefix = (
                NO_SUPPORTING_POLICY_SENTINEL
                .casefold()
                .startswith(
                    normalized_pending.casefold()
                )
            )
            if (
                sentinel_prefix
                and len(normalized_pending)
                <= len(
                    NO_SUPPORTING_POLICY_SENTINEL
                )
            ):
                continue
            visible_stream_started = True
            yield stream_event(
                "delta",
                text=pending_text,
            )
    except ChatServiceError:
        yield stream_event(
            "error",
            message=(
                "The local AI could not complete "
                "the streaming response."
            ),
        )
        return
    final_answer = "".join(
        answer_parts
    ).strip()
    if (
        not final_answer
        or final_answer.casefold()
        == NO_SUPPORTING_POLICY_SENTINEL.casefold()
    ):
        yield stream_event(
            "final",
            data=fallback_response(
                question=normalized_question,
                retrieved_chunks=len(
                    source_map
                ),
            ),
        )
        return
    model_output = SimpleNamespace(
        answer=final_answer,
        used_source_ids=[],
    )
    valid_source_ids = collect_valid_source_ids(
        model_output=model_output,
        source_map=source_map,
    )
    if not valid_source_ids:
        yield stream_event(
            "final",
            data=fallback_response(
                question=normalized_question,
                retrieved_chunks=len(
                    source_map
                ),
            ),
        )
        return
    result = {
        "question": normalized_question,
        "answer": final_answer,
        "answer_found": True,
        "response_type": "policy_guidance",
        "citations": build_citations(
            valid_source_ids=valid_source_ids,
            source_map=source_map,
        ),
        "retrieved_chunks": len(
            source_map
        ),
        "model": settings.ollama_chat_model,
    }
    yield stream_event(
        "final",
        data=result,
    )
