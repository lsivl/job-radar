"""Fetcher for the Lever public postings API.

Endpoint: https://api.lever.co/v0/postings/{slug}?mode=json
"""

from __future__ import annotations

import httpx

from ..models import Job
from .base import Fetcher


class LeverFetcher(Fetcher):
    source = "lever"

    BASE_URL = "https://api.lever.co/v0/postings/{slug}"

    def fetch(self, company_name: str, slug: str, tier: int) -> list[Job]:
        url = self.BASE_URL.format(slug=slug)
        try:
            response = self.client.get(url, params={"mode": "json"})
            response.raise_for_status()
        except httpx.HTTPError as exc:
            raise RuntimeError(
                f"Lever fetch failed for {company_name} ({slug}): {exc}"
            ) from exc

        postings = response.json()
        if not isinstance(postings, list):
            return []

        return [self._to_job(company_name, tier, raw) for raw in postings]

    def _to_job(self, company_name: str, tier: int, raw: dict) -> Job:
        categories = raw.get("categories") or {}
        location = categories.get("location") or categories.get("allLocations", ["Unknown"])
        if isinstance(location, list):
            location = ", ".join(location) if location else "Unknown"

        posted_at = raw.get("createdAt")
        # Lever returns an epoch millis int, convert to ISO string if present.
        if isinstance(posted_at, int):
            from datetime import datetime, timezone

            posted_at = datetime.fromtimestamp(posted_at / 1000, tz=timezone.utc).isoformat()

        return Job(
            source=self.source,
            company=company_name,
            external_id=str(raw.get("id")),
            title=(raw.get("text") or "").strip(),
            location=str(location).strip(),
            url=raw.get("hostedUrl") or raw.get("applyUrl") or "",
            tier=tier,
            department=categories.get("team") or categories.get("department"),
            posted_at=posted_at,
        )
