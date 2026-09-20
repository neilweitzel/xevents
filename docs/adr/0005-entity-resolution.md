# ADR 0005: Entity-resolution strategy

- Status: proposed (pending user redline)
- Date: 2026-09-18
- Deciders: project lead

## Context

Victim identity arrives as messy strings: "Acme Corp" vs "acme.com" vs a
subsidiary name vs an outright misnaming (Clop's "Thames Water" for South
Staffs Water). Reconciling observations into incident records (ADR 0001)
requires resolving these strings to canonical entities — without pretending
to certainty we don't have.

The free canonicalization landscape (landscape §4):

- **SEC tickers + CIK lookup** (`company_tickers.json`, `cik-lookup-data.txt`):
  free, U.S. public domain; resolves ~8k exchange-traded issuers to legal name
  + CIK, and SEC submissions carry **SIC industry codes** — a free
  company→sector signal for filers. 10 req/s, descriptive User-Agent.
- **GLEIF / LEI**: ~3.36M records (June 2026), 236 countries; free no-key API
  with fuzzy legal-name search; Level 2 parent/subsidiary data resolves the
  subsidiary-vs-parent ambiguity; downloadable "Golden Copy" updated 3× daily
  for local mirroring. **Redistribution license text UNVERIFIED** — verify on
  gleif.org legal pages before building the public surface on it.
- **Wikidata**: CC0; official website (P856), industry (P452), ticker (P249),
  parent/subsidiary (P749/P355), multilingual aliases. Crowd-sourced and
  biased toward notable/large companies. Dumps for bulk; SPARQL for ad-hoc
  (5 parallel/IP, 60s timeout).
- **Census NAICS 2022 tables**: free public-domain taxonomy, but **no free
  official per-company NAICS lookup API exists** — usable as a local sector
  spine, not as a resolver.
- **OpenFIGI**: free API key (25 req/min anonymous, 250/min keyed); FIGIs are
  free to use and redistribute — but identify *instruments*, not companies;
  useful only as corroboration for public-company victims.

Excluded: **OpenCorporates** (free API tier dead; from £2,250/yr; public-benefit
grant possible but not relied upon), **Clearbit** (dead as a standalone API),
**Diffbot/FullContact** (paid).

**Residual gap:** none of the free sources reliably identify SMEs — no LEI, no
Wikidata entry, no SEC filing. Small-business victims are systematically missed.
This is a documented coverage boundary, not a bug to hide.

## Decision

1. **Pipeline order** (cheapest and most authoritative first):
   1. Local normalization (own code): lowercase/strip, legal-suffix removal
      (LLC, Inc., GmbH, Ltd., S.A.S., …), abbreviation expansion, TLD/URL
      extraction from leak posts.
   2. SEC tickers + CIK lookup: exact/fuzzy match — resolves public-company
      victims to CIK + legal name + SIC sector at zero API cost.
   3. GLEIF API / mirrored Golden Copy: fuzzy legal-name search for private
      companies; parent/subsidiary data; entity status flags
      (ISSUED/LAPSED/MERGED) feed the confidence model.
   4. Wikidata: secondary name/alias match; P856 website cross-check against
      domains in breach notices; P452 industry as a sector signal.
   5. Census NAICS 2022 tables embedded locally as the sector spine;
      SIC→NAICS concordances and Wikidata-industry→NAICS recorded as
      low-confidence heuristic mappings.
   6. OpenFIGI: ticker/ISIN→issuer-name corroboration for public-company
      victims.
   **MVP subset:** steps 1–3 plus the alias table and human-review queue only
   (docs/mvp-scope.md item 3). Wikidata, NAICS sector mapping, and OpenFIGI
   are deferred to post-MVP — they serve the research surface, not the core
   loop.
2. **Every enrichment step is recorded as an observation** — source, timestamp,
   confidence. Entity resolution is part of the evidence trail, not a black box.
3. **Local alias table**, seeded from correction history: misnamings and
   variants become aliases linked to entities, never silent fixes. "Thames
   Water (as listed by Clop)" remains visible as an alias with its provenance.
4. **Human-review queue** for ambiguous matches and SME cases the pipeline
   cannot resolve. Queue is modeled (`review_task`, data-model.md); tasks are
   resolved with a recorded outcome, never silently dropped. In MVP the
   reviewer is the project lead.
5. **Coverage boundary documented honestly** in public docs: which entity
   classes resolve well (public companies, LEI holders, notable firms) and
   which do not (SMEs, municipalities, schools, hospitals without LEIs).
   Required contents are specified in data-model.md ("Coverage boundary").
6. Before building the public surface on GLEIF data, **verify the GLEIF
   redistribution license text** (flagged UNVERIFIED in research). This is an
   MVP launch gate (docs/mvp-scope.md).
7. **Threat-group identity is resolved through aliases, not the company
   pipeline.** Groups are entities (`entity_kind=threat_group`); rebrands,
   seizures, and successor claims (DarkSide→BlackMatter→ALPHV;
   Royal→BlackSuit; Hunters International→World Leaks) are recorded as
   aliases and group-identity observations (ADR 0007), sourced from
   RansomLook group profiles, the deepdarkCTI directory, and analyst
   reporting. No automated group-resolution pipeline in MVP — group aliasing
   is observation-driven and human-confirmed.

## Consequences

- Resolution is probabilistic and versioned: entities carry
  `resolution_confidence` and `resolution_model_version`; merges and splits
  are correction events (ADR 0004), not silent updates.
- Some victims remain unresolved strings indefinitely. That is acceptable and
  documented — an honest "unresolved" beats a confident mis-resolution.
- Batch work mirrors the Golden Copy and Wikidata dumps locally rather than
  hammering rate-limited APIs.

## Research basis

- Landscape §4.1–§4.6 (entity-resolution resources; recommended free-tier
  pipeline; residual SME gap).
- Landscape §6.3 (Clop/Thames Water misnaming).
- UNVERIFIED: GLEIF redistribution license text; GLEIF ~60 req/min as an
  official limit (observed, not confirmed); canonical machine-readable
  Fortune 500 endpoint and license terms (candidate, not relied upon).
