# job-radar

Agentic job search monitor — scans fintech / AI-native company careers daily, scores roles with Claude, and sends a Telegram digest.

Built for senior ICs / engineering leaders who want to **catch the right opening the day it is posted** without manually trawling 40 careers pages or trusting LinkedIn's algorithm.

## Why

Senior roles (Head of Engineering, Founding Engineer, Engineering Manager at AI-native product companies) are high-signal / low-volume. Inbound recruiter messages skew toward body-shop IC roles. The best openings fill in days from the private founder network — so a daily automated sweep of a curated target list is leverage.

job-radar runs serverlessly on GitHub Actions, hits public ATS APIs (Greenhouse, Lever, Ashby, Workable) for a curated target-company list plus the RemoteRocketship aggregator API for cross-company saved searches, diffs today's inventory against yesterday's snapshot, has Claude score only the newly posted roles against a personal rubric, and pushes a Telegram digest.

## Status

Phase 1 ✅  — Fetchers + snapshot persistence working across 4 ATS platforms
Phase 2 ✅  — Diff engine (new-jobs-since-yesterday) + Claude (Haiku) scoring against the candidate rubric
Phase 3 ✅  — Telegram digest delivery (dream matches + target-list hits, splits long messages)
Phase 4 ✅  — GitHub Actions daily cron (`.github/workflows/daily-digest.yml`, 07:00 Europe/Warsaw) — add the three secrets below to activate it
Phase 5 ✅  — RemoteRocketship aggregator source (`queries.yaml`, saved cross-company searches) — optional, needs its own API key

## Architecture

```
targets.yaml                queries.yaml
      │                           │
      ▼                           ▼
┌─────────────────────┐   ┌──────────────────────┐
│  Fetchers (per-ATS) │   │  RemoteRocketship    │
│  greenhouse / lever │   │  aggregator search    │
│  ashby / workable   │   │  (optional, paid key) │
└──────────┬──────────┘   └───────────┬───────────┘
           │                          │
           └──────────────┬───────────┘
                           │   normalized Job list
                           ▼
     ┌─────────────────┐
     │  Snapshot diff  │   (today vs. previous snapshot)
     └────────┬────────┘
              │   only new jobs
              ▼
     ┌─────────────────┐
     │  Claude scorer  │   (rubric → 0-10, dream_match flag)
     └────────┬────────┘
              │   high-score hits
              ▼
     ┌─────────────────┐
     │  Telegram push  │   (daily digest)
     └─────────────────┘
```

## Local setup

Requires Python 3.11+.

```bash
git clone git@github.com:lsivl/job-radar.git
cd job-radar
python3.13 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env   # fill in ANTHROPIC_API_KEY + Telegram creds

python scan.py         # one-off run: fetch -> snapshot -> diff -> score -> digest
```

Without `ANTHROPIC_API_KEY` set, scoring will raise. Without the Telegram
vars set, delivery just logs a warning and skips (everything else still
runs and the snapshot still gets saved).

### Getting a Telegram bot token + chat id

1. Message [@BotFather](https://t.me/BotFather) on Telegram -> `/newbot` -> follow the prompts -> copy the token.
2. Send your new bot any message (so it has a conversation to reply into).
3. Visit `https://api.telegram.org/bot<TOKEN>/getUpdates` and read `message.chat.id` from the JSON -> that's `TELEGRAM_CHAT_ID`.

## Configuring targets

Edit `targets.yaml`. Each entry needs the ATS and the board slug — see the comments in that file for how to find the slug from a company's careers URL.

Current list (20 companies) spans fintech (Monzo, Mercury, Wise, Qonto,
Trade Republic, Adyen, Plaid, Ramp), AI-native (Anthropic, OpenAI, Harvey,
Cursor, ElevenLabs, Vercel, Replit, Perplexity), and crypto/AI
infrastructure (Fireblocks, Gensyn, Ritual, Deel).

**Adding many companies at once?** Expect a one-time scoring backlog on the
next run — `scorer.py` parallelizes across a thread pool (`MAX_WORKERS` in
`radar/scorer.py`), so even a 500-1000 job backlog finishes in a couple of
minutes rather than tying up the sequential-call path for half an hour.

## RemoteRocketship aggregator (optional)

Unlike `targets.yaml`'s per-company ATS fetchers, [RemoteRocketship](https://www.remoterocketship.com/api-docs/)
is a cross-company job search API (300k+ company career pages) — saved
searches live in `queries.yaml` instead, with real filters (title,
seniority, salary floor, remote-only, exclude industry, hide ghost jobs)
applied server-side before Claude ever sees a posting.

Requires an **Advanced plan subscription** (check pricing at
https://www.remoterocketship.com/account/ -> Advanced -> API access) and
`REMOTEROCKETSHIP_API_KEY` in `.env`. Quota: 3000 jobs / 500 requests per
UTC day. If the key is unset, these queries are skipped entirely —
`targets.yaml` keeps working standalone.

## Deployment

Daily cron via GitHub Actions (`.github/workflows/daily-digest.yml`, 07:00
Europe/Warsaw, plus a manual `workflow_dispatch` trigger for testing).
Snapshots are committed back into `snapshots/` each run so history persists
without any external storage.

To activate it, add these as **repo secrets** (Settings -> Secrets and
variables -> Actions -> New repository secret) — same values as your local
`.env`, never committed:

- `ANTHROPIC_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `REMOTEROCKETSHIP_API_KEY` (optional — only if you want `queries.yaml` to run in the cron too)

Then trigger it once manually (Actions tab -> Daily Job Digest -> Run
workflow) to confirm it works before trusting the cron.

The `ANTHROPIC_API_KEY` from console.anthropic.com's quick-create flow may
be short-lived (~30 days) — if the workflow starts failing, check the
console for an expired key first.

## License

MIT — see [LICENSE](LICENSE).
