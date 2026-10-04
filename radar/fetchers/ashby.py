"""Fetcher for the Ashby public job board API.

Endpoint: https://api.ashbyhq.com/posting-api/job-board/{slug}
"""

from __future__ import annotations

import httpx

from ..models import Job
from .base import Fetcher


class AshbyFetcher(Fetcher):
    source = "ashby"

    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board/{slug}"

    def fetch(self, company_name: str, slug: str, tier: int) -> list[Job]:
        url = self.BASE_URL.format(slug=slug)
        try:
            response = self.client.get(url, params={"includeCompensation": "true"})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Ashby fetch failed for {company_name} ({slug}): {exc}"
            ) from exc

        payload = response.json()
        jobs = payload.get("jobs", [])

        return [self._to_job(company_name, tier, raw) for raw in jobs]

    def _to_job(self, company_name: str, tier: int, raw: dict) -> Job:
        return Job(
            source=self.source,
            company=company_name,
            external_id=str(raw.get("id")),
            title=(raw.get("title") or "").strip(),
            location=(raw.get("location") or "Unknown").strip(),
            url=raw.get("jobUrl") or raw.get("applyUrl") or "",
            tier=tier,
            department=raw.get("departmentName"),
            posted_at=raw.get("publishedAt") or raw.get("updatedAt"),
        )
