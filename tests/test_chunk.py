from passage_pipeline.chunk import (
    chunk_book,
    _split_sentences,
    _group_sentences,
    MIN_CHUNK_CHARS,
    TARGET_CHUNK_CHARS,
    MAX_CHUNK_CHARS,
)
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


class TestSplitSentences:
    def test_simple_english(self):
        result = _split_sentences("Hello world. How are you? I am fine!")
        assert result == ["Hello world.", "How are you?", "I am fine!"]

    def test_abbreviation_mr(self):
        result = _split_sentences("Mr. Smith went home. He was tired.")
        assert result == ["Mr. Smith went home.", "He was tired."]

    def test_abbreviation_dr(self):
        result = _split_sentences("Dr. Jones arrived. She examined the patient.")
        assert result == ["Dr. Jones arrived.", "She examined the patient."]

    def test_abbreviation_etc(self):
        result = _split_sentences("Cats, dogs, etc. are pets. They need care.")
        assert result == ["Cats, dogs, etc. are pets.", "They need care."]

    def test_ellipsis_no_split(self):
        result = _split_sentences("He paused... then continued. It was done.")
        assert result == ["He paused... then continued.", "It was done."]

    def test_japanese(self):
        result = _split_sentences("これは文です。次の文です。最後です。")
        assert result == ["これは文です。", "次の文です。", "最後です。"]

    def test_empty_string(self):
        assert _split_sentences("") == []

    def test_single_sentence_no_trailing_space(self):
        result = _split_sentences("Just one sentence.")
        assert result == ["Just one sentence."]

    def test_closing_quote(self):
        result = _split_sentences('"Hello," she said. "Goodbye." He left.')
        # The closing quote after "Goodbye." should be kept with it
        assert len(result) >= 2

    def test_multiple_spaces(self):
        result = _split_sentences("First.  Second.  Third.")
        assert result == ["First.", "Second.", "Third."]


class TestGroupSentences:
    def test_single_short_sentence_above_min(self):
        sentences = ["A" * MIN_CHUNK_CHARS]
        result = _group_sentences(sentences, set())
        assert result == sentences

    def test_single_short_sentence_below_min_discarded(self):
        sentences = ["A" * (MIN_CHUNK_CHARS - 1)]
        result = _group_sentences(sentences, set())
        assert result == []

    def test_groups_up_to_target(self):
        # 5 sentences of 50 chars each → should group ~4 per chunk (200 target)
        sentences = [("x" * 48 + ". ") for _ in range(8)]
        result = _group_sentences(sentences, set())
        assert len(result) >= 2
        for chunk in result:
            assert len(chunk) <= MAX_CHUNK_CHARS

    def test_respects_max(self):
        # Two sentences, each 250 chars → together 500+ > MAX, should be separate
        s1 = "A" * 250
        s2 = "B" * 250
        result = _group_sentences([s1, s2], set())
        assert len(result) == 2

    def test_paragraph_break_respected(self):
        # Two sentences in different paragraphs, each above MIN
        s1 = "A" * 60
        s2 = "B" * 60
        result = _group_sentences([s1, s2], {1})
        assert len(result) == 2

    def test_paragraph_break_merge_when_below_min(self):
        # First sentence below MIN, paragraph break at index 1
        # Should merge because first buffer < MIN
        s1 = "A" * 30
        s2 = "B" * 60
        result = _group_sentences([s1, s2], {1})
        assert len(result) == 1
        assert "\n\n" in result[0]  # Joined with paragraph separator

    def test_final_buffer_merges_into_previous(self):
        s1 = "A" * 60
        s2 = "B" * 30  # Below MIN
        result = _group_sentences([s1, s2], set())
        assert len(result) == 1
        assert "B" in result[0]

    def test_single_sentence_above_max_preserved(self):
        s = "A" * (MAX_CHUNK_CHARS + 100)
        result = _group_sentences([s], set())
        assert len(result) == 1
        assert result[0] == s


class TestChunkBook:
    def test_single_sentence_above_min(self):
        text = "This is a test sentence that is long enough to pass the minimum threshold for chunking."
        assert len(text) >= MIN_CHUNK_CHARS
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 1
        assert chunks[0].chunk_id == "test-book:00000"
        assert chunks[0].chapter == "Ch1"

    def test_single_sentence_below_min_no_previous_discarded(self):
        text = "Short."
        assert len(text) < MIN_CHUNK_CHARS
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert chunks == []

    def test_multiple_short_sentences_grouped(self):
        # Multiple short sentences that should be grouped together
        text = "First sentence here. Second sentence here. Third sentence here. Fourth one too."
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 1

    def test_long_paragraph_splits_into_multiple_chunks(self):
        # Build a paragraph with many sentences exceeding TARGET
        sentence = "This is a moderately long sentence for testing purposes. "
        text = sentence * 20  # ~1100 chars
        assert len(text) > TARGET_CHUNK_CHARS
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) >= 2
        for c in chunks:
            assert len(c.text) <= MAX_CHUNK_CHARS + 1  # Allow for joining char

    def test_paragraph_boundary_respected(self):
        # Two paragraphs, each above MIN
        para1 = "This is the first paragraph with enough content to stand alone as a chunk."
        para2 = "This is the second paragraph which also has enough content to be separate."
        assert len(para1) >= MIN_CHUNK_CHARS
        assert len(para2) >= MIN_CHUNK_CHARS
        text = f"{para1}\n\n{para2}"
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 2

    def test_short_paragraph_merges_with_next(self):
        # First paragraph is short (heading-like), second is substantial
        para1 = "Chapter One"
        para2 = "This is a longer paragraph that provides the actual content of the chapter section."
        assert len(para1) < MIN_CHUNK_CHARS
        text = f"{para1}\n\n{para2}"
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 1
        assert "Chapter One" in chunks[0].text
        assert para2 in chunks[0].text

    def test_abbreviation_not_split(self):
        text = "Mr. Smith went to the store on a bright sunny morning. He bought many things."
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 1
        assert "Mr. Smith" in chunks[0].text

    def test_single_sentence_above_max_preserved(self):
        # A single very long sentence (no sentence boundaries) > MAX
        text = "word " * 100  # 500 chars, no sentence-ending punctuation
        text = text.strip()
        assert len(text) > MAX_CHUNK_CHARS
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 1
        assert chunks[0].text == text  # Preserved intact

    def test_empty_book(self):
        book = _make_book([])
        assert chunk_book(book) == []

    def test_empty_chapter_text(self):
        book = _make_book([Chapter(title="Ch1", text="", index=0)])
        assert chunk_book(book) == []

    def test_metadata_propagation(self):
        book = ExtractedBook(
            book_id="austen-pride",
            title="Pride and Prejudice",
            author="Jane Austen",
            language="en",
            year=1813,
            chapters=[
                Chapter(
                    title="Chapter 1",
                    text="It is a truth universally acknowledged, that a single man in possession of a good fortune, must be in want of a wife.",
                    index=0,
                )
            ],
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
        text = "A sufficiently long sentence to exceed the minimum chunk character limit easily."
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert chunks[0].chunk_id == "test-book:00000"

    def test_multiple_chapters_global_index(self):
        text1 = "First chapter has a sentence that is long enough to be a chunk on its own."
        text2 = "Second chapter also has a sentence that meets the minimum character threshold."
        book = _make_book([
            Chapter(title="Ch1", text=text1, index=0),
            Chapter(title="Ch2", text=text2, index=1),
        ])
        chunks = chunk_book(book)
        assert len(chunks) == 2
        assert chunks[0].chapter == "Ch1"
        assert chunks[1].chapter == "Ch2"
        assert chunks[0].chunk_index == 0
        assert chunks[1].chunk_index == 1

    def test_poetry_short_lines(self):
        # Poetry: each line is a short paragraph, should group together
        lines = ["Roses are red,", "Violets are blue,", "Sugar is sweet,", "And so are you."]
        text = "\n\n".join(lines)
        book = _make_book([Chapter(title="Poem", text=text, index=0)])
        chunks = chunk_book(book)
        # All lines together are ~60 chars, should be one chunk
        assert len(chunks) == 1

    def test_japanese_sentences(self):
        # Each sentence ~20 chars, 4 sentences = ~80 chars > MIN_CHUNK_CHARS
        text = "これは最初の文章です。これは二番目の文章です。これは三番目の文章です。これは四番目の文章です。"
        book = _make_book([Chapter(title="Ch1", text=text, index=0)])
        chunks = chunk_book(book)
        assert len(chunks) == 1
        assert "これは最初の文章です。" in chunks[0].text
