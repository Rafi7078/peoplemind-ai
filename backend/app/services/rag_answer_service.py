import re
from time import perf_counter
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
    generate_grounded_answer,
)
FALLBACK_ANSWER = "No supporting policy found"
SOURCE_ID_PATTERN = re.compile(
    r"\bS\d+\b",
    flags=re.IGNORECASE,
)
SENTINEL_PATTERN = re.compile(
    re.escape(
        NO_SUPPORTING_POLICY_SENTINEL
    ),
    flags=re.IGNORECASE,
)
MULTIPLE_BLANK_LINES_PATTERN = re.compile(
    r"\n{3,}",
)
SOURCE_APPENDIX_LINE_PATTERN = re.compile(
    (
        r"^\s*\[?\s*"
        r"(?:supporting\s+sources?|sources?|references?)"
        r"\s*:\s*"
        r"(?:\[?S\d+\]?(?:\s*[,;]\s*|\s*)?)+"
        r"\s*\]?\s*$"
    ),
    flags=re.IGNORECASE,
)
class RagAnswerError(RuntimeError):
    pass
def remove_policy_sentinel(
    answer: str,
) -> str:
    return SENTINEL_PATTERN.sub(
        "",
        answer,
    )
def remove_source_appendix_lines(
    answer: str,
) -> str:
    visible_lines: list[str] = []
    for line in answer.splitlines():
        if SOURCE_APPENDIX_LINE_PATTERN.fullmatch(
            line.strip()
        ):
            continue
        visible_lines.append(line)
    return "\n".join(visible_lines)
def sanitize_policy_answer(
    answer: str,
) -> str:
    cleaned_answer = (
        remove_source_appendix_lines(
            remove_policy_sentinel(answer)
        )
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    cleaned_lines = [
        line.rstrip()
        for line in cleaned_answer.split("\n")
    ]
    normalized_answer = "\n".join(
        cleaned_lines
    ).strip()
    return MULTIPLE_BLANK_LINES_PATTERN.sub(
        "\n\n",
        normalized_answer,
    )
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
        normalized_source_id = (
            normalize_source_id(
                candidate
            )
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
def merge_search_results_by_page(
    search_results: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    merged_results: list[dict[str, Any]] = []
    result_positions: dict[
        tuple[int, int],
        int,
    ] = {}
    for result in search_results:
        distance = float(
            result["distance"]
        )
        if distance > settings.rag_max_distance:
            continue
        document_id = int(
            result["document_id"]
        )
        page_number = int(
            result["page_number"]
        )
        chunk_index = int(
            result["chunk_index"]
        )
        text = str(
            result["text"]
        ).strip()
        page_key = (
            document_id,
            page_number,
        )
        existing_position = (
            result_positions.get(page_key)
        )
        if existing_position is None:
            result_positions[page_key] = len(
                merged_results
            )
            merged_results.append(
                {
                    "document_id": document_id,
                    "document_name": str(
                        result["document_name"]
                    ),
                    "page_number": page_number,
                    "chunk_index": chunk_index,
                    "chunk_indices": [
                        chunk_index
                    ],
                    "distance": distance,
                    "text_parts": (
                        [text]
                        if text
                        else []
                    ),
                }
            )
            continue
        merged_result = merged_results[
            existing_position
        ]
        merged_result["distance"] = min(
            float(
                merged_result["distance"]
            ),
            distance,
        )
        chunk_indices = merged_result[
            "chunk_indices"
        ]
        if chunk_index not in chunk_indices:
            chunk_indices.append(
                chunk_index
            )
        text_parts = merged_result[
            "text_parts"
        ]
        if (
            text
            and text not in text_parts
        ):
            text_parts.append(text)
    return merged_results
def build_evidence_context(
    search_results: list[dict[str, Any]],
) -> tuple[
    str,
    dict[str, dict[str, Any]],
]:
    context_blocks: list[str] = []
    source_map: dict[
        str,
        dict[str, Any],
    ] = {}
    current_character_count = 0
    merged_results = (
        merge_search_results_by_page(
            search_results
        )
    )
    for result in merged_results:
        source_id = (
            f"S{len(source_map) + 1}"
        )
        chunk_indices = sorted(
            int(chunk_index)
            for chunk_index in result[
                "chunk_indices"
            ]
        )
        merged_text = "\n\n".join(
            result["text_parts"]
        )
        block = (
            f"[{source_id}]\n"
            f"Document: "
            f"{result['document_name']}\n"
            f"Document ID: "
            f"{result['document_id']}\n"
            f"Page: "
            f"{result['page_number']}\n"
            f"Chunks: "
            f"{', '.join(map(str, chunk_indices))}\n"
            f"Text:\n{merged_text}\n"
        )
        if (
            context_blocks
            and (
                current_character_count
                + len(block)
                > settings.rag_max_context_chars
            )
        ):
            break
        context_blocks.append(block)
        current_character_count += len(
            block
        )
        source_map[source_id] = {
            "document_id": (
                result["document_id"]
            ),
            "document_name": (
                result["document_name"]
            ),
            "page_number": (
                result["page_number"]
            ),
            "chunk_index": (
                chunk_indices[0]
            ),
            "chunk_indices": (
                chunk_indices
            ),
            "distance": (
                result["distance"]
            ),
            "text": merged_text,
        }
    return (
        "\n---\n".join(
            context_blocks
        ),
        source_map,
    )
def build_citations(
    valid_source_ids: list[str],
    source_map: dict[
        str,
        dict[str, Any],
    ],
) -> list[dict[str, Any]]:
    citations: list[
        dict[str, Any]
    ] = []
    cited_pages: set[
        tuple[int, int]
    ] = set()
    for source_id in valid_source_ids:
        source = source_map[
            source_id
        ]
        page_key = (
            int(
                source["document_id"]
            ),
            int(
                source["page_number"]
            ),
        )
        if page_key in cited_pages:
            continue
        cited_pages.add(page_key)
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
def answer_document_question(
    question: str,
    document_id: int | None,
    top_k: int,
) -> dict[str, Any]:
    normalized_question = (
        question.strip()
    )
    conversation_reply = (
        get_conversation_reply(
            normalized_question
        )
    )
    if conversation_reply is not None:
        return conversation_response(
            question=normalized_question,
            answer=conversation_reply.answer,
        )
    request_started = perf_counter()
    search_started = perf_counter()
    try:
        search_results = (
            search_document_chunks(
                query=normalized_question,
                document_id=document_id,
                top_k=top_k,
            )
        )
    except DocumentSearchError as error:
        raise RagAnswerError(
            str(error)
        ) from error
    search_seconds = (
        perf_counter() - search_started
    )
    evidence_context, source_map = (
        build_evidence_context(
            search_results
        )
    )
    print(
        "[PERF] RAG search: "
        f"{search_seconds:.2f}s | "
        f"results={len(search_results)} | "
        f"sources={len(source_map)} | "
        f"evidence_chars={len(evidence_context)}",
        flush=True,
    )
    if not source_map:
        return fallback_response(
            question=normalized_question,
            retrieved_chunks=len(
                search_results
            ),
        )
    model_started = perf_counter()
    try:
        model_output = (
            generate_grounded_answer(
                question=normalized_question,
                evidence_context=evidence_context,
            )
        )
    except ChatServiceError as error:
        raise RagAnswerError(
            str(error)
        ) from error
    model_seconds = (
        perf_counter() - model_started
    )
    total_seconds = (
        perf_counter() - request_started
    )
    print(
        "[PERF] RAG model: "
        f"{model_seconds:.2f}s | "
        f"total={total_seconds:.2f}s",
        flush=True,
    )
    sanitized_answer = (
        sanitize_policy_answer(
            model_output.answer
        )
    )
    model_output.answer = (
        sanitized_answer
    )
    valid_source_ids = (
        collect_valid_source_ids(
            model_output=model_output,
            source_map=source_map,
        )
    )
    if (
        not model_output.answerable
        or not sanitized_answer
        or not valid_source_ids
    ):
        return fallback_response(
            question=normalized_question,
            retrieved_chunks=len(
                source_map
            ),
        )
    citations = build_citations(
        valid_source_ids=valid_source_ids,
        source_map=source_map,
    )
    if not citations:
        return fallback_response(
            question=normalized_question,
            retrieved_chunks=len(
                source_map
            ),
        )
    return {
        "question": normalized_question,
        "answer": sanitized_answer,
        "answer_found": True,
        "response_type": "policy_guidance",
        "citations": citations,
        "retrieved_chunks": len(
            source_map
        ),
        "model": settings.ollama_chat_model,
    }
