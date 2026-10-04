"""Fetcher for the Greenhouse Job Board public API.

Docs: https://developers.greenhouse.io/job-board.html
Endpoint: https://boards-api.greenhouse.io/v1/boards/{board_token}/jobs
"""

from __future__ import annotations

import httpx

from ..models import Job
from .base import Fetcher


class GreenhouseFetcher(Fetcher):
    source = "greenhouse"

    BASE_URL = "https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"

    def fetch(self, company_name: str, slug: str, tier: int) -> list[Job]:
        url = self.BASE_URL.format(slug=slug)
        try:
            response = self.client.get(url)
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Greenhouse fetch failed for {company_name} ({slug}): {exc}"
            ) from exc

        payload = response.json()
        jobs = payload.get("jobs", [])

        return [self._to_job(company_name, tier, raw) for raw in jobs]

    def _to_job(self, company_name: str, tier: int, raw: dict) -> Job:
        location = (raw.get("location") or {}).get("name") or "Unknown"
        departments = raw.get("departments") or []
        department = departments[0].get("name") if departments else None

        return Job(
            source=self.source,
            company=company_name,
            external_id=str(raw["id"]),
            title=raw.get("title", "").strip(),
            location=location.strip(),
            url=raw.get("absolute_url", ""),
            tier=tier,
            department=department,
            posted_at=raw.get("updated_at"),
        )
