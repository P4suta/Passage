from __future__ import annotations

from typing import Self

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    TextColumn,
    TimeElapsedColumn,
)

STAGES = ("download", "extract", "r2", "chunk", "embed", "ingest")
STAGE_LABELS = {
    "download": "Download",
    "extract": "Extract",
    "r2": "R2 Upload",
    "chunk": "Chunk",
    "embed": "Embed",
    "ingest": "Ingest",
}

_DRY_RUN_SKIP = {"embed", "ingest"}


class ProgressTracker:
    """Rich progress bar tracker for the pipeline stages."""

    def __init__(self, total: int, *, dry_run: bool = False, console: Console | None = None) -> None:
        kwargs: dict = {}
        if console is not None:
            kwargs["console"] = console

        self._progress = Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            MofNCompleteColumn(),
            TimeElapsedColumn(),
            **kwargs,
        )
        self._final_stage = "chunk" if dry_run else "ingest"
        self._task_ids: dict[str, int] = {}

        self._overall_id = self._progress.add_task(
            f"Passage Pipeline — {total} books", total=total,
        )
        for stage in STAGES:
            if dry_run and stage in _DRY_RUN_SKIP:
                continue
            tid = self._progress.add_task(f"  {STAGE_LABELS[stage]}", total=total)
            self._task_ids[stage] = tid

    def __enter__(self) -> Self:
        self._progress.__enter__()
        return self

    def __exit__(self, *exc: object) -> None:
        self._progress.__exit__(*exc)

    def advance(self, stage: str) -> None:
        """Advance a stage task by 1. Also advances overall if this is the final stage."""
        if stage in self._task_ids:
            self._progress.advance(self._task_ids[stage])
        if stage == self._final_stage:
            self._progress.advance(self._overall_id)

    def log(self, message: str) -> None:
        """Print a message above the progress bars."""
        self._progress.console.print(message)
