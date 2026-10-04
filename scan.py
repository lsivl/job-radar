"""Daily scanner entry point.

Phase 1 scope:
    * Load target companies from targets.yaml
    * Fetch open jobs from each company's ATS
    * Print a summary table so we can see the pipeline is alive

Later phases will add diffing, LLM scoring, and Telegram delivery.
"""

from __future__ import annotations

import sys
from collections import defaultdict

from radar.config import load_targets
from radar.fetchers import get_fetcher
from radar.models import Job
from radar.storage import save_snapshot


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

    snapshot_path = save_snapshot(jobs)
    print(f"\n💾  Snapshot saved: {snapshot_path}")
    print("\n✅  Phase 1 complete: fetchers + snapshotting working.\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
