# xevents — MVP scope

**Status:** ACCEPTED 2026-09-21 (user redline on PR #8). The items in
`docs/open-decisions.md` also gate parts of this scope; wherever this
document touches one, it says so.

**Pivot note, 2026-09-21 (open-decisions.md #8–#11):** the public surface
is sector-aggregated — no organization names, no threat-actor brand names.
The unit of the public page is the sector × time-window aggregate, built
from internal full-fidelity observations held in the private
`xevents-internal` repo. Non-goals 4 (research surface) and 5 (sector
classification) are lifted into MVP scope by user decision. Accepted
2026-09-21 on the user's redline of PR #8.

## What the MVP proves

That the core loop works end to end on real data, at the highest quality bar:

**ingest → immutable observation (private) + captured evidence → sector
classification → explainable confidence + victim-acknowledged status →
correction handling → name-free aggregates → public research surface.**

One source, done well, before any second source is added. The pipeline is
designed source-agnostic so a second source is a new poller + parser, not a
redesign.

## In scope

### 1. Single-source ingest: RansomLook API

- Scheduled poller against RansomLook's no-key public API (ADR 0002). Full
  endpoint/schema/poller rules: docs/source-spec-ransomlook.md (verified
  live 2026-09-20).
- **Idempotent ingest.** Idempotency key is the item's `misp_uuid`
  (fallback: the entity link path). Re-polls update
  `listing_state.last_seen_at` and the `poll_run` row; they never create
  duplicate observations (data-model.md: `listing_state`, `poll_run`).
- **Backfill policy.** First run ingests the full available history via
  `/api/posts/period/{start}/{end}` (verify the endpoint at build time).
  Backfilled rows get `observed_at` = backfill time and
  `source_claimed_at` = the item's `discovered` — the two clocks keep
  backfill provenance honest. Backfill volume must be triaged against the
  entity-resolution review queue (item 3) before MVP sign-off; a full
  history dump that buries the queue fails the item-3 acceptance.
- Every genuinely new item → one immutable observation: `subject_raw`
  verbatim, `source_claimed_at` from RansomLook's `discovered`, raw payload
  stored, pipeline version recorded. Non-victim entries (`audit team`
  operational notices, `private="True"` items) are filtered at ingest and
  logged in the `poll_run` row.
- **Acceptance:** poller runs unattended on schedule; a re-run of any poll
  creates zero duplicate observations; RansomLook's current license terms are
  re-verified and the attribution string is rendered before first ingest.

### 2. Capture-at-ingest evidence

- Per observation: timestamped screenshot + raw HTML/metadata (ADR 0003),
  SHA-256 content-addressed, redaction step before storage.
- **Acceptance:** every observation has ≥1 evidence artifact; artifact hashes
  verify against stored bytes; a redaction note exists per artifact
  (null only when nothing was redacted). Archive-seeded observations under
  item 8, if accepted, carry source metadata and provenance as evidence in
  place of screenshots, which cannot exist for historical listings.

### 3. Sector classification (MVP subset; entity resolution narrowed by pivot)

- **Pivot note:** public entity resolution is replaced by **sector
  classification**. Internal observations keep `subject_raw` verbatim and
  a private entity record (for audit and re-derivation); the public
  pipeline classifies each observation into the NAICS 2-digit sector spine
  (`unclassified` when the evidence does not support it — never a guess).
  Organization-name resolution (SEC/GLEIF/Wikidata) is deferred; it served
  the named-ledger design this pivot retires.
- Pipeline: local normalization → sector heuristics from listing text →
  human-review queue for first-seen and low-confidence classifications
  (ADR 0010: novel taxonomy values are a 100%-review class).
- Every classification step recorded as an observation
  (`claim_type=enrichment`). Misclassifications become corrections, never
  silent fixes.
- **Acceptance:** every observation carries a sector or an honest
  `unclassified`; the review queue is empty or explicitly deferred; the
  coverage-boundary statement is published (see 7).

### 4. Observation → incident resolution (within-source, internal)

- Repeat listings and re-observations group into incidents via typed
  `incident_membership` rows with human-readable rationales (ADR 0001).
  **Pivot note:** incidents are an *internal* construct now — the unit of
  audit and confidence assessment, not the unit of the public page. The
  public page shows sector aggregates computed over incidents; incident
  titles, summaries, and entity references never cross the aggregation
  boundary (docs/naming-policy.md).
- **Grouping rule (MVP).** Observations group into one incident when they
  share the normalized threat-group string and resolve to the same victim
  entity (or the same unresolvable `subject_raw` string). Grouping rationale
  is generated from the rule plus the specific evidence; ambiguous cases go
  to the review queue instead of auto-grouping.
- **Relist after removal.** A relist following a `removed_confirmed`
  listing state opens a **new candidate incident**, linked to the prior
  incident in the rationale. Re-compromise is a distinct event until
  evidenced otherwise; the reviewer confirms or merges. (ADR 0007: removal
  ≠ retraction.)
- **Explicitly:** with one source there is no cross-source reconciliation.
  MVP "reconciliation" means dedup, repeat-listing grouping, and correction
  handling — not multi-vantage corroboration. Cross-source reconciliation is
  non-goal 3.
- **Acceptance:** the same victim relisted by the same group resolves to one
  incident; a relist-after-removal opens a linked candidate incident; every
  membership link carries a rationale a non-author can follow.

### 5. Explainable confidence + victim-acknowledged status

- Band + rationale + contributing independence classes + inputs hash on every
  incident with ≥1 observation (ADR 0006). Assessments superseded, never
  edited. Weights are internal model inputs; the band is the published output.
- **Victim-acknowledged status** (open-decisions.md #9) rides alongside the
  band: `acknowledged` / `unacknowledged` (binary — unacknowledged until a
  cited victim disclosure confirms the incident), sourced strictly to
  the victim's own public disclosure. No percentage scores anywhere.
- **Honest single-source behavior:** with one independence class in play,
  most incidents assess `unverified` or `low`. The model must not manufacture
  confidence out of repetition.
- **Acceptance:** any incident's band traces to its observations, classes,
  and rationale with no manual reconstruction; any `acknowledged` status
  traces to the cited victim disclosure.

### 6. Correction ledger + dispute channel + de-listing detection

- Append-only correction events (`correction`/`denial`/`removal`/`retraction`/
  `dispute_opened`/`dispute_resolved`/`administrative_note`); claim-framing
  mandatory on all outputs (ADR 0004). Dispute handling is manual in MVP;
  the slim process is docs/dispute-process.md (sector-classification
  corrections, internal-record inquiries, provenance challenges).
- De-listing detection: re-poll + diff against `listing_state`; removal
  observations feed incident review but **never auto-retract** (ADR 0007).
  **Pivot note:** the de-listing threshold (open-decisions.md #3, as
  operationalized in #11) governs *internal* observations; removals
  propagate to the public surface as aggregate recomputation plus ledger
  entries — there is no public victim entry to de-list.
- **Acceptance:** a simulated sector misclassification and a simulated
  de-listing both propagate end to end — observation → correction event →
  re-resolution → recomputed aggregate — with the full history visible and
  nothing deleted.

### 7. Public research surface (xfeeds-style dashboard)

- **Form (decided 2026-09-20, ADR 0009; reshaped 2026-09-21, decisions
  #8/#11):** a public static site on GitHub Pages: sector activity bands,
  sector detail pages (vector/malware-class/victim-acknowledged
  breakdowns), methodology, correction ledger, evidence-manifest browser,
  JSON aggregate export. Full page spec: docs/dashboard-spec.md.
- The surface serves the four honest MVP practitioner jobs (sector trend
  research; vector/method analysis; disclosure-lag research where both
  endpoints are evidenced; offline dataset analysis) and disclaims the
  rest (victim lookup, victim notification, alerting, attribution
  verdicts, breach verification) — see docs/dashboard-spec.md.
- Attribution strings rendered wherever CC BY 4.0-derived content appears.
  The coverage-boundary statement is published on the surface (required
  contents: entity classes resolved well vs missed, source coverage windows,
  known blind spots — see data-model.md).
- **Cadence (open-decisions.md #12):** ingest fast (decision #5),
  internal aggregation daily, public publication weekly. "Insufficient
  data" is per sector × week cell (small-cell rule, decision #13: k=5
  minimum, tunable), never a global publish gate. Each weekly publish includes only reviewed
  observations, with unreviewed counts shown. The surface stays dark until
  burn-in completes.
- **Launch gate:** the written lawful-basis / public-interest research memo
  (docs/lawful-basis-memo-template.md) must exist and be reviewed before
  the surface serves data publicly. No memo, no public surface.
- **Acceptance:** everything above reachable without manual DB queries;
  exported JSON re-derives from the observation log alone; the name-scan
  gate (ADR 0010 G5) passes on every published batch; a weekly publish
  completes with the pending-review line accurate.

### 8. Historical baseline (proposal)

- Load the frozen ransomwatch 2020–2025 archive (Unlicense) as observations
  to seed history. No live polling of a dead source.
- Archive observations carry provenance marked `ransomwatch_archive` and
  source metadata as evidence in place of screenshots (item 2 acceptance
  carve-out). If accepted, the confidence model gains the independence
  class `aggregator_ransomwatch_archive` (a frozen archive is its own
  class — it cannot echo and cannot be re-polled); adding it is a model
  change recorded in the `model_version` registry (ADR 0006).
- **Archive location/format/loader are UNVERIFIED** — the loader spec must
  be written and verified against the actual archive (joshhighet/ransomwatch
  repository) before this proposal can be accepted.
- **Acceptance:** archive items queryable with provenance marked
  `ransomwatch_archive`.

## Non-goals (explicit)

Every non-goal carries its rationale and the condition for reconsideration.
Lifting any non-goal requires a new ADR **and** the user's explicit approval
(AGENTS.md: Scope discipline).

| # | Non-goal | Rationale | Reconsidered when |
|---|---|---|---|
| 1 | Tor crawler / primary DLS collection | Largest engineering investment; MVP proves the loop on a clean aggregator first | Post-MVP ADR, when RansomLook metadata gaps block a user-approved analytic |
| 2 | Any second ingest source — including breach-disclosure sources (EDGAR, state AGs, HHS OCR) and KEV | One source done well beats three done thinly; the pipeline is source-agnostic by design | Post-MVP ADR per source, after the MVP-done checklist passes |
| 2a | (Carve-out, not a lift) Frozen, dead-source archives — the ransomwatch 2020–2025 baseline proposed in item 8 | An archive adds no ongoing ingest complexity and is tracked as its own proposal (open-decisions.md #6), not as a second live source | Decided under open-decisions.md #6 |
| 3 | Cross-source claim reconciliation | Requires ≥2 sources; MVP reconciliation is within-source only | When non-goal 2 is lifted |
| 4 | ~~Public research/analytics surface — trend dashboards, lag analytics, sector patterns, vendor concentration, victim counts~~ | **LIFTED into MVP scope by user decision 2026-09-21 (open-decisions.md #8).** The sector-aggregated research surface *is* the MVP output; victim counts are published as sector aggregates, never named entries. Analytics over a thin corpus still mislead — the launch corpus bar is set in docs/dashboard-spec.md and ADR 0010 §5 (burn-in). | Lifted |
| 5 | ~~Sector/vertical classification (NAICS mapping, Wikidata enrichment, OpenFIGI corroboration)~~ | **LIFTED into MVP scope by user decision 2026-09-21 (open-decisions.md #8)** as NAICS 2-digit sector classification (item 3). Wikidata/OpenFIGI organization enrichment stays deferred — it served the retired named-ledger design. | Lifted (partial) |
| 6 | CVE→incident linkage analytics | Needs KEV ingest (non-goal 2) plus an incident corpus; the schema already reserves `entity_kind=cve` and `claim_type=vuln_exploit_claim` | With non-goal 2, via its own ADR |
| 7 | STIX 2.1 export / OpenCTI connector | Interoperability, not core value | Post-MVP ADR on user request |
| 8 | Automated dispute handling | Volume doesn't justify it; manual keeps quality highest | Post-MVP, on dispute volume |
| 9 | Push/alerting ("new victim" notifications) | A distribution feature, not evidence infrastructure | Post-MVP ADR |
| 10 | Paid or restricted sources (ecrime.ch, ransomware.live PRO, or any RESTRICTED tier) | Licensing gates, not schedule gates | Only with written permission or a paid tier, plus user approval |
| 11 | IoC feeds, victim notification workflows, ransom negotiation, threat-actor attribution beyond group identity | Not incident-claim intelligence; outside the concept entirely | Never without a concept-level ADR and user approval |

## MVP-done checklist

- [ ] Poller + idempotent ingest + evidence capture running on RansomLook
      (private repo)
- [ ] Sector classification with evidenced steps; review queue triaged;
      coverage boundary published
- [ ] Incidents resolving with rationales; confidence assessments explainable
      end to end; victim-acknowledged statuses sourced
- [ ] Correction + de-listing propagation demonstrated on simulated inputs
      (aggregate recomputation + ledger)
- [ ] Public research surface + JSON aggregate export live, with claim-framing,
      attribution, and the name-scan gate passing
- [ ] Evidence manifest published and retrieval workflow verified end to end
- [ ] ransomwatch baseline loaded (if proposal 8 accepted)
- [ ] Open decisions resolved by the user
- [ ] Lawful-basis memo written and reviewed (launch gate)
- [ ] RansomLook terms re-verified at build time
