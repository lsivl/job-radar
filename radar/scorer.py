"""Claude-based scoring of newly posted jobs against the candidate rubric.

Only called on the (small, usually) set of newly diffed jobs each day —
that keeps API spend trivial (see README cost estimate). Scored
concurrently via a thread pool since each call is latency-bound, not
CPU-bound: on a one-time backlog flush (e.g. adding new target companies)
this is the difference between ~40 minutes and ~2 minutes.
"""

from __future__ import annotations

import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed

from anthropic import Anthropic

from .models import Job, ScoredJob
from .rubric import build_prompt

# Haiku is plenty for this classification task and keeps monthly cost ~$1.
MODEL = "claude-haiku-4-5-20251001"
MAX_WORKERS = 10


def _job_summary(job: Job) -> str:
    lines = [
        f"- Company: {job.company} (tier {job.tier} on the target list, "
        f"1 = dream, 3 = watch)",
        f"- Role title: {job.title}",
        f"- Department: {job.department or 'n/a'}",
        f"- Location: {job.location}",
        f"- Source: {job.source}",
        f"- URL: {job.url}",
    ]
    if job.salary_range:
        lines.append(f"- Salary: {job.salary_range}")
    if job.tech_stack:
        lines.append(f"- Tech stack: {', '.join(job.tech_stack)}")
    if job.description:
        lines.append(f"- Description excerpt:\n{job.description}")
    return "\n".join(lines)


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
    """Score every job concurrently, skipping (and logging) any that fail."""
    if not jobs:
        return []

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY not set — copy .env.example to .env and fill it in."
        )

    client = Anthropic(api_key=api_key)
    scored: list[ScoredJob] = []
    done = 0

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as pool:
        futures = {pool.submit(score_job, client, job): job for job in jobs}
        for future in as_completed(futures):
            job = futures[future]
            done += 1
            try:
                scored.append(future.result())
            except Exception as exc:  # noqa: BLE001 — one bad job shouldn't kill the run
                print(f"  ⚠️  Scoring failed for {job.company} — {job.title}: {exc}")
            if done % 50 == 0 or done == len(jobs):
                print(f"     ...scored {done}/{len(jobs)}")

    return scored
