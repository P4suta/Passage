from passage_pipeline.models import Chapter, ExtractedBook, TextChunk


class TestChapter:
    def test_create(self):
        ch = Chapter(title="Chapter 1", text="Some text.", index=0)
        assert ch.title == "Chapter 1"
        assert ch.text == "Some text."
        assert ch.index == 0


class TestExtractedBook:
    def test_create(self):
        book = ExtractedBook(
            book_id="author-title",
            title="Title",
            author="Author",
            language="en",
            year=1900,
            chapters=[Chapter(title="Ch1", text="Text", index=0)],
        )
        assert book.book_id == "author-title"
        assert len(book.chapters) == 1

    def test_empty_chapters(self):
        book = ExtractedBook(
            book_id="id",
            title="T",
            author="A",
            language="en",
            year=0,
            chapters=[],
        )
        assert book.chapters == []


class TestTextChunk:
    def test_create(self):
        chunk = TextChunk(
            chunk_id="book-id:00001",
            text="Some passage text.",
            book_id="book-id",
            title="Book Title",
            author="Author",
            year=1850,
            language="en",
            chapter="Chapter 1",
            chunk_index=1,
        )
        assert chunk.chunk_id == "book-id:00001"
        assert chunk.chunk_index == 1

    def test_chunk_id_format(self):
        chunk = TextChunk(
            chunk_id="shakespeare-hamlet:00042",
            text="To be or not to be.",
            book_id="shakespeare-hamlet",
            title="Hamlet",
            author="Shakespeare",
            year=1603,
            language="en",
            chapter="Act III",
            chunk_index=42,
        )
        assert chunk.chunk_id == f"{chunk.book_id}:{chunk.chunk_index:05d}"
