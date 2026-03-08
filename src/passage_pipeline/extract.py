import warnings

import ebooklib
from ebooklib import epub
from bs4 import BeautifulSoup, XMLParsedAsHTMLWarning

from passage_pipeline.models import Chapter, ExtractedBook, slugify

warnings.filterwarnings("ignore", category=XMLParsedAsHTMLWarning)


def extract_book(epub_path: str) -> ExtractedBook:
    """Extract structured text from an EPUB file."""
    book = epub.read_epub(epub_path)

    title = book.get_metadata("DC", "title")[0][0]
    author = book.get_metadata("DC", "creator")[0][0]
    language = book.get_metadata("DC", "language")[0][0]

    date_meta = book.get_metadata("DC", "date")
    date_str = date_meta[0][0] if date_meta else ""
    year = int(date_str[:4]) if date_str else 0

    book_id = slugify(f"{author}-{title}")

    chapters: list[Chapter] = []
    for idx, item in enumerate(book.get_items_of_type(ebooklib.ITEM_DOCUMENT)):
        soup = BeautifulSoup(item.get_content(), "lxml")
        body = soup.find("body")
        if not body:
            continue

        heading = body.find(["h1", "h2", "h3"])
        chapter_title = (
            heading.get_text(strip=True) if heading else f"Chapter {idx + 1}"
        )

        paragraphs = []
        for p in body.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                paragraphs.append(text)

        if paragraphs:
            chapters.append(
                Chapter(
                    title=chapter_title,
                    text="\n\n".join(paragraphs),
                    index=idx,
                )
            )

    return ExtractedBook(
        book_id=book_id,
        title=title,
        author=author,
        language=language,
        year=year,
        chapters=chapters,
    )
