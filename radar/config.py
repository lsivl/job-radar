"""Config loading from targets.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml


@dataclass
class CompanyConfig:
    name: str
    source: str
    slug: str
    tier: int = 2


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
