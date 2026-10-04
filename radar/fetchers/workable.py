"""Fetcher for the Workable public job board API.

Endpoint: https://apply.workable.com/api/v3/accounts/{slug}/jobs
"""

from __future__ import annotations

import httpx

from ..models import Job
from .base import Fetcher


class WorkableFetcher(Fetcher):
    source = "workable"

    BASE_URL = "https://apply.workable.com/api/v3/accounts/{slug}/jobs"

    def fetch(self, company_name: str, slug: str, tier: int) -> list[Job]:
        url = self.BASE_URL.format(slug=slug)
        try:
            response = self.client.post(url, json={"query": "", "location": {}})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Workable fetch failed for {company_name} ({slug}): {exc}"
            ) from exc

        payload = response.json()
        results = payload.get("results", [])

        return [self._to_job(company_name, tier, raw) for raw in results]

    def _to_job(self, company_name: str, tier: int, raw: dict) -> Job:
        location = raw.get("location") or {}
        location_str = (
            location.get("city")
            or location.get("country")
            or location.get("location_str")
            or "Unknown"
        )

        shortcode = raw.get("shortcode") or raw.get("id")
        public_url = raw.get("url") or f"https://apply.workable.com/{raw.get('company', {}).get('name', '')}/j/{shortcode}/"

        return Job(
            source=self.source,
            company=company_name,
            external_id=str(shortcode),
            title=(raw.get("title") or "").strip(),
            location=str(location_str).strip(),
            url=public_url,
            tier=tier,
            department=raw.get("department"),
            posted_at=raw.get("published_on") or raw.get("created_at"),
        )
