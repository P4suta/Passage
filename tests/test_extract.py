from pathlib import Path

from passage_pipeline.extract import extract_book
from passage_pipeline.models import slugify as _slugify


class TestExtractBook:
    def test_metadata(self, minimal_epub: Path):
        book = extract_book(str(minimal_epub))
        assert book.title == "Test Novel"
        assert book.author == "Jane Doe"
        assert book.language == "en"
        assert book.year == 1925

    def test_book_id_is_slug(self, minimal_epub: Path):
        book = extract_book(str(minimal_epub))
        assert book.book_id == "jane-doe-test-novel"

    def test_chapters_extracted(self, minimal_epub: Path):
        book = extract_book(str(minimal_epub))
        assert len(book.chapters) >= 2
        titles = [c.title for c in book.chapters]
        assert "Chapter 1" in titles
        assert "Chapter 2" in titles

    def test_paragraph_text(self, minimal_epub: Path):
        book = extract_book(str(minimal_epub))
        ch1 = next(c for c in book.chapters if c.title == "Chapter 1")
        assert "It was a bright cold day in April." in ch1.text
        assert "The clocks were striking thirteen." in ch1.text
        # Paragraphs joined by double newline
        assert "\n\n" in ch1.text

    def test_no_date_defaults_to_zero(self, no_date_epub: Path):
        book = extract_book(str(no_date_epub))
        assert book.year == 0

    def test_no_date_language(self, no_date_epub: Path):
        book = extract_book(str(no_date_epub))
        assert book.language == "fr"


class TestSlugify:
    def test_basic(self):
        assert _slugify("Jane Austen-Pride and Prejudice") == "jane-austen-pride-and-prejudice"

    def test_special_chars(self):
        assert _slugify("É. Zola — L'Assommoir!") == "zola-l-assommoir"

    def test_leading_trailing(self):
        assert _slugify("  --hello-- ") == "hello"
