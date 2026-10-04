"""ATS fetchers registry."""

from .ashby import AshbyFetcher
from .base import Fetcher
from .greenhouse import GreenhouseFetcher
from .lever import LeverFetcher
from .workable import WorkableFetcher

REGISTRY: dict[str, type[Fetcher]] = {
    "greenhouse": GreenhouseFetcher,
    "lever": LeverFetcher,
    "ashby": AshbyFetcher,
    "workable": WorkableFetcher,
}


def get_fetcher(source: str) -> Fetcher:
    """Instantiate a fetcher by its ATS source key."""
    if source not in REGISTRY:
        raise ValueError(
            f"Unknown source '{source}'. Supported: {sorted(REGISTRY)}"
        )
    return REGISTRY[source]()


__all__ = [
    "Fetcher",
    "GreenhouseFetcher",
    "LeverFetcher",
    "AshbyFetcher",
    "WorkableFetcher",
    "REGISTRY",
    "get_fetcher",
]
