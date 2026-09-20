# xevents — MVP scope

**Status:** PROPOSAL, 2026-09-18. Nothing in this file is approved until the
user signs off. The items in `docs/open-decisions.md` also gate parts of
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

- Scheduled poller against RansomLook's no-key public API (ADR 0002).
- **Idempotent ingest.** Every source item carries a stable `source_item_key`
  (group + victim + URL). Re-polls update `listing_state.last_seen`; they
  never create duplicate observations (data-model.md: `listing_state`).
- Every genuinely new item → one immutable observation: `subject_raw`
  verbatim, `source_claimed_at` from RansomLook's `discovered`, raw payload
  stored, pipeline version recorded.
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
- **Explicitly:** with one source there is no cross-source reconciliation.
  MVP "reconciliation" means dedup, repeat-listing grouping, and correction
  handling — not multi-vantage corroboration. Cross-source reconciliation is
  non-goal 3.
- **Acceptance:** the same victim relisted by the same group resolves to one
  incident; every membership link carries a rationale a non-author can follow.

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
- [ ] Open decisions resolved by the user
- [ ] GLEIF license text verified; RansomLook terms re-verified at build time
