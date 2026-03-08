from dataclasses import replace

from passage_pipeline.models import ExtractedBook, TextChunk

MIN_CHUNK_CHARS = 80
MAX_CHUNK_CHARS = 1500


def _split_long_text(text: str, max_chars: int) -> list[str]:
    """Split text exceeding max_chars at sentence boundaries."""
    if len(text) <= max_chars:
        return [text]

    fragments: list[str] = []
    remaining = text
    while len(remaining) > max_chars:
        cut = max_chars
        for sep in (". ", ".\u201d ", "! ", "? ", "。", "！", "？"):
            pos = remaining.rfind(sep, 0, max_chars)
            if pos > 0:
                cut = pos + len(sep)
                break
        else:
            # No sentence boundary found — split at space
            space_pos = remaining.rfind(" ", 0, max_chars)
            if space_pos > max_chars // 2:
                cut = space_pos + 1
        fragments.append(remaining[:cut].rstrip())
        remaining = remaining[cut:].lstrip()
    if remaining:
        fragments.append(remaining)
    return fragments


def chunk_book(book: ExtractedBook) -> list[TextChunk]:
    """Split an entire book into chunks by paragraph boundaries."""
    chunks: list[TextChunk] = []
    global_index = 0

    for chapter in book.chapters:
        paragraphs = chapter.text.split("\n\n")
        buffer = ""

        for raw_para in paragraphs:
            for para in _split_long_text(raw_para, MAX_CHUNK_CHARS):
                candidate = f"{buffer}\n\n{para}".strip() if buffer else para

                if len(candidate) > MAX_CHUNK_CHARS and buffer:
                    chunks.append(
                        TextChunk(
                            chunk_id=f"{book.book_id}:{global_index:05d}",
                            text=buffer,
                            book_id=book.book_id,
                            title=book.title,
                            author=book.author,
                            year=book.year,
                            language=book.language,
                            chapter=chapter.title,
                            chunk_index=global_index,
                        )
                    )
                    global_index += 1
                    buffer = para
                else:
                    buffer = candidate

        # Flush remaining buffer
        if buffer and len(buffer) >= MIN_CHUNK_CHARS:
            chunks.append(
                TextChunk(
                    chunk_id=f"{book.book_id}:{global_index:05d}",
                    text=buffer,
                    book_id=book.book_id,
                    title=book.title,
                    author=book.author,
                    year=book.year,
                    language=book.language,
                    chapter=chapter.title,
                    chunk_index=global_index,
                )
            )
            global_index += 1
        elif buffer and chunks:
            # Too short — merge into previous chunk
            last = chunks[-1]
            chunks[-1] = replace(last, text=f"{last.text}\n\n{buffer}")

    return chunks
