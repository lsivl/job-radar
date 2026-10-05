"""Daily scanner entry point.

Pipeline:
    1. Load target companies from targets.yaml
    2. Fetch open jobs from each company's ATS
    3. Save today's snapshot (so tomorrow has something to diff against)
    4. Diff against the most recent prior snapshot -> newly posted jobs
    5. Score the new jobs with Claude against the candidate rubric
    6. Push a Telegram digest of anything that clears the bar

GitHub Actions cron (Phase 4) will call this on a daily schedule.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from datetime import date

from dotenv import load_dotenv

from radar.config import load_targets
from radar.delivery import send_digest
from radar.diff import new_jobs_since_last_snapshot
from radar.fetchers import get_fetcher
from radar.models import Job
from radar.scorer import score_jobs
from radar.storage import save_snapshot

load_dotenv()


def scan_all() -> list[Job]:
    """Fetch open jobs for every company in targets.yaml."""
    targets = load_targets()
    all_jobs: list[Job] = []
    errors: list[str] = []

    print(f"\n🔍 Scanning {len(targets)} target companies...\n")

    for company in targets:
        try:
            fetcher = get_fetcher(company.source)
            jobs = fetcher.fetch(company.name, company.slug, company.tier)
            all_jobs.extend(jobs)
            tier_badge = "⭐" * company.tier
            print(f"  ✅  {company.name:<16} {tier_badge:<4} ({company.source:<10}) → {len(jobs):>3} jobs")
        except Exception as exc:  # noqa: BLE001 — surface all errors
            errors.append(f"{company.name} ({company.source}): {exc}")
            print(f"  ❌  {company.name:<16} ERROR: {exc}")

    if errors:
        print(f"\n⚠️  {len(errors)} companies failed:")
        for err in errors:
            print(f"     - {err}")

    return all_jobs


def print_summary(jobs: list[Job]) -> None:
    """Dump quick stats for sanity checking."""
    print(f"\n📊 Total jobs collected: {len(jobs)}")

    by_company: dict[str, int] = defaultdict(int)
    for job in jobs:
        by_company[job.company] += 1

    print("\n🏢 Jobs per company:")
    for company, count in sorted(by_company.items(), key=lambda x: -x[1]):
        print(f"     {company:<16} {count:>3}")

    # Spot-check a few titles to make sure parsing is sane.
    print("\n🧪 Sample titles (first 5):")
    for job in jobs[:5]:
        print(f"     [{job.company}] {job.title} — {job.location}")


def main() -> int:
    jobs = scan_all()
    print_summary(jobs)

    if not jobs:
        print("\n❌  No jobs collected — check network / slugs in targets.yaml")
        return 1

    today = date.today()
    snapshot_path = save_snapshot(jobs, today)
    print(f"\n💾  Snapshot saved: {snapshot_path}")

    new_jobs = new_jobs_since_last_snapshot(jobs, today)
    print(f"\n🆕  {len(new_jobs)} new job(s) since the previous snapshot")

    scored = score_jobs(new_jobs)
    hits = [s for s in scored if s.dream_match or s.score >= 7]
    if scored:
        print(f"🧠  Scored {len(scored)} new job(s) — {len(hits)} cleared the ≥7/10 or dream-match bar")

    send_digest(scored)
    print("\n✅  Pipeline complete: fetch + diff + score + digest.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
