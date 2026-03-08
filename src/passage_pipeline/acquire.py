import os
from pathlib import Path
from xml.etree import ElementTree

import httpx

from passage_pipeline.models import CatalogEntry

OPDS_URL = "https://standardebooks.org/feeds/opds/all"
OUTPUT_DIR = Path("data/epubs")

ATOM_NS = "{http://www.w3.org/2005/Atom}"
OPDS_NS = "{http://opds-spec.org/2010/catalog}"
DC_NS = "{http://purl.org/dc/terms/}"


def _get_auth() -> httpx.BasicAuth | None:
    """Return Basic auth for Standard Ebooks OPDS feed if SE_EMAIL is set."""
    email = os.environ.get("SE_EMAIL")
    if email:
        return httpx.BasicAuth(username=email, password="")
    return None


def fetch_catalog(url: str = OPDS_URL) -> list[CatalogEntry]:
    """Parse OPDS catalog and return a list of book entries."""
    entries: list[CatalogEntry] = []
    next_url: str | None = url
    auth = _get_auth()

    while next_url:
        resp = httpx.get(next_url, auth=auth, follow_redirects=True, timeout=30)
        resp.raise_for_status()
        root = ElementTree.fromstring(resp.content)

        for entry in root.findall(f"{ATOM_NS}entry"):
            title = entry.findtext(f"{ATOM_NS}title", "")
            author = entry.findtext(f"{ATOM_NS}author/{ATOM_NS}name", "")

            epub_link = None
            for link in entry.findall(f"{ATOM_NS}link"):
                if "application/epub+zip" in link.get("type", ""):
                    epub_link = link.get("href")
                    break

            if not epub_link:
                continue

            language = entry.findtext(f"{DC_NS}language", "")
            issued = entry.findtext(f"{DC_NS}issued", "")
            year = int(issued[:4]) if issued and len(issued) >= 4 else 0
            summary = entry.findtext(f"{ATOM_NS}summary", "")
            subjects = [
                cat.get("term", "")
                for cat in entry.findall(f"{ATOM_NS}category")
                if cat.get("term")
            ]

            entries.append(CatalogEntry(
                title=title,
                author=author,
                epub_url=epub_link,
                language=language,
                year=year,
                subjects=subjects,
                summary=summary,
            ))

        next_el = root.find(f'{ATOM_NS}link[@rel="next"]')
        next_url = next_el.get("href") if next_el is not None else None

    return entries


async def download_epub(
    url: str,
    output_path: Path,
    *,
    client: httpx.AsyncClient | None = None,
) -> None:
    """Download an EPUB file, skipping if already exists."""
    if output_path.exists():
        return

    own_client = client is None
    if own_client:
        client = httpx.AsyncClient()

    try:
        resp = await client.get(
            url, auth=_get_auth(), follow_redirects=True, timeout=60,
        )
        resp.raise_for_status()
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(resp.content)
    finally:
        if own_client:
            await client.aclose()
