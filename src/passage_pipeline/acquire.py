from pathlib import Path
from xml.etree import ElementTree

import httpx

OPDS_URL = "https://standardebooks.org/feeds/opds"
OUTPUT_DIR = Path("data/epubs")

ATOM_NS = "{http://www.w3.org/2005/Atom}"
OPDS_NS = "{http://opds-spec.org/2010/catalog}"


def fetch_catalog(url: str = OPDS_URL) -> list[dict]:
    """Parse OPDS catalog and return a list of book entries."""
    entries: list[dict] = []
    next_url: str | None = url

    while next_url:
        resp = httpx.get(next_url, follow_redirects=True, timeout=30)
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

            if epub_link:
                entries.append({
                    "title": title,
                    "author": author,
                    "epub_url": epub_link,
                })

        next_el = root.find(f'{ATOM_NS}link[@rel="next"]')
        next_url = next_el.get("href") if next_el is not None else None

    return entries


def download_epub(url: str, output_path: Path) -> None:
    """Download an EPUB file, skipping if already exists."""
    if output_path.exists():
        return

    resp = httpx.get(url, follow_redirects=True, timeout=60)
    resp.raise_for_status()
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(resp.content)
