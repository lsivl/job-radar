# job-radar

Agentic job search monitor — scans fintech / AI-native company careers daily, scores roles with Claude, and sends a Telegram digest.

Built for senior ICs / engineering leaders who want to **catch the right opening the day it is posted** without manually trawling 40 careers pages or trusting LinkedIn's algorithm.

## Why

Senior roles (Head of Engineering, Founding Engineer, Engineering Manager at AI-native product companies) are high-signal / low-volume. Inbound recruiter messages skew toward body-shop IC roles. The best openings fill in days from the private founder network — so a daily automated sweep of a curated target list is leverage.

job-radar runs serverlessly on GitHub Actions, hits public ATS APIs (Greenhouse, Lever, Ashby, Workable), diffs today's inventory against yesterday's snapshot, has Claude score only the newly posted roles against a personal rubric, and pushes a Telegram digest.

## Status

Phase 1 ✅  — Fetchers + snapshot persistence working across 4 ATS platforms
Phase 2 🚧  — Diff engine + Claude scoring
Phase 3 🗓️  — Telegram delivery
Phase 4 🗓️  — GitHub Actions daily cron

## Architecture

```
targets.yaml
      │
      ▼
┌─────────────────────────────────┐
│  Fetchers (per-ATS)             │
│    greenhouse / lever /         │
│    ashby    / workable          │
└──────────────┬──────────────────┘
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

cp .env.example .env   # fill in ANTHROPIC_API_KEY + Telegram creds later

python scan.py         # one-off run
```

## Configuring targets

Edit `targets.yaml`. Each entry needs the ATS and the board slug — see the comments in that file for how to find the slug from a company's careers URL.

Current seed list covers Monzo, Mercury, Plaid, Ramp, Anthropic, OpenAI, Harvey, Cursor, Fireblocks.

## Deployment (planned)

Daily cron via GitHub Actions. Secrets (Anthropic API key, Telegram bot token, chat id) stored in repo settings — never committed. Snapshots are committed back into `snapshots/` to maintain historical state across runs without external storage.

## License

MIT — see [LICENSE](LICENSE).
