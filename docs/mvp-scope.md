# xevents — MVP scope

**Status:** PROPOSAL, 2026-09-18. Nothing in this file is approved until the
user signs off. The four items in `docs/open-decisions.md` also gate parts of
this scope; wherever this document touches one, it says so.

## What the MVP proves

That the core loop works end to end on real data, at the highest quality bar:

**ingest → immutable observation + captured evidence → entity resolution →
incident resolution → explainable confidence → correction handling →
queryable output.**

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
  (null only when nothing was redacted).

### 3. Entity resolution (MVP subset)

- Pipeline: local normalization → SEC tickers/CIK → GLEIF → local alias
  table → human-review queue (ADR 0005). The reviewer is the project lead;
  the queue is triaged before MVP sign-off.
- Every enrichment step recorded as an observation (`claim_type=enrichment`).
  Misnamings become aliases, never silent fixes.
- **Deferred to post-MVP:** Wikidata enrichment, NAICS sector mapping,
  OpenFIGI corroboration (see non-goals 5).
- **Launch gate:** the GLEIF redistribution license text is UNVERIFIED in
  research — it must be verified before building on GLEIF data, not after.
- **Acceptance:** every resolution attempt is evidenced as an observation;
  unresolvable subjects keep `entity_id` null with the raw string preserved;
  the review queue is empty or explicitly deferred; the coverage-boundary
  statement is published (see 7).

### 4. Observation → incident resolution (within-source)

- Repeat listings and re-observations group into incidents via typed
  `incident_membership` rows with human-readable rationales (ADR 0001).
  Incident IDs stable; resolution model version recorded in the
  `model_version` registry (data-model.md).
- **Grouping rule (MVP).** Observations group into one incident when they
  share the normalized threat-group string and resolve to the same victim
  entity (or the same unresolvable `subject_raw` string). Grouping rationale
  is generated from the rule plus the specific evidence (e.g. "same
  normalized group 'qilin', same resolved entity ACME Corp (CIK 000123);
  3 observations, 2026-09-10…2026-09-18"); ambiguous cases go to the review
  queue instead of auto-grouping.
- **Relist after removal.** A relist following a `removed_confirmed`
  listing state opens a **new candidate incident**, linked to the prior
  incident in the rationale. Re-compromise is a distinct event until
  evidenced otherwise; the reviewer confirms or merges. (ADR 0007: removal
  ≠ retraction.)
- **Victim rename mid-stream.** A changed `subject_raw` for the same
  underlying org becomes an `alias` row with provenance; the incident keeps
  its ID and the membership rationale notes the rename.
- **Explicitly:** with one source there is no cross-source reconciliation.
  MVP "reconciliation" means dedup, repeat-listing grouping, and correction
  handling — not multi-vantage corroboration. Cross-source reconciliation is
  non-goal 3.
- **Acceptance:** the same victim relisted by the same group resolves to one
  incident; a relist-after-removal opens a linked candidate incident; every
  membership link carries a rationale a non-author can follow.

### 5. Explainable confidence

- Band + rationale + contributing independence classes + inputs hash on every
  incident with ≥1 observation (ADR 0006). Assessments superseded, never
  edited. Weights are internal model inputs; the band is the published output.
- **Honest single-source behavior:** with one independence class in play,
  most incidents assess `unverified` or `low`. The model must not manufacture
  confidence out of repetition.
- Band set pending open decision #1.
- **Acceptance:** any incident's band traces to its observations, classes,
  and rationale with no manual reconstruction.

### 6. Correction ledger + dispute channel + de-listing detection

- Append-only correction events (`correction`/`denial`/`removal`/`retraction`/
  `dispute_opened`/`dispute_resolved`); claim-framing mandatory on all
  outputs (ADR 0004). Dispute handling is manual in MVP.
- De-listing detection: re-poll + diff against `listing_state`; removal
  observations feed incident review but **never auto-retract** (ADR 0007).
  Detection threshold pending open decision #3. Dispute SLA pending open
  decision #4.
- **Acceptance:** a simulated victim denial and a simulated de-listing both
  propagate end to end — observation → correction event → re-resolution →
  superseded assessment — with the full history visible and nothing deleted.

### 7. Minimal read/query surface ("operational surface")

- Incident list with filters (entity, threat group, date range, confidence
  band, status); incident detail (observations, evidence, corrections,
  confidence rationale); correction-ledger view; JSON export of incidents +
  observations.
- Attribution strings rendered wherever CC BY 4.0-derived content appears.
  The coverage-boundary statement is published on the surface (required
  contents: entity classes resolved well vs missed, source coverage windows,
  known blind spots — see data-model.md).
- This is the **operational surface**, not the research surface (glossary).
  No trend analytics in MVP.
- **Acceptance:** everything above reachable without manual DB queries;
  exported JSON re-derives from the observation log alone.

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
| 3 | Cross-source claim reconciliation | Requires ≥2 sources; MVP reconciliation is within-source only | When non-goal 2 is lifted |
| 4 | Public research/analytics surface — trend dashboards, lag analytics, sector patterns, vendor concentration, victim counts | Analytics over a thin corpus mislead; the operational surface is the MVP output | Post-MVP ADR, gated on a corpus size/quality bar set by the user |
| 5 | Sector/vertical classification (NAICS mapping, Wikidata enrichment, OpenFIGI corroboration) | Serves the research surface (non-goal 4), not the core loop | With non-goal 4 |
| 6 | CVE→incident linkage analytics | Needs KEV ingest (non-goal 2) plus an incident corpus; the schema already reserves `entity_kind=cve` and `claim_type=vuln_exploit_claim` | With non-goal 2, via its own ADR |
| 7 | STIX 2.1 export / OpenCTI connector | Interoperability, not core value | Post-MVP ADR on user request |
| 8 | Automated dispute handling | Volume doesn't justify it; manual keeps quality highest | Post-MVP, on dispute volume |
| 9 | Push/alerting ("new victim" notifications) | A distribution feature, not evidence infrastructure | Post-MVP ADR |
| 10 | Paid or restricted sources (ecrime.ch, ransomware.live PRO, or any RESTRICTED tier) | Licensing gates, not schedule gates | Only with written permission or a paid tier, plus user approval |
| 11 | IoC feeds, victim notification workflows, ransom negotiation, threat-actor attribution beyond group identity | Not incident-claim intelligence; outside the concept entirely | Never without a concept-level ADR and user approval |

## MVP-done checklist

- [ ] Poller + idempotent ingest + evidence capture running on RansomLook
- [ ] Entity resolution with evidenced steps; review queue triaged; coverage
      boundary published
- [ ] Incidents resolving with rationales; confidence assessments explainable
      end to end
- [ ] Correction + de-listing propagation demonstrated on simulated inputs
- [ ] Operational query surface + JSON export live, with claim-framing and
      attribution
- [ ] ransomwatch baseline loaded (if proposal 8 accepted)
- [ ] Open decisions #1–#4 resolved by the user
- [ ] GLEIF license text verified; RansomLook terms re-verified at build time
