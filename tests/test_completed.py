"""Tests for the completed-books idempotency feature in main.py."""

from pathlib import Path

from passage_pipeline.main import (
    _load_completed,
    _mark_completed,
)
from passage_pipeline.models import slugify


class TestLoadCompleted:
    def test_missing_file(self, tmp_path: Path):
        result = _load_completed(tmp_path / ".completed")
        assert result == set()

    def test_empty_file(self, tmp_path: Path):
        p = tmp_path / ".completed"
        p.write_text("")
        assert _load_completed(p) == set()

    def test_reads_ids(self, tmp_path: Path):
        p = tmp_path / ".completed"
        p.write_text("book-a\nbook-b\n")
        assert _load_completed(p) == {"book-a", "book-b"}

    def test_ignores_blank_lines(self, tmp_path: Path):
        p = tmp_path / ".completed"
        p.write_text("book-a\n\nbook-b\n\n")
        assert _load_completed(p) == {"book-a", "book-b"}


class TestMarkCompleted:
    def test_creates_file(self, tmp_path: Path):
        p = tmp_path / ".completed"
        _mark_completed(p, "book-a")
        assert p.read_text() == "book-a\n"

    def test_appends(self, tmp_path: Path):
        p = tmp_path / ".completed"
        _mark_completed(p, "book-a")
        _mark_completed(p, "book-b")
        assert p.read_text() == "book-a\nbook-b\n"

    def test_roundtrip(self, tmp_path: Path):
        p = tmp_path / ".completed"
        _mark_completed(p, "book-a")
        _mark_completed(p, "book-b")
        assert _load_completed(p) == {"book-a", "book-b"}
