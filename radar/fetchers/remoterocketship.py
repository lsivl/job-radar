"""Fetcher for the RemoteRocketship Jobs API (aggregator, not a single-company ATS).

Unlike the other fetchers, this isn't keyed by a company slug — it runs
saved searches (queries.yaml) against a cross-company job feed. Requires
REMOTEROCKETSHIP_API_KEY (Advanced plan) in .env; callers should treat a
missing key as "feature disabled", not an error.

Docs: https://www.remoterocketship.com/api-docs/
Quota: 500 requests or 3000 returned jobs per UTC day, whichever hits first.
"""

from __future__ import annotations

import httpx

from ..config import QueryConfig
from ..models import Job

BASE_URL = "https://www.remoterocketship.com/api/openclaw/jobs/"


def _to_job(tier: int, raw: dict) -> Job:
    company = raw.get("company") or {}
    salary = raw.get("salaryRange")
    salary_text = salary.get("salaryHumanReadableText") if isinstance(salary, dict) else None

    return Job(
        source="remoterocketship",
        company=company.get("name") or "Unknown",
        external_id=str(raw.get("id")),
        title=(raw.get("roleTitle") or "").strip(),
        location="Remote",  # queries are remote-only; see filters in queries.yaml
        url=raw.get("url") or "",
        tier=tier,
        posted_at=raw.get("created_at"),
        salary_range=salary_text,
        tech_stack=list(raw.get("techStack") or []),
        sponsors_h1b=company.get("sponsorsH1B"),
    )


def run_query(client: httpx.Client, query: QueryConfig) -> list[Job]:
    """Page through a single saved search, up to query.max_pages."""
    jobs: list[Job] = []
    page = 1

    while page <= query.max_pages:
        body = {
            "filters": {**query.filters, "page": page},
            "includeJobDescription": False,
        }
        response = client.post(BASE_URL, json=body)

        if response.status_code == 429:
            # Daily quota hit — stop gracefully, keep whatever we already collected.
            break
        response.raise_for_status()

        data = response.json()
        openings = data.get("jobOpenings", [])
        jobs.extend(_to_job(query.tier, raw) for raw in openings)

        if not data.get("pagination", {}).get("hasNextPage"):
            break
        page += 1

    return jobs


def fetch_all(api_key: str, queries: list[QueryConfig]) -> list[Job]:
    """Run every saved query and return the combined, de-duplicated job list."""
    if not queries:
        return []

    client = httpx.Client(
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "User-Agent": "job-radar/0.1 (+https://github.com/lsivl/job-radar)",
        },
        timeout=httpx.Timeout(20.0, connect=5.0),
        follow_redirects=True,
    )

    all_jobs: list[Job] = []
    seen: set[str] = set()
    try:
        for query in queries:
            try:
                for job in run_query(client, query):
                    if job.dedup_key in seen:
                        continue
                    seen.add(job.dedup_key)
                    all_jobs.append(job)
            except httpx.HTTPError as exc:
                print(f"  ⚠️  RemoteRocketship query '{query.name}' failed: {exc}")
    finally:
        client.close()

    return all_jobs
