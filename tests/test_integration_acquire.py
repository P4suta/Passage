"""Integration tests for acquire module against live Standard Ebooks OPDS feed.

These tests require:
- Network access to standardebooks.org
- SE_EMAIL set in .env (Patrons Circle membership)

Run with: uv run pytest -m integration --run-integration
"""

import os
from pathlib import Path

import pytest

from passage_pipeline.acquire import fetch_catalog, download_epub, OPDS_URL
from passage_pipeline.models import CatalogEntry

pytestmark = pytest.mark.integration

requires_se_email = pytest.mark.skipif(
    not os.environ.get("SE_EMAIL"),
    reason="SE_EMAIL not set — requires Patrons Circle membership",
)


@requires_se_email
class TestFetchCatalogLive:
    """Verify OPDS feed parsing against the real Standard Ebooks catalog."""

    @pytest.fixture(scope="class")
    def catalog(self) -> list[CatalogEntry]:
        return fetch_catalog()

    def test_returns_nonempty_catalog(self, catalog):
        assert len(catalog) > 100, f"Expected 100+ books, got {len(catalog)}"

    def test_entries_are_catalog_entry(self, catalog):
        assert all(isinstance(e, CatalogEntry) for e in catalog)

    def test_entries_have_required_fields(self, catalog):
        for entry in catalog[:10]:
            assert entry.title, "title must not be empty"
            assert entry.author, "author must not be empty"
            assert entry.epub_url.startswith("https://"), f"bad epub_url: {entry.epub_url}"
            assert ".epub" in entry.epub_url, f"bad epub_url: {entry.epub_url}"

    def test_entries_have_metadata(self, catalog):
        """Most entries should have language and year populated."""
        with_language = [e for e in catalog if e.language]
        with_year = [e for e in catalog if e.year > 0]
        assert len(with_language) > len(catalog) * 0.9, "Expected 90%+ entries with language"
        assert len(with_year) > len(catalog) * 0.9, "Expected 90%+ entries with year"

    def test_english_entries_exist(self, catalog):
        english = [e for e in catalog if e.language.startswith("en")]
        assert len(english) > 50, f"Expected 50+ English books, got {len(english)}"

    def test_subjects_populated(self, catalog):
        """At least some entries should have subject categories."""
        with_subjects = [e for e in catalog if e.subjects]
        assert len(with_subjects) > len(catalog) * 0.5, "Expected 50%+ entries with subjects"

    def test_default_url_points_to_all(self):
        assert "/all" in OPDS_URL, "Default URL should point to /feeds/opds/all"


@requires_se_email
class TestDownloadEpubLive:
    """Verify EPUB download against a real Standard Ebooks file."""

    def test_download_real_epub(self, tmp_path: Path):
        catalog = fetch_catalog()
        entry = catalog[0]

        epub_path = tmp_path / "test.epub"
        download_epub(entry.epub_url, epub_path)

        assert epub_path.exists()
        content = epub_path.read_bytes()
        assert content[:2] == b"PK", "EPUB should be a ZIP file (PK header)"
        assert len(content) > 1000, "EPUB should be more than 1KB"

    def test_skip_existing_file(self, tmp_path: Path):
        sentinel = b"do not overwrite"
        epub_path = tmp_path / "existing.epub"
        epub_path.write_bytes(sentinel)

        catalog = fetch_catalog()
        download_epub(catalog[0].epub_url, epub_path)

        assert epub_path.read_bytes() == sentinel


class TestNoAuthFallback:
    """Verify behavior when SE_EMAIL is not set."""

    def test_fetch_catalog_without_auth_gets_401(self, monkeypatch):
        monkeypatch.delenv("SE_EMAIL", raising=False)
        with pytest.raises(Exception):
            fetch_catalog()
