import os
import tempfile
from pathlib import Path

import pytest
from dotenv import load_dotenv
from ebooklib import epub

load_dotenv()


def pytest_collection_modifyitems(config, items):
    """Skip integration tests unless --run-integration is passed."""
    if config.getoption("--run-integration", default=False):
        return
    skip_integration = pytest.mark.skip(reason="use --run-integration to run")
    for item in items:
        if "integration" in item.keywords:
            item.add_marker(skip_integration)


def pytest_addoption(parser):
    parser.addoption(
        "--run-integration",
        action="store_true",
        default=False,
        help="Run integration tests that access external services",
    )


@pytest.fixture
def minimal_epub(tmp_path: Path) -> Path:
    """Create a minimal EPUB file for testing."""
    book = epub.EpubBook()
    book.set_identifier("test-id-123")
    book.set_title("Test Novel")
    book.set_language("en")
    book.add_author("Jane Doe")
    book.add_metadata("DC", "date", "1925-01-01")

    # Chapter 1
    ch1 = epub.EpubHtml(title="Chapter 1", file_name="ch1.xhtml", lang="en")
    ch1.set_content(
        b"<html><body>"
        b"<h1>Chapter 1</h1>"
        b"<p>It was a bright cold day in April.</p>"
        b"<p>The clocks were striking thirteen.</p>"
        b"</body></html>"
    )
    book.add_item(ch1)

    # Chapter 2
    ch2 = epub.EpubHtml(title="Chapter 2", file_name="ch2.xhtml", lang="en")
    ch2.set_content(
        b"<html><body>"
        b"<h2>Chapter 2</h2>"
        b"<p>Outside, even through the shut window-pane.</p>"
        b"</body></html>"
    )
    book.add_item(ch2)

    # Navigation
    book.toc = [epub.Link("ch1.xhtml", "Chapter 1", "ch1"),
                epub.Link("ch2.xhtml", "Chapter 2", "ch2")]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", ch1, ch2]

    epub_path = tmp_path / "test.epub"
    epub.write_epub(str(epub_path), book)
    return epub_path


@pytest.fixture
def no_date_epub(tmp_path: Path) -> Path:
    """EPUB without a date metadata field."""
    book = epub.EpubBook()
    book.set_identifier("test-no-date")
    book.set_title("Dateless Book")
    book.set_language("fr")
    book.add_author("Jean Dupont")

    ch1 = epub.EpubHtml(title="Ch1", file_name="ch1.xhtml", lang="fr")
    ch1.set_content(
        b"<html><body><p>Bonjour le monde.</p></body></html>"
    )
    book.add_item(ch1)

    book.toc = [epub.Link("ch1.xhtml", "Ch1", "ch1")]
    book.add_item(epub.EpubNcx())
    book.add_item(epub.EpubNav())
    book.spine = ["nav", ch1]

    epub_path = tmp_path / "no_date.epub"
    epub.write_epub(str(epub_path), book)
    return epub_path
