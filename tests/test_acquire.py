from pathlib import Path

import httpx
import pytest
import respx

from passage_pipeline.acquire import fetch_catalog, download_epub

OPDS_PAGE_1 = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <entry>
    <title>Pride and Prejudice</title>
    <author><name>Jane Austen</name></author>
    <link type="application/epub+zip" href="https://example.com/pride.epub"/>
  </entry>
  <entry>
    <title>No EPUB Link</title>
    <author><name>Unknown</name></author>
    <link type="text/html" href="https://example.com/page"/>
  </entry>
  <link rel="next" href="https://example.com/opds?page=2"/>
</feed>
"""

OPDS_PAGE_2 = b"""\
<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom"
      xmlns:opds="http://opds-spec.org/2010/catalog">
  <entry>
    <title>Hamlet</title>
    <author><name>William Shakespeare</name></author>
    <link type="application/epub+zip" href="https://example.com/hamlet.epub"/>
  </entry>
</feed>
"""


class TestFetchCatalog:
    @respx.mock
    def test_single_page(self):
        respx.get(url__eq="https://example.com/opds").mock(
            return_value=httpx.Response(200, content=OPDS_PAGE_2)
        )
        entries = fetch_catalog("https://example.com/opds")
        assert len(entries) == 1
        assert entries[0]["title"] == "Hamlet"
        assert entries[0]["author"] == "William Shakespeare"
        assert entries[0]["epub_url"] == "https://example.com/hamlet.epub"

    @respx.mock
    def test_pagination(self):
        respx.get(url__eq="https://example.com/opds").mock(
            return_value=httpx.Response(200, content=OPDS_PAGE_1)
        )
        respx.get(url__eq="https://example.com/opds?page=2").mock(
            return_value=httpx.Response(200, content=OPDS_PAGE_2)
        )
        entries = fetch_catalog("https://example.com/opds")
        assert len(entries) == 2
        assert entries[0]["title"] == "Pride and Prejudice"
        assert entries[1]["title"] == "Hamlet"

    @respx.mock
    def test_skips_entries_without_epub_link(self):
        respx.get(url__eq="https://example.com/opds").mock(
            return_value=httpx.Response(200, content=OPDS_PAGE_1)
        )
        respx.get(url__eq="https://example.com/opds?page=2").mock(
            return_value=httpx.Response(200, content=OPDS_PAGE_2)
        )
        entries = fetch_catalog("https://example.com/opds")
        titles = [e["title"] for e in entries]
        assert "No EPUB Link" not in titles

    @respx.mock
    def test_http_error_raises(self):
        respx.get(url__eq="https://example.com/opds").mock(
            return_value=httpx.Response(500)
        )
        with pytest.raises(httpx.HTTPStatusError):
            fetch_catalog("https://example.com/opds")


class TestDownloadEpub:
    @respx.mock
    def test_downloads_file(self, tmp_path: Path):
        content = b"PK\x03\x04fake epub content"
        respx.get(url__eq="https://example.com/book.epub").mock(
            return_value=httpx.Response(200, content=content)
        )
        output = tmp_path / "book.epub"
        download_epub("https://example.com/book.epub", output)
        assert output.read_bytes() == content

    @respx.mock
    def test_skips_existing_file(self, tmp_path: Path):
        output = tmp_path / "book.epub"
        output.write_bytes(b"existing")
        route = respx.get(url__eq="https://example.com/book.epub").mock(
            return_value=httpx.Response(200, content=b"new")
        )
        download_epub("https://example.com/book.epub", output)
        assert output.read_bytes() == b"existing"
        assert route.call_count == 0

    @respx.mock
    def test_creates_parent_dirs(self, tmp_path: Path):
        content = b"PK\x03\x04data"
        respx.get(url__eq="https://example.com/book.epub").mock(
            return_value=httpx.Response(200, content=content)
        )
        output = tmp_path / "sub" / "dir" / "book.epub"
        download_epub("https://example.com/book.epub", output)
        assert output.exists()
