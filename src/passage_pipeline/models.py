import re
from dataclasses import dataclass, field


def slugify(text: str) -> str:
    """Convert text to a URL-friendly slug."""
    slug = text.lower().strip()
    slug = re.sub(r"[^a-z0-9]+", "-", slug)
    return slug.strip("-")


@dataclass
class CatalogEntry:
    title: str
    author: str
    epub_url: str
    language: str
    year: int
    subjects: list[str] = field(default_factory=list)
    summary: str = ""


@dataclass
class Chapter:
    title: str
    text: str
    index: int


@dataclass
class ExtractedBook:
    book_id: str
    title: str
    author: str
    language: str
    year: int
    chapters: list[Chapter]


@dataclass
class TextChunk:
    chunk_id: str  # "{book_id}:{chunk_index:05d}"
    text: str
    book_id: str
    title: str
    author: str
    year: int
    language: str
    chapter: str
    chunk_index: int
