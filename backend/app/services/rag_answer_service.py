import re
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
    generate_grounded_answer,
)
FALLBACK_ANSWER = "No supporting policy found"
SOURCE_ID_PATTERN = re.compile(
    r"\bS\d+\b",
    flags=re.IGNORECASE,
)
class RagAnswerError(RuntimeError):
    pass
def conversation_response(
    question: str,
    answer: str,
) -> dict[str, Any]:
    return {
        "question": question,
        "answer": answer,
        "answer_found": False,
        "response_type": "conversation",
        "citations": [],
        "retrieved_chunks": 0,
        "model": "deterministic-router",
    }
def fallback_response(
    question: str,
    retrieved_chunks: int = 0,
) -> dict[str, Any]:
    return {
        "question": question,
        "answer": FALLBACK_ANSWER,
        "answer_found": False,
        "response_type": "no_supporting_policy",
        "citations": [],
        "retrieved_chunks": retrieved_chunks,
        "model": settings.ollama_chat_model,
    }
def normalize_source_id(
    raw_source_id: str,
) -> str | None:
    match = SOURCE_ID_PATTERN.search(
        str(raw_source_id)
    )
    if match is None:
        return None
    return match.group(0).upper()
def collect_valid_source_ids(
    model_output: Any,
    source_map: dict[str, dict[str, Any]],
) -> list[str]:
    candidates: list[str] = [
        str(source_id)
        for source_id in model_output.used_source_ids
    ]
    candidates.extend(
        SOURCE_ID_PATTERN.findall(
            model_output.answer
        )
    )
    valid_source_ids: list[str] = []
    for candidate in candidates:
        normalized_source_id = normalize_source_id(
            candidate
        )
        if normalized_source_id is None:
            continue
        if normalized_source_id not in source_map:
            continue
        if normalized_source_id in valid_source_ids:
            continue
        valid_source_ids.append(
            normalized_source_id
        )
    return valid_source_ids
def build_evidence_context(
    search_results: list[dict[str, Any]],
) -> tuple[str, dict[str, dict[str, Any]]]:
    context_blocks: list[str] = []
    source_map: dict[str, dict[str, Any]] = {}
    current_character_count = 0
    for result in search_results:
        distance = float(result["distance"])
        if distance > settings.rag_max_distance:
            continue
        source_id = f"S{len(source_map) + 1}"
        block = (
            f"[{source_id}]\n"
            f"Document: {result['document_name']}\n"
            f"Document ID: {result['document_id']}\n"
            f"Page: {result['page_number']}\n"
            f"Chunk: {result['chunk_index']}\n"
            f"Text:\n{result['text']}\n"
        )
        if (
            context_blocks
            and current_character_count + len(block)
            > settings.rag_max_context_chars
        ):
            break
        context_blocks.append(block)
        current_character_count += len(block)
        source_map[source_id] = result
    return (
        "\n---\n".join(context_blocks),
        source_map,
    )
def answer_document_question(
    question: str,
    document_id: int | None,
    top_k: int,
) -> dict[str, Any]:
    normalized_question = question.strip()
    conversation_reply = get_conversation_reply(
        normalized_question
    )
    if conversation_reply is not None:
        return conversation_response(
            question=normalized_question,
            answer=conversation_reply.answer,
        )
    try:
        search_results = search_document_chunks(
            query=normalized_question,
            document_id=document_id,
            top_k=top_k,
        )
    except DocumentSearchError as error:
        raise RagAnswerError(
            str(error)
        ) from error
    evidence_context, source_map = (
        build_evidence_context(
            search_results
        )
    )
    if not source_map:
        return fallback_response(
            question=normalized_question,
            retrieved_chunks=len(
                search_results
            ),
        )
    try:
        model_output = generate_grounded_answer(
            question=normalized_question,
            evidence_context=evidence_context,
        )
    except ChatServiceError as error:
        raise RagAnswerError(
            str(error)
        ) from error
    valid_source_ids = collect_valid_source_ids(
        model_output=model_output,
        source_map=source_map,
    )
    if (
        not model_output.answerable
        or not model_output.answer.strip()
        or not valid_source_ids
    ):
        return fallback_response(
            question=normalized_question,
            retrieved_chunks=len(
                source_map
            ),
        )
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
    return {
        "question": normalized_question,
        "answer": model_output.answer.strip(),
        "answer_found": True,
        "response_type": "policy_guidance",
        "citations": citations,
        "retrieved_chunks": len(
            source_map
        ),
        "model": settings.ollama_chat_model,
    }
