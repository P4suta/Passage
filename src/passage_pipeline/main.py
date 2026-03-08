import argparse
import os
import sys

from dotenv import load_dotenv

load_dotenv()
from pathlib import Path
from urllib.parse import urlparse

from passage_pipeline.acquire import fetch_catalog, download_epub, OUTPUT_DIR
from passage_pipeline.extract import extract_book
from passage_pipeline.chunk import chunk_book
from passage_pipeline.embed import generate_embeddings
from passage_pipeline.ingest import upload_to_vectorize
from passage_pipeline.store import upload_to_r2


def run_pipeline(
    max_books: int | None = None,
    dry_run: bool = False,
    output_dir: Path = OUTPUT_DIR,
    language: str | None = None,
) -> None:
    """Run the full preprocessing pipeline."""
    if not dry_run:
        missing = [
            key for key in (
                "CF_ACCOUNT_ID", "CF_API_TOKEN",
                "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY",
            )
            if not os.environ.get(key)
        ]
        if missing:
            print(
                f"Error: required environment variables not set: {', '.join(missing)}\n"
                "Copy .env.example to .env and fill in the values.",
                file=sys.stderr,
            )
            sys.exit(1)

    # Stage 1: Acquire
    print("Stage 1: Fetching OPDS catalog...")
    catalog = fetch_catalog()

    if language:
        catalog = [e for e in catalog if e.language.startswith(language)]

    if max_books:
        catalog = catalog[:max_books]
    print(f"  Found {len(catalog)} books")

    for i, entry in enumerate(catalog):
        book_name = f"{entry.author} - {entry.title}"
        print(f"\n[{i + 1}/{len(catalog)}] {book_name}")

        # Download
        filename = Path(urlparse(entry.epub_url).path).name
        epub_path = output_dir / filename
        print("  Downloading EPUB...")
        download_epub(entry.epub_url, epub_path)

        # Stage 2: Extract
        print("  Extracting text...")
        extracted = extract_book(str(epub_path))
        if not extracted.chapters:
            print("  Skipping: no chapters found")
            continue

        # Stage 3: Store chapter texts in R2
        print("  Uploading chapter texts to R2..." if not dry_run else "  [DRY RUN] Counting chapters for R2...")
        uploaded = upload_to_r2(extracted.chapters, extracted.book_id, dry_run=dry_run)
        print(f"  {'Uploaded' if not dry_run else 'Would upload'} {uploaded} chapters to R2")

        # Stage 4: Chunk
        print("  Chunking...")
        chunks = chunk_book(extracted)
        print(f"  Created {len(chunks)} chunks")

        if dry_run:
            print("  [DRY RUN] Skipping embedding and ingestion")
            continue

        # Stage 5: Embed
        print("  Generating embeddings...")
        texts = [c.text for c in chunks]
        embeddings = generate_embeddings(texts)

        # Stage 6: Ingest
        print("  Uploading to Vectorize...")
        upload_to_vectorize(chunks, embeddings)

    print("\nPipeline complete.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Passage preprocessing pipeline"
    )
    parser.add_argument(
        "--max-books",
        type=int,
        default=None,
        help="Maximum number of books to process",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Run without embedding/ingestion",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Directory for downloaded EPUBs",
    )
    parser.add_argument(
        "--language",
        type=str,
        default=None,
        help="Filter by language prefix (e.g. 'en' for English)",
    )
    args = parser.parse_args()
    run_pipeline(
        max_books=args.max_books,
        dry_run=args.dry_run,
        output_dir=args.output_dir,
        language=args.language,
    )


if __name__ == "__main__":
    main()
