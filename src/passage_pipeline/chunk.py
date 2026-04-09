import re
from dataclasses import replace

from passage_pipeline.models import ExtractedBook, TextChunk

MIN_CHUNK_CHARS = 50
TARGET_CHUNK_CHARS = 200
MAX_CHUNK_CHARS = 400

_ABBREVIATIONS = re.compile(
    r"\b(Mr|Mrs|Ms|Dr|St|Jr|Sr|vs|etc|Prof|Gen|Col|Sgt|Corp|Lt|Capt|Maj|Rev)\.$",
    re.IGNORECASE,
)

_SENTENCE_END = re.compile(
    r'(?<=[.!?])(?:["\u201d\u2019\u300d])?\s+|(?<=[。！？])(?:["\u201d\u2019\u300d])?'
)


def _split_sentences(text: str) -> list[str]:
    """Split text into sentences, respecting abbreviations and ellipses."""
    parts = _SENTENCE_END.split(text)
    sentences: list[str] = []
    for part in parts:
        stripped = part.strip()
        if not stripped:
            continue
        # Merge back if previous ended with an abbreviation or ellipsis
        if sentences and (
            _ABBREVIATIONS.search(sentences[-1])
            or sentences[-1].endswith("...")
        ):
            sentences[-1] = sentences[-1] + " " + stripped
        else:
            sentences.append(stripped)
    return sentences


def _group_sentences(
    sentences: list[str], paragraph_breaks: set[int]
) -> list[str]:
    """Group sentences into chunks respecting TARGET/MAX limits and paragraph breaks."""
    chunks: list[str] = []
    buffer = ""
    buffer_has_para_break = False

    for i, sentence in enumerate(sentences):
        is_para_break = i in paragraph_breaks

        # If adding this sentence would exceed MAX and buffer is non-empty, flush
        if buffer:
            sep = "\n\n" if is_para_break or buffer_has_para_break else " "
            candidate = buffer + sep + sentence
            if len(candidate) > MAX_CHUNK_CHARS:
                chunks.append(buffer)
                buffer = sentence
                buffer_has_para_break = False
            elif is_para_break and len(buffer) >= MIN_CHUNK_CHARS:
                # Respect paragraph boundary: flush current buffer
                chunks.append(buffer)
                buffer = sentence
                buffer_has_para_break = False
            elif len(buffer) >= TARGET_CHUNK_CHARS:
                # Buffer already at target, flush before adding more
                chunks.append(buffer)
                buffer = sentence
                buffer_has_para_break = False
            else:
                buffer = candidate
                if is_para_break:
                    buffer_has_para_break = True
        else:
            buffer = sentence
            buffer_has_para_break = False

    # Handle final buffer
    if buffer:
        if len(buffer) < MIN_CHUNK_CHARS and chunks:
            # Merge into previous chunk
            chunks[-1] = chunks[-1] + "\n\n" + buffer
        elif len(buffer) >= MIN_CHUNK_CHARS:
            chunks.append(buffer)
        # else: below MIN with no previous chunk → discard

    return chunks


def chunk_book(book: ExtractedBook) -> list[TextChunk]:
    """Split an entire book into chunks by sentence grouping."""
    chunks: list[TextChunk] = []
    global_index = 0

    for chapter in book.chapters:
        paragraphs = chapter.text.split("\n\n")
        all_sentences: list[str] = []
        paragraph_breaks: set[int] = set()

        for p_idx, para in enumerate(paragraphs):
            para = para.strip()
            if not para:
                continue
            sentences = _split_sentences(para)
            if not sentences:
                continue
            if all_sentences:
                # Mark the start of a new paragraph
                paragraph_breaks.add(len(all_sentences))
            all_sentences.extend(sentences)

        if not all_sentences:
            continue

        grouped = _group_sentences(all_sentences, paragraph_breaks)

        for text in grouped:
            chunks.append(
                TextChunk(
                    chunk_id=f"{book.book_id}:{global_index:05d}",
                    text=text,
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

    return chunks
