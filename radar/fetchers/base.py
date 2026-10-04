"""Base interface and shared helpers for ATS fetchers."""

from __future__ import annotations

from abc import ABC, abstractmethod

import httpx

from ..models import Job


class Fetcher(ABC):
    """Each ATS platform implements a Fetcher subclass."""

    source: str  # e.g. "greenhouse"

    def __init__(self, client: httpx.Client | None = None) -> None:
        self.client = client or httpx.Client(
            timeout=httpx.Timeout(15.0, connect=5.0),
            headers={
                "User-Agent": "job-radar/0.1 (+https://github.com/lsivl/job-radar)",
                "Accept": "application/json",
            },
            follow_redirects=True,
        )

    @abstractmethod
    def fetch(self, company_name: str, slug: str, tier: int) -> list[Job]:
        """Return the current list of open jobs for the given company."""
