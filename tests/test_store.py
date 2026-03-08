import boto3
from moto import mock_aws

from passage_pipeline.models import Chapter
from passage_pipeline.store import upload_to_r2, _safe_name


class TestSafeName:
    def test_lowercase_and_strip_special(self):
        assert _safe_name("The Great Gatsby") == "thegreatgatsby"

    def test_preserves_hyphens(self):
        assert _safe_name("chapter-one") == "chapter-one"

    def test_removes_unicode(self):
        assert _safe_name("Héllo Wörld") == "hllowrld"

    def test_keeps_numbers(self):
        assert _safe_name("Chapter 42") == "chapter42"

    def test_empty_string(self):
        assert _safe_name("") == ""


BUCKET = "passage-texts"


def _make_chapters(*titles_and_texts):
    return [
        Chapter(title=t, text=txt, index=i)
        for i, (t, txt) in enumerate(titles_and_texts)
    ]


@mock_aws
class TestUploadToR2:
    def _setup(self):
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket=BUCKET)
        return s3

    def test_upload_chapters(self):
        s3 = self._setup()
        chapters = _make_chapters(
            ("Chapter One", "Hello world"),
            ("Chapter Two", "Goodbye world"),
        )

        count = upload_to_r2(
            chapters,
            book_id="the-great-gatsby",
            bucket_name=BUCKET,
            s3_client=s3,
        )

        assert count == 2
        obj = s3.get_object(Bucket=BUCKET, Key="the-great-gatsby/chapterone.txt")
        assert obj["Body"].read().decode() == "Hello world"

    def test_skips_empty_chapters(self):
        s3 = self._setup()
        chapters = _make_chapters(
            ("Chapter One", "Hello"),
            ("Chapter Two", "   "),
            ("Chapter Three", ""),
        )

        count = upload_to_r2(
            chapters,
            book_id="test-book",
            bucket_name=BUCKET,
            s3_client=s3,
        )

        assert count == 1

    def test_empty_title_uses_chapter_index(self):
        s3 = self._setup()
        chapters = _make_chapters(("", "Some text"),)

        upload_to_r2(
            chapters,
            book_id="test-book",
            bucket_name=BUCKET,
            s3_client=s3,
        )

        obj = s3.get_object(Bucket=BUCKET, Key="test-book/chapter-0.txt")
        assert obj["Body"].read().decode() == "Some text"

    def test_key_format_matches_api(self):
        """Keys should match R2TextStorageAdapter's format."""
        s3 = self._setup()
        chapters = _make_chapters(("The Beginning!", "text"),)

        upload_to_r2(
            chapters,
            book_id="Jane Austen: Pride & Prejudice",
            bucket_name=BUCKET,
            s3_client=s3,
        )

        # API: bookId.replace(/[^a-z0-9-]/g, "")
        obj = s3.get_object(
            Bucket=BUCKET,
            Key="janeaustenprideprejudice/thebeginning.txt",
        )
        assert obj["Body"].read().decode() == "text"


class TestDryRun:
    def test_dry_run_returns_count_without_upload(self):
        """dry_run=True ではS3に何もアップロードしない"""
        chapters = _make_chapters(("Ch1", "text1"), ("Ch2", "text2"))
        count = upload_to_r2(
            chapters, book_id="test", dry_run=True,
        )
        assert count == 2

    def test_dry_run_skips_empty_chapters(self):
        """dry_run でも空チャプターはスキップする"""
        chapters = _make_chapters(("Ch1", "hello"), ("Ch2", "  "))
        count = upload_to_r2(
            chapters, book_id="test", dry_run=True,
        )
        assert count == 1

    def test_dry_run_no_s3_calls(self):
        """dry_run=True のとき put_object が呼ばれない"""
        from unittest.mock import MagicMock
        mock_s3 = MagicMock()
        chapters = _make_chapters(("Ch1", "text"),)
        upload_to_r2(
            chapters, book_id="test", dry_run=True, s3_client=mock_s3,
        )
        mock_s3.put_object.assert_not_called()
