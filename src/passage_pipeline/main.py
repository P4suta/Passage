import argparse
import asyncio
import os
import sys

from dotenv import load_dotenv

load_dotenv()
from pathlib import Path
from urllib.parse import urlparse

import httpx

from passage_pipeline.acquire import fetch_catalog, download_epub, OUTPUT_DIR
from passage_pipeline.extract import extract_book
from passage_pipeline.chunk import chunk_book
from passage_pipeline.embed import generate_embeddings
from passage_pipeline.ingest import delete_all_from_vectorize, upload_to_vectorize
from passage_pipeline.models import CatalogEntry
from passage_pipeline.store import delete_all_from_r2, upload_to_r2, _create_s3_client

# Concurrency limits
SEM_BOOK = 50
SEM_DOWNLOAD = 2
SEM_R2 = 20
SEM_EMBED = 30
SEM_INGEST = 10


def run_reset() -> None:
    """Delete all data from R2 and Vectorize."""
    print("Resetting: deleting all data from R2...")
    r2_count = delete_all_from_r2()
    print(f"  Deleted {r2_count} objects from R2")

    print("Resetting: deleting all vectors from Vectorize...")
    vec_count = delete_all_from_vectorize()
    print(f"  Deleted {vec_count} vectors from Vectorize")

    print("Reset complete.")


async def run_pipeline(
    max_books: int | None = None,
    dry_run: bool = False,
    output_dir: Path = OUTPUT_DIR,
    language: str | None = None,
    download_delay: float = 0.5,
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

    # Stage 1: Acquire (sync — one-time catalog fetch)
    print("Stage 1: Fetching OPDS catalog...")
    catalog = fetch_catalog()

    if language:
        catalog = [e for e in catalog if e.language.startswith(language)]

    if max_books is not None:
        catalog = catalog[:max_books]
    print(f"  Found {len(catalog)} books")

    # Create semaphores
    sem_book = asyncio.Semaphore(SEM_BOOK)
    sem_download = asyncio.Semaphore(SEM_DOWNLOAD)
    sem_r2 = asyncio.Semaphore(SEM_R2)
    sem_embed = asyncio.Semaphore(SEM_EMBED)
    sem_ingest = asyncio.Semaphore(SEM_INGEST)

    # Create shared S3 client once (skip for dry-run)
    s3_client = None
    if not dry_run:
        s3_client = _create_s3_client(
            os.environ["CF_ACCOUNT_ID"],
            os.environ["R2_ACCESS_KEY_ID"],
            os.environ["R2_SECRET_ACCESS_KEY"],
        )

    async def _process_book(
        i: int, total: int, entry: CatalogEntry,
    ) -> None:
        """Process a single book through the full pipeline."""
        async with sem_book:
            book_name = f"{entry.author} - {entry.title}"
            print(f"\n[{i + 1}/{total}] {book_name}")

            # Download
            filename = Path(urlparse(entry.epub_url).path).name
            epub_path = output_dir / filename
            async with sem_download:
                print(f"  Downloading EPUB... ({book_name})")
                await download_epub(entry.epub_url, epub_path, client=http_client)
                if download_delay > 0:
                    await asyncio.sleep(download_delay)

            # Extract (CPU-bound)
            print(f"  Extracting text... ({book_name})")
            extracted = await asyncio.to_thread(extract_book, str(epub_path))
            if not extracted.chapters:
                print(f"  Skipping: no chapters found ({book_name})")
                return

            # Store chapter texts in R2 and chunk in parallel
            async with sem_r2:
                print(f"  {'Uploading chapter texts to R2' if not dry_run else '[DRY RUN] Counting chapters for R2'}... ({book_name})")
                upload_coro = upload_to_r2(
                    extracted.chapters, extracted.book_id,
                    dry_run=dry_run, s3_client=s3_client,
                )
                chunk_coro = asyncio.to_thread(chunk_book, extracted)
                uploaded, chunks = await asyncio.gather(upload_coro, chunk_coro)
                print(f"  {'Uploaded' if not dry_run else 'Would upload'} {uploaded} chapters to R2 ({book_name})")

            print(f"  Created {len(chunks)} chunks ({book_name})")

            if dry_run:
                print(f"  [DRY RUN] Skipping embedding and ingestion ({book_name})")
                return

            # Embed
            async with sem_embed:
                print(f"  Generating embeddings... ({book_name})")
                texts = [c.text for c in chunks]
                embeddings = await generate_embeddings(
                    texts, client=http_client,
                )

            # Ingest
            async with sem_ingest:
                print(f"  Uploading to Vectorize... ({book_name})")
                await upload_to_vectorize(
                    chunks, embeddings, client=http_client,
                )

    async with httpx.AsyncClient() as http_client:
        tasks = [
            _process_book(i, len(catalog), entry)
            for i, entry in enumerate(catalog)
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

    # Report errors
    errors = [(i, r) for i, r in enumerate(results) if isinstance(r, Exception)]
    if errors:
        print(f"\n{len(errors)} book(s) failed:")
        for i, exc in errors:
            print(f"  [{i + 1}] {catalog[i].title}: {exc}")

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
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Delete all data from R2 and Vectorize before running",
    )
    parser.add_argument(
        "--download-delay",
        type=float,
        default=0.5,
        help="Delay in seconds between downloads (default: 0.5)",
    )
    args = parser.parse_args()

    if args.reset:
        if args.dry_run:
            print("Error: --reset cannot be used with --dry-run", file=sys.stderr)
            sys.exit(1)
        run_reset()

    asyncio.run(
        run_pipeline(
            max_books=args.max_books,
            dry_run=args.dry_run,
            output_dir=args.output_dir,
            language=args.language,
            download_delay=args.download_delay,
        )
    )


if __name__ == "__main__":
    main()
