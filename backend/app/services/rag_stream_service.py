import json
from collections.abc import Iterator
from types import SimpleNamespace
from typing import Any
from sqlalchemy.orm import Session
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
    build_citations,
    build_evidence_context,
    collect_valid_source_ids,
    conversation_response,
    fallback_response,
    remove_policy_sentinel,
    sanitize_policy_answer,
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
def stream_document_answer(
    question: str,
    document_id: int | None,
    top_k: int,
    database: Session | None = None,
) -> Iterator[str]:
    normalized_question = (
        question.strip()
    )
    conversation_reply = (
        get_conversation_reply(
            normalized_question
        )
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
        message=(
            "Searching company policies..."
        ),
    )
    try:
        search_results = (
            search_document_chunks(
                query=normalized_question,
                document_id=document_id,
                top_k=top_k,
                database=database,
            )
        )
    except DocumentSearchError:
        yield stream_event(
            "error",
            message=(
                "Company policy search is "
                "currently unavailable."
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
        message=(
            "Generating policy guidance..."
        ),
    )
    answer_parts: list[str] = []
    stream_buffer = ""
    holdback_length = (
        len(
            NO_SUPPORTING_POLICY_SENTINEL
        )
        + 8
    )
    try:
        for text_delta in (
            stream_grounded_answer_text(
                question=normalized_question,
                evidence_context=evidence_context,
            )
        ):
            answer_parts.append(
                text_delta
            )
            stream_buffer += text_delta
            stream_buffer = (
                remove_policy_sentinel(
                    stream_buffer
                )
            )
            if (
                len(stream_buffer)
                <= holdback_length
            ):
                continue
            safe_character_count = (
                len(stream_buffer)
                - holdback_length
            )
            safe_text = stream_buffer[
                :safe_character_count
            ]
            stream_buffer = stream_buffer[
                safe_character_count:
            ]
            if safe_text:
                yield stream_event(
                    "delta",
                    text=safe_text,
                )
    except ChatServiceError:
        yield stream_event(
            "error",
            message=(
                "The local AI could not "
                "complete the streaming response."
            ),
        )
        return
    final_answer = (
        sanitize_policy_answer(
            "".join(answer_parts)
        )
    )
    if not final_answer:
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
    remaining_text = (
        remove_policy_sentinel(
            stream_buffer
        )
    )
    if remaining_text:
        yield stream_event(
            "delta",
            text=remaining_text,
        )
    model_output = SimpleNamespace(
        answer=final_answer,
        used_source_ids=[],
    )
    valid_source_ids = (
        collect_valid_source_ids(
            model_output=model_output,
            source_map=source_map,
        )
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
    citations = build_citations(
        valid_source_ids=valid_source_ids,
        source_map=source_map,
    )
    if not citations:
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
        "citations": citations,
        "retrieved_chunks": len(
            source_map
        ),
        "model": settings.ollama_chat_model,
    }
    yield stream_event(
        "final",
        data=result,
    )
