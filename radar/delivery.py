"""Telegram digest delivery."""

from __future__ import annotations

import os

import httpx

from .models import ScoredJob

TELEGRAM_API = "https://api.telegram.org/bot{token}/sendMessage"
DEFAULT_THRESHOLD = 7
TELEGRAM_CHUNK_SIZE = 4000  # Telegram's hard cap is 4096 chars per message.


def _format_job(scored: ScoredJob) -> str:
    job = scored.job
    flag = "🔥 DREAM MATCH" if scored.dream_match else f"🎯 Score {scored.score}/10"
    lines = [
        f"{flag} — <b>{job.company}</b>",
        job.title,
        f"📍 {job.location}",
        f"🔗 {job.url}",
    ]
    if scored.reasons:
        lines.append("✅ " + "; ".join(scored.reasons))
    if scored.concerns:
        lines.append("⚠️ " + "; ".join(scored.concerns))
    if scored.suggested_action:
        lines.append(f"👉 {scored.suggested_action}")
    return "\n".join(lines)


def _chunk(text: str, size: int = TELEGRAM_CHUNK_SIZE) -> list[str]:
    return [text[i : i + size] for i in range(0, len(text), size)] or [text]


def _send(token: str, chat_id: str, text: str) -> None:
    url = TELEGRAM_API.format(token=token)
    for chunk in _chunk(text):
        response = httpx.post(
            url,
            data={
                "chat_id": chat_id,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=10.0,
        )
        if response.status_code != 200:
            print(f"  ⚠️  Telegram delivery failed ({response.status_code}): {response.text}")


def send_digest(scored_jobs: list[ScoredJob], threshold: int = DEFAULT_THRESHOLD) -> None:
    """Push a digest of today's hits. Safe to call with an empty list."""
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat_id:
        print("  ⚠️  Telegram not configured — skipping delivery "
              "(set TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID in .env).")
        return

    dream = [s for s in scored_jobs if s.dream_match]
    hits = [s for s in scored_jobs if not s.dream_match and s.score >= threshold]

    if not dream and not hits:
        _send(token, chat_id, f"📭 Job radar: checked today, no matches ≥ {threshold}/10. All quiet.")
        return

    sections = []
    if dream:
        sections.append("🔥 <b>DREAM MATCHES</b>\n\n" + "\n\n".join(_format_job(s) for s in dream))
    if hits:
        sections.append("🎯 <b>TARGET LIST HITS</b>\n\n" + "\n\n".join(_format_job(s) for s in hits))

    _send(token, chat_id, "\n\n".join(sections))
