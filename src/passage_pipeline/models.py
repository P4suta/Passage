from dataclasses import dataclass


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
