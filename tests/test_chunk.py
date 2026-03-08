from passage_pipeline.chunk import chunk_book, MIN_CHUNK_CHARS, MAX_CHUNK_CHARS
from passage_pipeline.models import Chapter, ExtractedBook


def _make_book(chapters: list[Chapter], book_id: str = "test-book") -> ExtractedBook:
    return ExtractedBook(
        book_id=book_id,
        title="Test Book",
        author="Test Author",
        language="en",
        year=1900,
        chapters=chapters,
    )


class TestChunkBook:
    def test_single_paragraph_above_min(self):
        text = "A" * MIN_CHUNK_CHARS
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 1
        assert chunks[0].text == text
        assert chunks[0].chunk_id == "test-book:00000"
        assert chunks[0].chapter == "Ch1"

    def test_short_paragraph_below_min_merges_into_previous(self):
        # First chapter produces a chunk, second chapter's text is too short
        long_text = "A" * MIN_CHUNK_CHARS
        short_text = "B" * (MIN_CHUNK_CHARS - 1)
        book = _make_book([
            Chapter(title="Ch1", text=long_text, index=0),
            Chapter(title="Ch2", text=short_text, index=1),
        ])
        chunks = chunk_book(book)
        assert len(chunks) == 1
        assert short_text in chunks[0].text

    def test_large_paragraph_splits_on_boundary(self):
        # Two paragraphs that together exceed MAX_CHUNK_CHARS
        para1 = "A" * (MAX_CHUNK_CHARS - 10)
        para2 = "B" * (MAX_CHUNK_CHARS - 10)
        text = f"{para1}\n\n{para2}"
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 2
        assert chunks[0].text == para1
        assert chunks[1].text == para2

    def test_multiple_chapters(self):
        text1 = "A" * 200
        text2 = "B" * 200
        book = _make_book([
            Chapter(title="Ch1", text=text1, index=0),
            Chapter(title="Ch2", text=text2, index=1),
        ])
        chunks = chunk_book(book)
        assert len(chunks) == 2
        assert chunks[0].chapter == "Ch1"
        assert chunks[1].chapter == "Ch2"
        # Global index should be sequential
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1

    def test_empty_book(self):
        book = _make_book([])
        chunks = chunk_book(book)
        assert chunks == []

    def test_empty_chapter_text(self):
        book = _make_book([Chapter(title="Ch1", text="", index=0)])
        chunks = chunk_book(book)
        assert chunks == []

    def test_metadata_propagation(self):
        book = ExtractedBook(
            book_id="austen-pride",
            title="Pride and Prejudice",
            author="Jane Austen",
            language="en",
            year=1813,
            chapters=[Chapter(title="Chapter 1", text="X" * 200, index=0)],
        )
        chunks = chunk_book(book)
        assert len(chunks) == 1
        c = chunks[0]
        assert c.book_id == "austen-pride"
        assert c.title == "Pride and Prejudice"
        assert c.author == "Jane Austen"
        assert c.year == 1813
        assert c.language == "en"
        assert c.chapter == "Chapter 1"

    def test_chunk_id_format(self):
        text = "A" * 200
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert chunks[0].chunk_id == "test-book:00000"

    def test_paragraphs_merge_when_below_max(self):
        # Three short paragraphs that should merge into one chunk
        paras = [("P" * 30) for _ in range(3)]
        text = "\n\n".join(paras)
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 1
        assert chunks[0].text == text

    def test_flush_short_buffer_first_chapter_no_previous(self):
        # Only content is below MIN_CHUNK_CHARS and no previous chunk exists
        text = "A" * (MIN_CHUNK_CHARS - 1)
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert chunks == []
