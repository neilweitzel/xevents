# ADR 0007: De-listing / removal detection via re-polling and diffing

- Status: accepted (2026-09-21, user redline on PR #8)
- Date: 2026-09-18
- Deciders: project lead

## Context

Ransomware groups remove victims from leak sites — most notably when victims
pay. **No aggregator publishes a structured "listing removed" history**
(landscape §1.8.4, §7.3). Removals are therefore invisible to every existing
tracker, yet they are among the most valuable observations available: a
removal is evidence of payment, of a false claim being pulled, or of a
takedown/seizure.

Two cautions from the research. First, a removal must not be auto-read as a
retraction: a victim who paid the ransom was still genuinely compromised — the
incident is real, the claim's *lifecycle* changed. Second, absence is not
evidence (AGENTS.md doctrine 3): when a group's site is seized or goes dark,
scrapers go silent, and that silence means "not observed," never "inactive"
(landscape §1.8.7). Takedowns do not reduce aggregate volume — operators
scatter and regroup within days — and rebrand chains (DarkSide→BlackMatter→
ALPHV; Royal→BlackSuit; Hunters International→World Leaks) mean a listing can
"disappear" from one identity and reappear under another.

## Decision

1. **Re-poll listing sources on a schedule; diff current listings against
   last-seen state.** When a previously observed listing is absent, emit a
   **removal observation** automatically: claim type `removal`, linked to the
   original listing observation, carrying the last-seen capture as evidence
   (ADR 0003) and the first-missing timestamp.
2. **Removal observations feed the incident record** — they trigger a status
   review and a confidence re-assessment (ADR 0006) — but they **do not
   auto-retract** the incident. The rationale records the ambiguity: payment,
   false claim, or takedown.
3. **Distinguish true de-listings from scraper failures.** A single missed
   poll is not a removal. The threshold is **DECIDED (open-decisions.md #3,
   2026-09-20):** three consecutive missed polls, plus absence from a
   rolling `/recent` window and a negative direct `/search` for the item
   (the operational equivalent of a full-index comparison — RansomLook
   exposes no public full-index endpoint). The chosen parameter is recorded
   in the observation's pipeline version and in `listing_state`. Until the
   threshold is met, no removal observation may be auto-emitted: flag
   candidates for human review instead.
4. **Track group-identity chains as observations** (rebrands, seizures,
   successor groups) so removals are not misread across identities — a victim
   "removed" from BlackSuit's site the week Royal rebranded is not the same
   signal as a quiet mid-campaign de-listing. **MVP note:** applied to the
   single MVP source (diffing successive RansomLook snapshots); Tor-side
   diffing arrives with the crawler (docs/mvp-scope.md, non-goal 1).

## Consequences

- Polling cadence is a cost/accuracy tradeoff: too sparse and removal
  timestamps are useless; too aggressive and we burn rate limits and Tor
  circuits. Cadence is DECIDED (open-decisions.md #5, 2026-09-20): 2-hour
  trigger with a 6-hour effective-cadence guard. Tune from the data once set.
- Diffing needs a stable listing identity (group + victim + URL). Groups that
  rotate URLs or rename victims will produce false removals — the alias table
  (ADR 0005) and group-identity tracking are the mitigation.
- Removal observations are a differentiator: no surveyed source publishes this
  signal, and it directly serves the long-term trend analytics (e.g.,
  payment-rate proxies, false-claim rates).

## Research basis

- Landscape §1.8.4 (de-listing/removal events: no aggregator publishes them),
  §7.3 (detection via re-polling/diffing as a top-5 hard problem).
- Landscape §1.8.7 (seizure/takedown blind spots; absence ≠ inactivity).
- Landscape §6.1 (volatility, rebrands, takedowns 2024–2026; fragmentation:
  85+ active groups, ~8,000 claimed victims in 2025).
- Landscape §5.2 (Coveware: 23% of victims paid in Q3 2025 — removals are a
  measurable, policy-relevant signal).

## Pivot note, 2026-09-21 (user decisions #8–#11)

The detection mechanics are unchanged (three consecutive missed polls plus
the operational full-index equivalent — rolling `/recent` window plus
negative direct `/search`; never a single missed poll — see
docs/source-spec-ransomlook.md). What changed is the blast radius:

- **De-listing now governs internal observations only.** `listing_state`
  and `removed_confirmed` live in `xevents-internal`. There is no public
  victim entry to de-list — nothing about this pivot weakens the
  detection; it shrinks what a removal affects.
- **Propagation:** a confirmed removal becomes an internal `removal`
  observation and a correction-ledger entry; the affected public
  aggregates are recomputed and the removal is visible on the sector
  detail page's ledger section. Removal ≠ retraction still holds: the
  observation history is retained, the aggregate carries the
  `removed_confirmed` contribution in its breakdown, and the ledger says
  so.
- The de-listing threshold is unchanged by the pivot (open-decisions.md
  #3 stands; #11 operationalizes it).

Status: accepted (2026-09-21, user redline on PR #8).
