import argparse
import sys
from pathlib import Path

from passage_pipeline.acquire import fetch_catalog, download_epub, OUTPUT_DIR
from passage_pipeline.extract import extract_book
from passage_pipeline.chunk import chunk_book
from passage_pipeline.embed import generate_embeddings
from passage_pipeline.ingest import upload_to_vectorize


def run_pipeline(
    max_books: int | None = None,
    dry_run: bool = False,
    output_dir: Path = OUTPUT_DIR,
) -> None:
    """Run the full preprocessing pipeline."""
    # Stage 1: Acquire
    print("Stage 1: Fetching OPDS catalog...")
    catalog = fetch_catalog()
    if max_books:
        catalog = catalog[:max_books]
    print(f"  Found {len(catalog)} books")

    for i, entry in enumerate(catalog):
        book_name = f"{entry['author']} - {entry['title']}"
        print(f"\n[{i + 1}/{len(catalog)}] {book_name}")

        # Download
        filename = entry["epub_url"].split("/")[-1]
        epub_path = output_dir / filename
        print("  Downloading EPUB...")
        download_epub(entry["epub_url"], epub_path)

        # Stage 2: Extract
        print("  Extracting text...")
        extracted = extract_book(str(epub_path))
        if not extracted.chapters:
            print("  Skipping: no chapters found")
            continue

        # Stage 3: Chunk
        print("  Chunking...")
        chunks = chunk_book(extracted)
        print(f"  Created {len(chunks)} chunks")

        if dry_run:
            print("  [DRY RUN] Skipping embedding and ingestion")
            continue

        # Stage 4: Embed
        print("  Generating embeddings...")
        texts = [c.text for c in chunks]
        embeddings = generate_embeddings(texts)

        # Stage 5: Ingest
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
    args = parser.parse_args()
    run_pipeline(
        max_books=args.max_books,
        dry_run=args.dry_run,
        output_dir=args.output_dir,
    )


if __name__ == "__main__":
    main()
