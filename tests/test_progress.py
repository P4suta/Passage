import io

from rich.console import Console

from passage_pipeline.progress import ProgressTracker, STAGES, _DRY_RUN_SKIP


def _make_tracker(total: int = 5, *, dry_run: bool = False) -> ProgressTracker:
    """Create a ProgressTracker with a captured console for testing."""
    console = Console(file=io.StringIO(), force_terminal=True)
    return ProgressTracker(total, dry_run=dry_run, console=console)


class TestProgressTracker:
    def test_context_manager(self):
        tracker = _make_tracker()
        with tracker:
            pass  # should not raise

    def test_advance_all_stages(self):
        total = 3
        tracker = _make_tracker(total)
        with tracker:
            for _ in range(total):
                for stage in STAGES:
                    tracker.advance(stage)

            # overall should be complete (ingest is final stage)
            overall = tracker._progress.tasks[0]
            assert overall.completed == total

    def test_advance_updates_stage_task(self):
        tracker = _make_tracker(total=5)
        with tracker:
            tracker.advance("download")
            tracker.advance("download")
            download_task = tracker._progress.tasks[tracker._task_ids["download"]]
            assert download_task.completed == 2

    def test_advance_final_stage_advances_overall(self):
        tracker = _make_tracker(total=5)
        with tracker:
            tracker.advance("ingest")
            overall = tracker._progress.tasks[0]
            assert overall.completed == 1

    def test_advance_non_final_does_not_advance_overall(self):
        tracker = _make_tracker(total=5)
        with tracker:
            tracker.advance("download")
            overall = tracker._progress.tasks[0]
            assert overall.completed == 0

    def test_advance_skipped_stages_for_no_chapters(self):
        """Advancing remaining stages individually keeps counts consistent."""
        tracker = _make_tracker(total=5)
        with tracker:
            # Simulate: download and extract done, then skip remaining
            tracker.advance("download")
            tracker.advance("extract")
            for stage in ("r2", "chunk", "embed", "ingest"):
                tracker.advance(stage)

            # Each stage advanced exactly once
            for stage in STAGES:
                task = tracker._progress.tasks[tracker._task_ids[stage]]
                assert task.completed == 1
            # Overall advanced once (via ingest)
            overall = tracker._progress.tasks[0]
            assert overall.completed == 1

    def test_dry_run_omits_embed_ingest(self):
        tracker = _make_tracker(total=5, dry_run=True)
        with tracker:
            for stage in _DRY_RUN_SKIP:
                assert stage not in tracker._task_ids
            # remaining stages should be present
            for stage in STAGES:
                if stage not in _DRY_RUN_SKIP:
                    assert stage in tracker._task_ids

    def test_dry_run_final_stage_is_chunk(self):
        tracker = _make_tracker(total=3, dry_run=True)
        with tracker:
            tracker.advance("chunk")
            overall = tracker._progress.tasks[0]
            assert overall.completed == 1

    def test_dry_run_advance_skipped_stages_ignored(self):
        """In dry-run, advancing embed/ingest is silently ignored."""
        tracker = _make_tracker(total=3, dry_run=True)
        with tracker:
            tracker.advance("embed")
            tracker.advance("ingest")
            # No embed/ingest task ids, so nothing should crash
            assert "embed" not in tracker._task_ids
            assert "ingest" not in tracker._task_ids

    def test_log_outputs_message(self):
        buf = io.StringIO()
        console = Console(file=buf, force_terminal=True)
        tracker = ProgressTracker(5, console=console)
        with tracker:
            tracker.log("test message")
        output = buf.getvalue()
        assert "test message" in output

    def test_no_skip_method(self):
        """skip() was removed — ensure it doesn't exist."""
        tracker = _make_tracker()
        assert not hasattr(tracker, "skip")
