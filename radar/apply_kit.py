"""Draft a tailored CV-highlights + cover letter for standout matches.

Deliberately does NOT send anything to a company or an ATS — see the
project's own "don't build auto-apply" decision in README. This only
produces a reviewable draft, delivered as a Telegram document, that the
candidate reads and decides whether to use.

Requires a local, gitignored resume/base_cv.md (contains PII — name,
email, phone — so it is never read from, or written to, the repo itself).
If that file is missing (e.g. in the GitHub Actions cloud run, where it
was never uploaded as a secret), apply-kit generation is skipped entirely.
"""

from __future__ import annotations

import json
from pathlib import Path

from anthropic import Anthropic

from .models import ScoredJob

MODEL = "claude-sonnet-5-5"  # writing quality matters here more than for triage scoring
RESUME_PATH = Path("resume/base_cv.md")


def load_resume(path: Path = RESUME_PATH) -> str | None:
    """Return the base resume text, or None if it isn't present locally."""
    if not path.exists():
        return None
    return path.read_text()


def _parse_json(text: str) -> dict:
    text = text.strip()
    if text.startswith("```"):
        text = text.strip("`")
        if "\n" in text:
            first_line, rest = text.split("\n", 1)
            text = rest if first_line.strip().lower() in ("json", "") else text
    return json.loads(text)


def _build_prompt(scored: ScoredJob, resume_text: str) -> str:
    job = scored.job
    return f"""\
You are helping a candidate prepare application material for ONE specific
job opening. Ground every claim strictly in the resume below — never
invent experience, employers, dates, or skills that aren't in it. If the
role's apparent requirements exceed what the resume supports, say so
honestly in the cover letter rather than papering over the gap (the
candidate already does this deliberately — e.g. acknowledging limited
blockchain/smart-contract depth rather than bluffing).

CANDIDATE'S BASE RESUME:
---
{resume_text}
---

THIS OPENING:
- Company: {job.company}
- Role: {job.title}
- Location: {job.location}
- Salary: {job.salary_range or "not listed"}
- Tech stack mentioned: {", ".join(job.tech_stack) if job.tech_stack else "not listed"}
- URL: {job.url}

An earlier automated screening pass already evaluated fit against this
opening and found:
- Reasons it's a good match: {"; ".join(scored.reasons) or "none recorded"}
- Concerns / gaps: {"; ".join(scored.concerns) or "none recorded"}

Produce:
1. A one-line positioning statement tailored to this specific opening
   (how the candidate should introduce themselves for THIS role).
2. 4-6 resume highlight bullets, pulled or lightly reworded from the
   resume above, re-ordered and re-emphasized for this specific opening
   (most relevant first). Do not fabricate anything not already in the
   resume.
3. A cover letter, 150-220 words, specific to this company and role
   (reference the company/role by name, not generic filler), honest
   about any real gaps, professional tone, no corporate cliches.

Respond with ONLY a single JSON object (no prose, no markdown fences):
{{
  "positioning_line": "<string>",
  "highlights": ["<string>", ...],
  "cover_letter": "<string, may contain \\n for paragraph breaks>"
}}
"""


def draft_application(client: Anthropic, scored: ScoredJob, resume_text: str) -> dict:
    response = client.messages.create(
        model=MODEL,
        max_tokens=3000,  # Sonnet reasons before answering; 1200 truncated mid-JSON
        messages=[{"role": "user", "content": _build_prompt(scored, resume_text)}],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return _parse_json(text)


def format_draft_markdown(scored: ScoredJob, draft: dict) -> str:
    job = scored.job
    highlights = "\n".join(f"- {h}" for h in draft.get("highlights", []))
    return f"""\
# DRAFT application material — {job.title} @ {job.company}

**This is a draft for your review only — nothing has been sent anywhere.**

Job: {job.url}
Match score: {scored.score}/10{" (dream match)" if scored.dream_match else ""}

## Positioning line

{draft.get("positioning_line", "")}

## Resume highlights to lead with

{highlights}

## Cover letter draft

{draft.get("cover_letter", "")}
"""
