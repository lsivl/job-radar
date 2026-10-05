# job-radar

Agentic job search monitor — scans fintech / AI-native company careers daily, scores roles with Claude, and sends a Telegram digest.

Built for senior ICs / engineering leaders who want to **catch the right opening the day it is posted** without manually trawling 40 careers pages or trusting LinkedIn's algorithm.

## Why

Senior roles (Head of Engineering, Founding Engineer, Engineering Manager at AI-native product companies) are high-signal / low-volume. Inbound recruiter messages skew toward body-shop IC roles. The best openings fill in days from the private founder network — so a daily automated sweep of a curated target list is leverage.

job-radar runs serverlessly on GitHub Actions, hits public ATS APIs (Greenhouse, Lever, Ashby, Workable), diffs today's inventory against yesterday's snapshot, has Claude score only the newly posted roles against a personal rubric, and pushes a Telegram digest.

## Status

Phase 1 ✅  — Fetchers + snapshot persistence working across 4 ATS platforms
Phase 2 ✅  — Diff engine (new-jobs-since-yesterday) + Claude (Haiku) scoring against the candidate rubric
Phase 3 ✅  — Telegram digest delivery (dream matches + target-list hits, splits long messages)
Phase 4 ✅  — GitHub Actions daily cron (`.github/workflows/daily-digest.yml`, 07:00 Europe/Warsaw) — add the three secrets below to activate it

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

Current seed list covers Monzo, Mercury, Plaid, Ramp, Anthropic, OpenAI, Harvey, Cursor, Fireblocks.

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

Then trigger it once manually (Actions tab -> Daily Job Digest -> Run
workflow) to confirm it works before trusting the cron.

The `ANTHROPIC_API_KEY` from console.anthropic.com's quick-create flow may
be short-lived (~30 days) — if the workflow starts failing, check the
console for an expired key first.

## License

MIT — see [LICENSE](LICENSE).
