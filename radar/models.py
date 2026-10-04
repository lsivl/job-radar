"""Shared data models used across fetchers, scorer and delivery."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass
class Job:
    """Normalized representation of a single open role across ATS platforms."""

    source: str  # "greenhouse" | "lever" | "ashby" | "workable"
    company: str  # Display name, e.g. "Monzo"
    external_id: str  # ATS-provided unique id
    title: str
    location: str
    url: str
    tier: int = 2
    department: str | None = None
    posted_at: str | None = None  # ISO-8601 if available
    description: str | None = None  # Full JD text, filled lazily for scoring

    @property
    def dedup_key(self) -> str:
        """Stable identifier used across daily snapshots."""
        return f"{self.source}:{self.company}:{self.external_id}"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Job":
        return cls(**data)


@dataclass
class ScoredJob:
    """A job plus the LLM scoring verdict."""

    job: Job
    score: int  # 0-10
    confidence: int  # 0-10
    dream_match: bool
    reasons: list[str] = field(default_factory=list)
    concerns: list[str] = field(default_factory=list)
    suggested_action: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "job": self.job.to_dict(),
            "score": self.score,
            "confidence": self.confidence,
            "dream_match": self.dream_match,
            "reasons": self.reasons,
            "concerns": self.concerns,
            "suggested_action": self.suggested_action,
        }
