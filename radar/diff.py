"""Diff engine: isolate newly posted jobs since the previous snapshot."""

from __future__ import annotations

from datetime import date

from .models import Job
from .storage import latest_snapshot_before


def new_jobs_since_last_snapshot(today_jobs: list[Job], today: date | None = None) -> list[Job]:
    """Return jobs present today but absent from the most recent prior snapshot.

    On the very first run there is no prior snapshot, so everything counts as
    new — callers should expect (and tolerate) a large one-time backlog.
    """
    today = today or date.today()
    previous = latest_snapshot_before(today)

    if previous is None:
        return list(today_jobs)

    _, previous_jobs = previous
    seen = {job.dedup_key for job in previous_jobs}
    return [job for job in today_jobs if job.dedup_key not in seen]
