# xevents — AGENTS.md

Operating manual for anyone (human or agent) working on this project. Concrete
rules; `docs/` is the theory, `research/landscape-report.md` is the evidence.

## What xevents is

- An evidence-first incident-intelligence application that records, preserves, and
  reconciles **public** claims about cyber incidents, starting with ransomware
  victim listings and breach disclosures.
- Every claim stays attached to its source, timestamp, entity details, supporting
  evidence, confidence, and correction history.
- Observations resolve into cautious, explainable incident records.
- Long-term goal: a public research surface for defensible trend analysis —
  new victims, disclosure patterns by sector, compromise-to-disclosure lag,
  exploited-vuln mentions, vendor concentration, vertical exposure.
- **The MVP is defined in `docs/mvp-scope.md`: one licensing-clean source
  (RansomLook) end to end.** The research surface, all other sources, and
  everything in the non-goals table are explicitly post-MVP. If it is not in
  the MVP scope doc, it is not approved work.

## Scope discipline

- The only approved build target is `docs/mvp-scope.md`.
- Lifting any non-goal, adding any source, or changing any `proposed` ADR
  requires a **new ADR and the user's explicit approval**. An ADR without
  user approval is a proposal, not a decision — all seven ADRs are currently
  `proposed (pending user redline)`.
- A new feature proposal must cite which MVP acceptance criterion it serves.
  If it serves none, reject it or park it as a post-MVP ADR proposal.
- The items in `docs/open-decisions.md` are undecided. Never resolve
  them by assumption, and flag any work that depends on a particular answer.

## What xevents is NOT

- Not a breach verification service. We do not confirm intrusions; we record
  claims about them.
- Not a leak-data mirror. We never acquire, host, or redistribute stolen content
  or personal data. We index publicly visible listing metadata and screenshots
  only.
- Not a second ransomware.live. We do not derive bulk datasets from
  terms-restricted aggregators (see Licensing below).
- Not an indicator platform. MISP/OpenCTI cover IoCs; xevents covers incidents
  and the claims made about them.

## The doctrine (non-negotiable)

1. **Observations are immutable.** Once written, an observation never changes.
   If it was wrong, append a correction event.
2. **Echoes are not votes.** Repeated or re-aggregated claims do not corroborate
   each other. Confidence counts independence classes, not raw source count.
   (xfeeds heritage: independence classes over file counts.)
3. **Absence is not evidence.** A source going silent — takedown, seizure,
   scraper failure — means "not observed," never "inactive."
4. **Every claim is framed.** Public-facing text always says whose claim it is.
   Never present an attacker's listing as an established breach.
5. **Corrections are load-bearing.** The retraction ledger is a first-class
   output, not an afterthought.

## Source-of-truth rules

Authoritative reasoning: ADR 0001. This section is the rules.

- The observation log is the system of record. Incident records, entity tables,
  and confidence assessments are derived and must be re-derivable from
  observations + correction events + the recorded model version.
- Correction events are append-only. Incident records and entity resolution may
  be revised, but every revision carries a rationale and links the
  observations/corrections that caused it.
- Confidence assessments are versioned and superseded, never edited in place.
  Record the model version, the inputs hash, and the contributing independence
  classes.

## Licensing and ToS discipline

Authoritative reasoning: ADR 0002. This section is the rules.

- Ingest tiers come from the landscape report (`research/landscape-report.md`):
  FREELY USABLE / PAID / RESTRICTED. **Build the stored and published dataset
  only on FREELY USABLE sources.**
- **ransomware.live is excluded as a dependency.** No storage of its data at
  scale, no republication, no build-time or run-time dependency. Whether even
  manual query-level cross-checks are acceptable is **UNDECIDED**
  (docs/open-decisions.md #2) — until decided, no contact at all.
- **MVP builds on exactly one source: RansomLook** (CC BY 4.0). Attribution
  is mandatory; keep a per-source attribution record in the source registry.
  Adding a second source needs a new ADR + user approval.
- **ecrime.ch is paid-only** ($2,799/yr Pro; commercial re-use needs the
  custom tier). Paid enrichment option, never a foundation.
- Default for any new source: **RESTRICTED until a human clears it.** Verify
  terms before ingesting any new source; re-verify at build time — terms
  change. (Landscape is a September 2026 snapshot.)
- Legal posture notes in ADR 0002 / landscape §6 are reported considerations,
  not legal advice. Independent primary collection sidesteps aggregator
  database rights; get written permission before touching any RESTRICTED
  source at scale.
- Never interact with criminal infrastructure. Passive collection only: no
  engagement with threat actors, no negotiation chats, no probing leak sites.

## Evidence-handling rules

Authoritative reasoning: ADR 0003. This section is the rules.

- **Capture at ingest.** Every observation gets its evidence then and there:
  timestamped screenshot + raw HTML/metadata at minimum; WARC where feasible.
- **Content-addressed storage.** Evidence artifacts are stored by SHA-256; the
  hash is recorded on the observation.
- **No stolen content, no personal data.** Redact or exclude personal data
  (names, emails, phone numbers in ransom notes or screenshots) before storage.
  Index metadata, not payloads.
- **Retention is documented and applied.** Evidence for retracted or false
  claims is retained alongside its correction — deletion would destroy the audit
  trail.
- If a source's ToS forbids archival copying, do not archive it. Record the ToS
  constraint as an observation and fall back to linking with a fetched-at
  timestamp.
- **Pre-public-surface gate:** the written lawful-basis / public-interest
  research justification must exist and be reviewed before serving data
  publicly. No memo, no public surface.

## Scar tissue — known traps

1. **Licensing is the binding constraint**, not engineering. The richest free
   feed cannot be republished. Verify terms before ingesting any new source;
   when in doubt, treat as RESTRICTED until a human clears it.
2. **Hoax injection is live.** Maine's AG register went offline June 12, 2026
   after fabricated VRChat (2.4M claimed) and Discord (10M claimed) filings.
   Treat every inbound claim as attacker- or submitter-asserted until evidenced
   otherwise.
3. **Misnaming happens.** Clop listed "Thames Water"; the victim was South
   Staffs Water. Entity resolution must tolerate and record misnamings, not
   silently fix them.
4. **De-listings are invisible.** No source publishes removal history. Re-poll
   and diff; treat removals as first-class observations (payment, false claim,
   or takedown).
5. **EDGAR has no structured Item 1.05 field.** Item filtering is text search
   within 8-K results. The 4-day clock runs from the unobservable materiality
   determination — never compute compromise-to-disclosure lag from EDGAR alone.
6. **SMEs are a coverage boundary.** Free entity sources (SEC ~8k issuers, GLEIF
   ~3.36M mostly large/regulated entities, Wikidata's notable-company bias)
   systematically miss small-business victims. Document the boundary; resolve
   what you can; queue the rest for human review.
7. **Tor volatility.** Leak sites die, rebrand (DarkSide→BlackMatter→ALPHV;
   Royal→BlackSuit; Hunters International→World Leaks), and get seized
   (LockBit/Cronos). Track group-identity chains as observations. Silence is
   not inactivity.
8. **Rate limits are real.** EDGAR: 10 req/s, descriptive User-Agent with
   contact info or 403. GLEIF: ~60 req/min observed (unverified as official) —
   mirror the Golden Copy for batch work. Wikidata: 5 parallel queries per IP,
   60s timeout — use dumps for bulk.
9. **No off-the-shelf evidence archiving exists.** We are building it. Keep the
   design simple enough to audit.
10. **The correction channel ships on day one.** Published dispute/correction
    process before the public research surface. Reference posture: GalaxyWarden's
    published takedown policy; ransomware.live's §9 dispute process.

## Dependency discipline

- Pin everything. Lockfile with hashes; no floating version ranges on ingest
  dependencies.
- Verify the license of every dependency and data source before use. Record it
  in the source registry.
- **AGPL awareness:** RansomLook's platform code and CIRCL's AIL Framework are
  AGPL-3.0. Their *data* is CC BY 4.0 (RansomLook) — consuming the API/feed does
  not trigger AGPL; embedding or modifying their *code* does. Keep the boundary
  clean: consume feeds, don't fork AGPL code into this codebase without a
  deliberate decision recorded in an ADR.
- No mystery deps. If a library's provenance can't be established, don't add it.

## Determinism and reproducibility

- Ingest pipelines are deterministic: same inputs, same observations. Record the
  pipeline version on every observation.
- Entity resolution and confidence assessments record the model/code version
  that produced them.
- Never mutate history to "fix" a bug in derived data — re-derive, record a new
  version, and link the correction.

## Docs discipline

- Every ADR cites the landscape-report finding it rests on. Where the research
  was inconclusive, mark it UNVERIFIED and name what would settle it.
- Docs before code for anything touching the data model, licensing posture, or
  the public surface.
- The landscape report is a snapshot (September 17, 2026). Re-verify source
  terms before building; terms change.
