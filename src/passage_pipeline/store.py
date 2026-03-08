import os
import re

import boto3

from passage_pipeline.models import Chapter


def _safe_name(s: str) -> str:
    """Sanitize a string to match the API's key format.

    Matches R2TextStorageAdapter: replace(/[^a-z0-9-]/g, "")
    """
    return re.sub(r"[^a-z0-9-]", "", s.lower())


def _create_s3_client(
    account_id: str,
    access_key_id: str,
    secret_access_key: str,
):
    """Create a boto3 S3 client configured for Cloudflare R2."""
    return boto3.client(
        "s3",
        endpoint_url=f"https://{account_id}.r2.cloudflarestorage.com",
        aws_access_key_id=access_key_id,
        aws_secret_access_key=secret_access_key,
        region_name="auto",
    )


def upload_to_r2(
    chapters: list[Chapter],
    book_id: str,
    account_id: str | None = None,
    access_key_id: str | None = None,
    secret_access_key: str | None = None,
    bucket_name: str = "passage-texts",
    *,
    dry_run: bool = False,
    s3_client=None,
) -> int:
    """Upload chapter texts to R2 via S3-compatible API.

    Returns the number of chapters uploaded (or would-be-uploaded in dry-run).
    """
    if s3_client is None and not dry_run:
        account_id = account_id or os.environ["CF_ACCOUNT_ID"]
        access_key_id = access_key_id or os.environ["R2_ACCESS_KEY_ID"]
        secret_access_key = secret_access_key or os.environ["R2_SECRET_ACCESS_KEY"]
        s3_client = _create_s3_client(account_id, access_key_id, secret_access_key)

    safe_book_id = _safe_name(book_id)
    uploaded = 0

    for chapter in chapters:
        if not chapter.text.strip():
            continue

        safe_chapter = _safe_name(chapter.title)
        if not safe_chapter:
            safe_chapter = f"chapter-{chapter.index}"

        key = f"{safe_book_id}/{safe_chapter}.txt"

        if not dry_run:
            s3_client.put_object(
                Bucket=bucket_name,
                Key=key,
                Body=chapter.text.encode("utf-8"),
                ContentType="text/plain; charset=utf-8",
            )
        uploaded += 1

    return uploaded
