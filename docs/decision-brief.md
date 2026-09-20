# xevents — Decision brief: four open questions

- Date: 2026-09-18
- Status: for redline — nothing here is decided until the project lead rules.

## How to use this document

Each section is self-contained; decide the four questions in any order. Every
section gives the full option set first, tradeoffs second, and exactly one
recommendation third. No recommendation contradicts a baked-in design decision
(two clocks everywhere, confidence as bands with rationale, the correction
ledger as a queryable public output, removal distinct from retraction,
research-unverifiable details flagged UNVERIFIED). Where an option would reopen
a baked-in decision, it is flagged.

---

## Q1. Confidence band granularity

**The question (open-decisions.md #1):** Is `unverified / low / moderate /
high / disputed` the right set and granularity? Alternatives include
collapsing `unverified`/`low`, or adding granularity at the top end.

**ADR context (0006):** Confidence is a band with a rationale, never a bare
number; model weights are internal-only. Corroboration counts independence
classes, not raw source counts. Single-source MVP: most incidents honestly
assess `unverified`/`low`. Assessments are superseded, never edited.

**Options:**

- **A. Keep the five bands** as proposed.
- **B. Collapse to four:** merge `unverified` + `low`.
- **C. Add top-end granularity:** split `high`, or add a stronger band such as
  `confirmed`.
- **D. Drop `disputed` from the band set;** represent disputes via incident
  status (`contested`) only.

**Tradeoffs:**

- **B** loses the most load-bearing distinction in the MVP: "we recorded a
  claim" vs "we recorded a claim, captured evidence at ingest, and resolved
  the entity to a real organization." With one source, nearly everything lives
  in `unverified`/`low` — collapsing them flattens the only variance the MVP
  produces.
- **C** designs for a future with no data. The top bands will be near-empty
  until multi-source corroboration exists, so finer top-end granularity is
  unmeasurable in MVP. Worse, any label stronger than `high` (e.g.
  `confirmed`) **reopens a baked-in decision**: xevents is not a breach
  verification service. We record claims; we do not confirm intrusions.
- **D** is superficially clean (dispute as status, not confidence), but the
  band is the at-a-glance published output. Dropping `disputed` from it means
  a consumer reading only the band sees `high` on an actively contested
  incident. Status and band must agree, and the band must carry the warning.
- **A** costs one thing: every band needs an operational definition with
  necessary-and-sufficient criteria, or assessors drift. That is real writing
  work — but it is required under any option.

**Recommendation: A — keep the five bands,** with two hardening requirements
written into ADR 0006 before build: (1) operational definitions for each band
with criteria plus two worked examples each; (2) an explicit single-source cap
rule — one independence class caps an incident at `low`, regardless of how
clean the evidence capture is. Revisit granularity empirically once the
correction ledger holds real retraction data (the ledger is the training
signal per ADR 0006); do not pre-design finer bands now.

**Unblocks:** ADR 0006 finalization; MVP scope item 5.

**Docs to update on acceptance:** ADR 0006 (status → accepted; add band
definitions + cap rule); open-decisions.md #1 → resolved.

---

## Q2. ransomware.live manual cross-checks

**The question (open-decisions.md #2):** Is even manual, query-level use too
close to the line, or acceptable under constraints (minimal, documented, never
automated at bulk)? Current default: no contact at all.

**ADR context (0002):** ransomware.live is excluded as a dependency — no bulk
storage, no republication, no build-time or run-time dependency. Its v2 ToS is
"Personal use only … not intended for corporate or business use," and bars
redistribution-as-API and raw-data publishing. EU sui generis database right
(French-law governed) protects the aggregation.

**Options:**

- **A. No contact at all,** as a standing rule.
- **B. Manual query-level cross-checks under hard constraints:** single-fact
  verification only, every lookup logged as an observation with source, never
  automated, never stored at scale, never republished.
- **C. Seek written permission first;** scope follows the answer.
- **D. Published aggregate statistics only** (with attribution); no
  victim-level lookups.

**Tradeoffs:**

- The legal subtlety that decides this: the EU database right covers not just
  bulk extraction but **repeated and systematic extraction of insubstantial
  parts**. Occasional single-fact lookups are fine; a standing practice of
  "check ransomware.live whenever entity resolution is uncertain" starts to
  look like exactly the repeated-extraction pattern the right targets — even
  done by hand. B's constraints are load-bearing, not cosmetic, and they are
  hard to audit after the fact.
- The practical value of B is real but narrow: richer metadata for
  disambiguating victim identity (the Thames Water trap — Clop listed the
  wrong water company). But every identity question B would answer already has
  a home: the human-review queue (ADR 0005), fed by our own enrichment
  observations.
- Licensing cleanliness is the project's moat (AGENTS.md scar tissue #1). A
  provenance story with an asterisk — "clean except for the lookups we ran on
  the restricted aggregator" — is the kind of thing that surfaces at the worst
  possible moment, e.g. when a listed company disputes a record.
- **C** costs one email and has asymmetric upside. **D** keeps a door open
  with zero victim-level exposure, but published aggregates add little over
  what RansomLook already provides.

**Recommendation: A as the standing rule, with C executed in parallel** —
send the written permission request now; if granted, scope is revisited in a
new ADR. If denied or unanswered after 30 days, close the question as A for v1.
Rationale: the marginal value (slightly better disambiguation on some victims)
does not justify tainting the provenance story, and the review queue already
covers the need. Log the permission request itself in the source registry.

**Unblocks:** ADR 0002 finalization (delete or keep the carve-out paragraph
accordingly).

**Docs to update on acceptance:** ADR 0002; source registry (permission
request); open-decisions.md #2 → resolved.

---

## Q3. De-listing detection threshold

**The question (open-decisions.md #3):** What counts as a removal? N
consecutive missed polls (N = ?), multi-poller confirmation, or something
else? Currently UNSET; no auto-emission until decided.

**ADR context (0007):** Re-poll listing sources on a schedule; diff against
last-seen state. Removal observations are first-class but **never
auto-retract** the incident (removal ≠ retraction — baked in). A single missed
poll is not a removal. MVP diffs successive RansomLook snapshots; Tor-side
diffing arrives with the crawler.

**Options:**

- **A. N=2** consecutive missed polls.
- **B. N=3** consecutive missed polls.
- **C. N=5+** consecutive missed polls.
- **D. Time-based:** absent for X hours, independent of poll count.
- **E. Two-condition:** N missed polls AND the listing is absent from the
  source's own current full index.

**Tradeoffs:**

- **Error asymmetry dominates.** A false removal observation is an immutable
  claim about the world ("this victim was de-listed" reads as paid ransom or
  false claim). It triggers re-assessment and, if surfaced, misleads. A slow
  removal merely timestamps late — and the two clocks record `observed_at`
  honestly, so delay corrupts nothing. Doctrine 3 ("absence is not evidence")
  demands conservatism.
- **The subtlety most designs miss:** in MVP we diff *RansomLook's*
  snapshots, not leak sites directly. A listing absent from RansomLook may be
  RansomLook's scraper failing, not a true de-listing. Counting only our own
  missed polls measures our pipeline, not the world — E's second condition
  (absent from the source's own current index) is what ties the observation to
  the source's view of the world.
- **D vs counts:** equivalent under a fixed cadence; counts are simpler to
  record in `listing_state` and self-document in the rationale. Make it
  count-based, record the cadence alongside, note the time equivalent.
- **N=2** is trigger-happy against upstream scraper flakiness; **N=5** buys
  little over N=3 while delaying a genuinely valuable signal (removals are a
  differentiator — no surveyed source publishes them).

**Recommendation: B+E — 3 consecutive missed polls AND absence from the
source's current full index**, then auto-emit the removal observation with
both conditions cited in its rationale. Parameterize N per source (recorded in
`listing_state` and the pipeline version), default 3. Starting cadence
proposal: poll every 6 hours (≈18h detection latency; cheap against an API) —
cadence stays tunable without revisiting this decision. Until cadence is set,
keep current behavior: flag candidates for human review, no auto-emission.

**Unblocks:** ADR 0007 finalization; MVP scope item 6.

**Docs to update on acceptance:** ADR 0007 (status → accepted; threshold
rule); data-model `listing_state` semantics; open-decisions.md #3 → resolved.

---

## Q4. Dispute-channel response SLA for v1

**The question (open-decisions.md #4):** Should the v1 docs state a
response-time commitment (e.g. acknowledge within N days), or state
best-effort with no SLA? Currently: published process with manual handling,
no time commitment.

**ADR context (0004):** The dispute/correction channel ships on day one,
before the public research surface. Handling is manual in MVP (reviewer: the
project lead). Correction events are append-only; the ledger is a public
credibility asset. Claim-framing is mandatory on the public surface.

**Options:**

- **A. No published SLA** — best-effort, "we review disputes as received."
- **B. Modest published SLA:** acknowledge within 2 business days; initial
  assessment posted to the ledger within 10 business days.
- **C. Aggressive SLA:** 24-hour acknowledgment, 72-hour resolution.
- **D. Tiered:** wrongful/false-listing allegations (reputational harm)
  fast-tracked; routine corrections on the standard track.

**Tradeoffs:**

- The ledger is the credibility asset, and the project publishes attacker
  claims about named companies — the defamation-adjacent surface (landscape
  §6.3) is exactly where a responsive dispute process matters most. A
  published channel with no time commitment reads as a formality, and "a
  published channel nobody monitors is worse than none."
- But the reviewer is one human. An SLA he cannot keep destroys the
  credibility it was meant to build — **C is a trap** for a single-operator
  project.
- Acknowledgment and resolution are different commitments. Acknowledgment is
  cheap (templated reply + `dispute_opened` ledger entry); resolution requires
  investigation and sometimes victim cooperation. Bind the cheap part tightly,
  the expensive part loosely.
- Wrongful-listing claims deserve the fast track on risk grounds alone: a
  company wrongly named as a ransomware victim suffers reputational harm every
  day the claim stands unacknowledged.

**Recommendation: D-flavored B** — publish a two-tier commitment: (1) every
dispute acknowledged within 2 business days via a `dispute_opened` ledger
entry; (2) disputes alleging wrongful/false listing acknowledged within 1
business day and prioritized; (3) initial assessment posted to the ledger
within 10 business days for all disputes. State explicitly that the commitment
covers acknowledgment and initial assessment, not final resolution, and that it
is a research-project commitment, not a legal one. Handling stays manual in
MVP.

**Unblocks:** ADR 0004 finalization; MVP scope item 6.

**Docs to update on acceptance:** ADR 0004 (status → accepted; SLA text);
dispute process doc; open-decisions.md #4 → resolved.

---

## Acceptance checklist

For each question ruled on:

1. Flip the ADR from `proposed` to `accepted` (or record the rejection and
   the chosen alternative).
2. Apply the "Docs to update" line for that section.
3. Mark the open-decisions.md item resolved, with the date and the decision.

A partial redline is fine — each section stands alone.
