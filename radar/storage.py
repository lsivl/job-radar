"""Snapshot persistence for daily diffing.

Each run writes a dated JSON snapshot into snapshots/.
Phase 2 diffing compares today's snapshot with the previous one
to isolate newly posted roles.
"""

from __future__ import annotations

import json
from datetime import date
from pathlib import Path

from .models import Job

SNAPSHOT_DIR = Path("snapshots")


def _snapshot_path(day: date) -> Path:
    return SNAPSHOT_DIR / f"{day.isoformat()}.json"


def save_snapshot(jobs: list[Job], day: date | None = None) -> Path:
    """Write a snapshot of the current open-job inventory."""
    day = day or date.today()
    SNAPSHOT_DIR.mkdir(exist_ok=True)
    path = _snapshot_path(day)
    payload = {
        "date": day.isoformat(),
        "count": len(jobs),
        "jobs": [job.to_dict() for job in jobs],
    }
    path.write_text(json.dumps(payload, indent=2, sort_keys=True))
    return path


def load_snapshot(day: date) -> list[Job] | None:
    """Return the jobs recorded on the given day, or None if no snapshot."""
    path = _snapshot_path(day)
    if not path.exists():
        return None
    data = json.loads(path.read_text())
    return [Job.from_dict(entry) for entry in data.get("jobs", [])]


def latest_snapshot_before(day: date) -> tuple[date, list[Job]] | None:
    """Find the most recent snapshot strictly earlier than `day`."""
    if not SNAPSHOT_DIR.exists():
        return None

    candidates = sorted(
        (p for p in SNAPSHOT_DIR.glob("*.json")),
        reverse=True,
    )
    for path in candidates:
        try:
            snapshot_day = date.fromisoformat(path.stem)
        except ValueError:
            continue
        if snapshot_day >= day:
            continue
        jobs = [Job.from_dict(entry) for entry in json.loads(path.read_text()).get("jobs", [])]
        return snapshot_day, jobs

    return None
