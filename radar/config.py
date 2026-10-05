"""Config loading from targets.yaml and queries.yaml."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class CompanyConfig:
    name: str
    source: str
    slug: str
    tier: int = 2


@dataclass
class QueryConfig:
    """A saved aggregator search (e.g. against RemoteRocketship)."""

    name: str
    filters: dict[str, Any]
    tier: int = 2
    max_pages: int = 3


def load_targets(path: str | Path = "targets.yaml") -> list[CompanyConfig]:
    """Parse targets.yaml into typed CompanyConfig objects."""
    path = Path(path)
    data = yaml.safe_load(path.read_text())
    companies = data.get("companies", [])

    out: list[CompanyConfig] = []
    for entry in companies:
        out.append(
            CompanyConfig(
                name=entry["name"],
                source=entry["source"],
                slug=entry["slug"],
                tier=int(entry.get("tier", 2)),
            )
        )
    return out


def load_queries(path: str | Path = "queries.yaml") -> list[QueryConfig]:
    """Parse queries.yaml into typed QueryConfig objects. Missing file -> []."""
    path = Path(path)
    if not path.exists():
        return []

    data = yaml.safe_load(path.read_text()) or {}
    queries = data.get("queries", [])

    out: list[QueryConfig] = []
    for entry in queries:
        out.append(
            QueryConfig(
                name=entry["name"],
                filters=dict(entry.get("filters", {})),
                tier=int(entry.get("tier", 2)),
                max_pages=int(entry.get("max_pages", 3)),
            )
        )
    return out
