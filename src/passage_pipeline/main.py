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
from passage_pipeline.models import CatalogEntry, slugify
from passage_pipeline.progress import ProgressTracker
from passage_pipeline.store import delete_all_from_r2, upload_to_r2, create_s3_client
from passage_pipeline._rate_limit import AsyncRateLimiter

# Concurrency limits
SEM_BOOK = 50
SEM_DOWNLOAD = 2
SEM_R2 = 20
SEM_EMBED = 30
SEM_INGEST = 10

_REQUIRED_ENV_VARS = ("CF_ACCOUNT_ID", "CF_API_TOKEN", "R2_ACCESS_KEY_ID", "R2_SECRET_ACCESS_KEY")

COMPLETED_FILE = Path(".completed")


def _load_completed(path: Path) -> set[str]:
    """Load processed book IDs from the completed file."""
    if not path.exists():
        return set()
    text = path.read_text()
    return {line for line in text.splitlines() if line}


def _mark_completed(path: Path, book_id: str) -> None:
    """Append a book ID to the completed file."""
    with path.open("a") as f:
        f.write(f"{book_id}\n")


def _check_env_vars() -> None:
    """Exit with an error if required environment variables are missing."""
    missing = [k for k in _REQUIRED_ENV_VARS if not os.environ.get(k)]
    if missing:
        print(
            f"Error: required environment variables not set: {', '.join(missing)}\n"
            "Copy .env.example to .env and fill in the values.",
            file=sys.stderr,
        )
        sys.exit(1)


def run_reset() -> None:
    """Delete all data from R2 and Vectorize."""
    _check_env_vars()

    r2_ok, vec_ok = False, False

    try:
        print("Resetting: deleting all data from R2...")
        r2_count = delete_all_from_r2()
        print(f"  Deleted {r2_count} objects from R2")
        r2_ok = True
    except Exception as e:
        print(f"  R2 deletion failed: {e}", file=sys.stderr)

    try:
        print("Resetting: deleting all vectors from Vectorize...")
        vec_count = delete_all_from_vectorize()
        print(f"  Deleted {vec_count} vectors from Vectorize")
        vec_ok = True
    except Exception as e:
        print(f"  Vectorize deletion failed: {e}", file=sys.stderr)

    if not (r2_ok and vec_ok):
        print("Reset incomplete. Re-run --reset to retry.", file=sys.stderr)
        sys.exit(1)

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
        _check_env_vars()

    # Stage 1: Acquire (sync — one-time catalog fetch)
    print("Stage 1: Fetching OPDS catalog...")
    catalog = fetch_catalog()

    if language:
        catalog = [e for e in catalog if e.language.startswith(language)]

    if max_books is not None:
        catalog = catalog[:max_books]
    print(f"  Found {len(catalog)} books")

    # Load completed books for resume support
    completed_path = output_dir / COMPLETED_FILE
    completed = _load_completed(completed_path)
    if completed:
        before = len(catalog)
        catalog = [
            e for e in catalog
            if slugify(f"{e.author}-{e.title}") not in completed
        ]
        skipped = before - len(catalog)
        if skipped:
            print(f"  Skipping {skipped} already-completed books")

    if not catalog:
        print("No books to process.")
        return

    # Create semaphores
    sem_book = asyncio.Semaphore(SEM_BOOK)
    sem_download = asyncio.Semaphore(SEM_DOWNLOAD)
    sem_r2 = asyncio.Semaphore(SEM_R2)
    sem_embed = asyncio.Semaphore(SEM_EMBED)
    sem_ingest = asyncio.Semaphore(SEM_INGEST)

    # Rate limiter for embed API calls
    rate_limiter = AsyncRateLimiter(max_per_second=50)

    # Create shared S3 client once (skip for dry-run)
    s3_client = None
    if not dry_run:
        s3_client = create_s3_client(
            os.environ["CF_ACCOUNT_ID"],
            os.environ["R2_ACCESS_KEY_ID"],
            os.environ["R2_SECRET_ACCESS_KEY"],
        )

    with ProgressTracker(len(catalog), dry_run=dry_run) as tracker:

        async def _process_book(
            i: int, total: int, entry: CatalogEntry,
        ) -> None:
            """Process a single book through the full pipeline."""
            async with sem_book:
                book_name = f"{entry.author} - {entry.title}"
                book_id = slugify(f"{entry.author}-{entry.title}")
                tracker.log(f"[{i + 1}/{total}] {book_name}")

                # Download
                filename = Path(urlparse(entry.epub_url).path).name
                epub_path = output_dir / filename
                async with sem_download:
                    await download_epub(entry.epub_url, epub_path, client=http_client)
                    if download_delay > 0:
                        await asyncio.sleep(download_delay)
                tracker.advance("download")

                # Extract (CPU-bound)
                extracted = await asyncio.to_thread(extract_book, str(epub_path))
                tracker.advance("extract")

                if not extracted.chapters:
                    tracker.log(f"  Skipping: no chapters found ({book_name})")
                    # Advance remaining stages to keep counts consistent
                    for stage in ("r2", "chunk", "embed", "ingest"):
                        tracker.advance(stage)
                    _mark_completed(completed_path, book_id)
                    return

                # Store chapter texts in R2 and chunk in parallel
                async with sem_r2:
                    upload_coro = upload_to_r2(
                        extracted.chapters, extracted.book_id,
                        dry_run=dry_run, s3_client=s3_client,
                    )
                    chunk_coro = asyncio.to_thread(chunk_book, extracted)
                    uploaded, chunks = await asyncio.gather(upload_coro, chunk_coro)
                tracker.advance("r2")
                tracker.advance("chunk")

                if dry_run:
                    tracker.log(f"  [DRY RUN] {len(chunks)} chunks ({book_name})")
                    _mark_completed(completed_path, book_id)
                    return

                # Embed
                async with sem_embed:
                    texts = [c.text for c in chunks]
                    embeddings = await generate_embeddings(
                        texts, client=http_client,
                        rate_limiter=rate_limiter,
                    )
                tracker.advance("embed")

                # Ingest
                async with sem_ingest:
                    await upload_to_vectorize(
                        chunks, embeddings, client=http_client,
                    )
                tracker.advance("ingest")

                _mark_completed(completed_path, book_id)

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
