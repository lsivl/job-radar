"""Claude-based scoring of newly posted jobs against the candidate rubric.

Only called on the (small) set of newly diffed jobs each day — that keeps
API spend trivial (see README cost estimate).
"""

from __future__ import annotations

import json
import os

from anthropic import Anthropic

from .models import Job, ScoredJob
from .rubric import build_prompt

# Haiku is plenty for this classification task and keeps monthly cost ~$1.
MODEL = "claude-haiku-4-5-20251001"


def _job_summary(job: Job) -> str:
    return (
        f"- Company: {job.company} (tier {job.tier} on the target list, "
        f"1 = dream, 3 = watch)\n"
        f"- Role title: {job.title}\n"
        f"- Department: {job.department or 'n/a'}\n"
        f"- Location: {job.location}\n"
        f"- Source: {job.source}\n"
        f"- URL: {job.url}"
    )


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        # Strip a ```json ... ``` fence if Claude adds one despite instructions.
        text = text.strip("`")
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            text = rest if first_line.strip().lower() in ("json", "") else text
    return json.loads(text)


def score_job(client: Anthropic, job: Job) -> ScoredJob:
    prompt = build_prompt(_job_summary(job))
    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        messages=[{"role": "user", "content": prompt}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    data = _parse_json(text)

    return ScoredJob(
        job=job,
        score=int(data["score"]),
        confidence=int(data["confidence"]),
        dream_match=bool(data["dream_match"]),
        reasons=[str(r) for r in data.get("reasons", [])],
        concerns=[str(c) for c in data.get("concerns", [])],
        suggested_action=str(data.get("suggested_action", "")),
    )


def score_jobs(jobs: list[Job]) -> list[ScoredJob]:
    """Score every job, skipping (and logging) any that fail individually."""
    if not jobs:
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set — copy .env.example to .env and fill it in."
        )

    client = Anthropic(api_key=api_key)
    scored: list[ScoredJob] = []
    for job in jobs:
        try:
            scored.append(score_job(client, job))
        except Exception as exc:  # noqa: BLE001 — one bad job shouldn't kill the run
            print(f"  ⚠️  Scoring failed for {job.company} — {job.title}: {exc}")
    return scored
