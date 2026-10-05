"""Candidate profile + scoring rubric used to prompt Claude.

Keeping this in its own module makes it easy to tune the criteria over time
without touching the scoring plumbing in scorer.py.
"""

from __future__ import annotations

CANDIDATE_PROFILE = """\
CANDIDATE PROFILE:
- Current: Team Lead at eToro (fintech) — owns financial reporting across
  30+ countries. Previously first backend engineer at Wirex (crypto
  exchange): hot wallet architecture, on-chain transaction analysis via
  Elliptic, PCI DSS certification.
- Shipped two 0->1 AI products to production: RetroKPI (agent-based
  engineering analytics platform, 1,000+ engineers) and Hot Topics
  (LLM + embeddings pipeline).
- Target roles: Head of Engineering / Engineering Manager / Founding
  Engineer — ideally at an early-stage (seed-Series C) AI-native product
  company. Open to a hybrid IC+leadership role (0->1 builder energy), not
  a pure large-team people-manager role.
- Domain preference: fintech, AI infrastructure, crypto/digital-assets
  adjacent (custodial/infra side — NOT deep DeFi protocol / smart-contract
  development; that is an honest, known gap).
- Location: Wrocław, Poland. Works as a Polish B2B contractor
  (działalność gospodarcza). Location rules, in order of preference:
    1. Remote, but MUST be legally eligible to work from Poland. A role
       advertised as "remote" that is actually restricted to a specific
       country/region excluding Poland (e.g. "Remote - US only", "must
       reside in the UK", "EU-only" when Poland isn't clearly EU-covered,
       visa/work-authorization tied to a non-Poland jurisdiction) is a
       DISQUALIFIER, not a minor concern — flag it clearly and score low.
    2. Hybrid is acceptable ONLY if the office is in Wrocław itself.
       Hybrid requiring any other city/country is a disqualifier.
    3. Fully remote with frequent business travel/offsites is explicitly
       FINE — do not treat travel requirements as a concern.
  Relocation (permanent onsite elsewhere) only worth it at "game-changer"
  comp (~€13K+ gross/month Dutch-equivalent or similar, accounting for
  dual-income household).
- Compensation anchor: €9K+/month gross equivalent (B2B or net-equivalent
  UoP), or meaningful equity upside at an early-stage company.
- Explicitly NOT interested in: staffing/body-shop placements (not direct
  hire), pure IC/"Tech Lead" downshifts from current Team Lead level,
  non-AI-native traditional enterprise software, roles requiring deep
  smart-contract/DeFi protocol expertise.
"""

SCORING_INSTRUCTIONS = """\
Score this opportunity for the candidate above, from the job posting
metadata given below. Be honest and skeptical — most postings will NOT be
a great fit, and that is fine; the goal is to surface the rare good ones,
not to be generous.

A "dream_match" (true) requires ALL of:
  - Early-stage (roughly seed through Series B, small team)
  - AI-native core product (not just "uses AI tools internally")
  - Founding-engineer or first-senior-hire level scope
  - Remote and confirmed/likely eligible from Poland (or hybrid based in
    Wrocław specifically)
  - Strong equity / upside signal

Respond with ONLY a single JSON object (no prose, no markdown fences)
matching exactly this shape:
{
  "score": <integer 0-10, overall fit>,
  "confidence": <integer 0-10, how confident you are given the limited
                  metadata available — low if title/location is all you
                  have, higher if department/context is rich>,
  "dream_match": <true or false>,
  "reasons": [<short string>, ...],
  "concerns": [<short string>, ...],
  "suggested_action": <one short sentence: apply / research / pass / ...>
}
"""


def build_prompt(job_summary: str) -> str:
    return f"{CANDIDATE_PROFILE}\nOPPORTUNITY:\n{job_summary}\n\n{SCORING_INSTRUCTIONS}"
