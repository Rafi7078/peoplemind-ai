def split_text_into_chunks(
    text: str,
    chunk_size: int,
    overlap: int,
) -> list[str]:
    if chunk_size <= 0:
        raise ValueError("Chunk size must be greater than zero.")
    if overlap < 0:
        raise ValueError("Chunk overlap cannot be negative.")
    if overlap >= chunk_size:
        raise ValueError(
            "Chunk overlap must be smaller than chunk size."
        )
    normalized_text = text.replace("\x00", "").strip()
    if not normalized_text:
        return []
    chunks: list[str] = []
    start = 0
    text_length = len(normalized_text)
    while start < text_length:
        tentative_end = min(
            start + chunk_size,
            text_length,
        )
        end = tentative_end
        if tentative_end < text_length:
            boundary_search_start = min(
                start + (chunk_size // 2),
                tentative_end,
            )
            newline_boundary = normalized_text.rfind(
                "\n",
                boundary_search_start,
                tentative_end,
            )
            space_boundary = normalized_text.rfind(
                " ",
                boundary_search_start,
                tentative_end,
            )
            preferred_boundary = max(
                newline_boundary,
                space_boundary,
            )
            if preferred_boundary > start:
                end = preferred_boundary
        chunk = normalized_text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= text_length:
            break
        start = max(
            end - overlap,
            start + 1,
        )
    return chunks
