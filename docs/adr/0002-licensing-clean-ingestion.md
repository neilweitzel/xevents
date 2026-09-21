# ADR 0002: Licensing-clean ingestion architecture

- Status: proposed (pending user redline)
- Date: 2026-09-18
- Deciders: project lead

## Context

Licensing, not engineering, is the binding constraint on xevents' data supply
(landscape §7.1). The findings:

- **ransomware.live** has the richest free victim metadata (country, sector,
  press, 8-K links, screenshots) but its v2 API is "Personal use only … not
  intended for corporate or business use," and its T&C (fetched 2026-09-17)
  expressly bars "Redistribution as an API" and "Raw data publishing" (§4) and
  unapproved commercial use (§5). xevents cannot re-serve its dataset without
  written permission.
- **ecrime.ch** is paid: $2,799/yr Professional tier; commercial re-use of data
  requires the custom commercial tier.
- **EU sui generis database right** protects databases built with substantial
  investment for 15 years; ransomware.live is French-law governed, squarely in
  this regime. Facts (victim names, dates) are not copyrightable, but bulk
  extraction of an aggregator's database is the risk zone.
- Clean alternatives exist: **RansomLook** (CC BY 4.0 on all content — website,
  API, datasets — confirmed in writing by maintainers; no-key API; open-source
  platform), **ransomfeed.it** (free and open to all "including integration into
  commercial platforms"; 60-minute scrape cadence; analyst-added country),
  **SEC EDGAR** (U.S. public domain; 10 req/s with descriptive User-Agent),
  **CA AG** (CSV download) and **WA AG** (Socrata API + CSV), **HHS OCR portal**
  (scrape-only; ~70 requests for the full archive via the documented community
  pattern), **HIBP keyless breach catalog** (CC BY 4.0), **CISA KEV** (no-auth
  JSON/CSV), and the frozen **ransomwatch** 2020–2025 archive (Unlicense).
- In practice most researchers rely on aggregators (Emsisoft's census used
  RansomLook + ransomware.live), but aggregator dependence is exactly what the
  ToS findings forbid us from building on.

## Decision

1. **Foundation sources** — the only sources whose data may be stored at scale
   and republished in xevents outputs: RansomLook API, ransomfeed.it
   RSS/API, SEC EDGAR (efts full-text search, submissions JSON, bulk ZIP), CA
   AG CSV, WA AG Socrata datasets (`sb4j-ca4h`, `padd-mby7`), HHS OCR portal
   (scrape pattern), HIBP breach catalog, CISA KEV feed, ransomwatch frozen
   archive, plus our own primary collection.
2. **ransomware.live is explicitly excluded as a dependency.** No storage of
   its data at scale, no republication, no build-time or run-time dependency.
   **UNDECIDED (open-decisions.md #2):** whether manual, query-level
   cross-checks of individual facts are acceptable. Until the user decides,
   treat any contact as prohibited: no queries, manual or automated. (If the
   user approves the carve-out, the rule becomes: minimal, documented, never
   automated at bulk — verifying a single fact ≠ extracting the database,
   but the line is gray.)
3. **MVP pins exactly one foundation source: RansomLook.** The full
   foundation-source list above is the approved *pool*; MVP builds on one
   (docs/mvp-scope.md). Adding a second source is a scope change: new ADR +
   user approval.
4. **Long-term primary: our own Tor crawler.** Independent primary DLS
   collection sidesteps aggregator database rights entirely and is the only
   licensing-safe way to close the metadata gap (RansomLook, the cleanest open
   feed, has the sparsest metadata — no country/sector fields). Seed with the
   deepdarkCTI directory; use CIRCL's AIL Framework (AGPL-3.0) as a reference
   implementation, not as embedded code (AGENTS.md: consume feeds, don't fork
   AGPL code without a deliberate ADR). The crawler must handle onion
   discovery, site volatility, and rebrand/successor-group tracking from the
   start — this is the project's biggest engineering investment and its
   biggest legal protection, in one.
5. **Attribution registry.** Every CC BY 4.0 source (RansomLook, HIBP catalog)
   gets visible attribution; the source registry records license text and
   attribution requirements per source.
6. **Enrichment from RESTRICTED sources** (ransomware.live PRO, ecrime.ch) is
   a future option gated on written permission or a paid tier — not a design
   dependency today.

## Consequences

- Metadata will be sparser than ransomware.live's at first (no country/sector
  from RansomLook). In MVP, compensate only with our own enrichment — each
  enrichment recorded as an observation with source and confidence (ADR 0005).
  ransomfeed.it's analyst-added country becomes available when a second source
  is approved (docs/mvp-scope.md, non-goal 2).
- The Tor crawler is a real operations commitment: concurrent runners, queue
  management, storage, onion discovery, anti-volatility engineering. Passive
  collection only; no interaction with criminal infrastructure.
- Any new source goes through a license check before ingest; default to
  RESTRICTED until a human clears it.

## Why RansomLook for the MVP (recorded 2026-09-20)

The MVP pins one foundation source (decision item 3 above); the rationale
was never written down. RansomLook, not ransomfeed.it, is first because:

1. **Strongest licensing certainty.** CC BY 4.0 confirmed *in writing* by
   the maintainers (ransomlook issue #590) covers website, API responses,
   and datasets — including the per-post screenshots, which are the MVP's
   evidence-capture path. No other free aggregator offers that in writing.
2. **Simplest integration.** No-key public API with documented endpoints
   (docs/source-spec-ransomlook.md, verified live 2026-09-20).
3. **Self-auditable platform.** The full RansomLook platform is open source
   (AGPL-3.0); its scraping and parsing behavior can be inspected, not just
   trusted.
4. **ransomfeed.it stays in the pool as the second source** — its
   analyst-moderated country enrichment is the documented answer to
   RansomLook's sparsest-metadata weakness (consequence 1 above), and its
   commercial-reuse terms are clear. It is deferred, not rejected:
   one source done well first (mvp-scope.md non-goal 2).

## Research basis

- Landscape §1.1 (RansomLook: CC BY 4.0, no-key API), §1.2 (ransomfeed.it
  commercial-reuse terms), §1.3 (ransomware.live v2 terms; 393 groups / 31,303
  victims per /v2/info 2026-08-29), §1.6 (ecrime.ch pricing/tiers).
- Landscape §6.2 (licensing/ToS: EU database right, hiQ v. LinkedIn scraping
  note — reported considerations, not legal advice).
- Landscape §6.1 (Tor collection practicalities; volatility, rebrands,
  takedowns 2024–2026), §8 (recommended ingestion architecture table).
- UNVERIFIED in research: ransomware.live v2 ~1 req/min rate limit (from
  third-party docs, not primary); ransomfeed.it exact API endpoints;
  RansomLook v1.9.0 "2,000 onion sites" claim. Verify before building ingest
  against them.

## Pivot note, 2026-09-21 (user decisions #8–#11)

The licensing doctrine is unchanged: RansomLook (CC BY 4.0) remains the
MVP's one source; ransomware.live remains excluded without written
permission. The pivot changes where licensed content lives:

- **Two-repo split.** Raw payloads and screenshots are ingested into
  `xevents-internal` (private) — archival of CC BY 4.0 material for
  research audit is permitted. The public repo (`xevents`) carries only
  derived, name-free sector aggregates plus the evidence manifest (hashes +
  provenance), with attribution strings satisfying CC BY 4.0 wherever
  RansomLook-derived content appears.
- **Attribution travels with the aggregate**, including into the JSON
  export (data-model.md export contract). An aggregate separated from the
  site must still attribute its sources.
- The naming policy (docs/naming-policy.md) is now the primary
  minimization measure; the lawful-basis memo template
  (docs/lawful-basis-memo-template.md) is rewritten around the two-repo
  split.

Status remains `proposed (pending user redline)`.
