# xevents — Glossary

Precise working definitions. This file is the authoritative home for what
terms mean; ADRs and the data model use them without redefining them. Where a
term has an ADR, the ADR governs the mechanics and this file governs the
meaning.

## Core record types

- **observation** — A single, immutable record of one source's claim at one
  time: source, two timestamps (`observed_at`, `source_claimed_at`), entity
  details exactly as given, raw payload, evidence artifacts, pipeline
  version. The system of record. Never edited; corrected only by appending
  correction events. One observation per (source, item, first-seen):
  re-polls update `listing_state`, they do not duplicate observations.
  (ADR 0001)
- **claim** — The assertion inside an observation (e.g. "ransomware group X
  lists victim Y"). A claim is *attributed*, never established fact, until an
  incident record with a confidence assessment says otherwise.
- **claim type** — The controlled vocabulary classifying what kind of claim
  an observation carries: `ransomware_listing`, `breach_disclosure`,
  `company_statement`, `vuln_exploit_claim`, `enrichment`, `removal`,
  `correction_notice`, `other`. (data-model.md)
- **incident** — A resolved, mutable record grouping related observations
  about the same real-world event, with typed membership links, a status
  (`candidate`/`active`/`contested`/`retracted`), and a versioned confidence
  assessment. Incident IDs are stable across re-resolution. (ADR 0001)
- **incident membership** — A typed, immutable link between one observation
  and one incident: `supports`, `duplicates`, `refutes`, `corrects`, each
  with a rationale. A changed judgment is a new row, never an edit.
  (ADR 0001)
- **entity** — A canonicalized real-world subject: a victim organization, a
  subsidiary, a municipality, a threat group, a vendor, a CVE. Resolved
  probabilistically from observation-level strings; carries a resolution
  confidence and model version. Merges and splits are correction events.
  (ADR 0005)
- **alias** — A name variant tied to an entity with provenance (legal name,
  DBA, domain, abbreviation, **misnaming**). Misnamings are recorded as
  aliases, never silently fixed. Threat-group rebrands are aliases too
  (e.g. Royal→BlackSuit). (ADR 0005)
- **evidence** — Preserved proof of what a source showed at observation
  time: at minimum a timestamped screenshot plus raw HTML/metadata,
  content-addressed by SHA-256. Captured at ingest; leak sites die.
  (ADR 0003)
- **evidence artifact** — One stored unit of evidence linked to an
  observation. Immutable; a re-capture is a new artifact, never an
  overwrite.
- **correction** — An append-only event revising the record: `correction`,
  `denial`, `removal`, `retraction`, `dispute_opened`, `dispute_resolved`.
  Corrections attach to observations, incidents, entities, or aliases; they
  never rewrite history. The correction ledger is a first-class public
  output. (ADR 0004)
- **confidence** — A band (`unverified`/`low`/`moderate`/`high`/`disputed` —
  set PROPOSED, pending open decision #1) assigned to an incident or
  observation by a versioned model, always accompanied by a human-readable
  rationale, the contributing independence classes, and an inputs hash.
  Assessments are superseded, never edited. Model weights are internal
  inputs; the band is the published output. (ADR 0006)
- **independence class** — A grouping of sources by shared provenance
  (`tor_primary`, `aggregator_ransomlook`, `regulatory_filing`, …).
  Confidence counts each class once: echoed claims are one vote, not many.
  The xfeeds heritage — corroboration by independence, not by count. The
  class set is versioned per model version. (ADR 0006)

## Sources and collection

- **source** — A registered ingest origin with a kind, a licensing tier
  (`freely_usable`/`paid`/`restricted`), license terms, attribution
  requirements, access method, and known limitations. Only `freely_usable`
  sources feed the stored/published dataset. (ADR 0002)
- **licensing tier** — `freely_usable` (public, republication-safe terms),
  `paid` (commercial tier required), `restricted` (key-gated, ToS-limited,
  offline, or scrape-only-with-friction). Default for any new source is
  `restricted` until a human clears it. (ADR 0002)
- **leak site (DLS)** — A ransomware group's data-leak site, typically a Tor
  hidden service, where victim listings are published. Primary source for
  `tor_primary` observations; volatile by nature.
- **source item key** — The stable identity of one listed item within one
  source (group + victim + URL). Used for idempotent ingest and for
  re-poll/diff de-listing detection. Stored on the observation and tracked
  in `listing_state`. (ADR 0007; data-model.md)
- **listing state** — Per-source-item polling memory: first seen, last seen,
  and whether the item is currently listed. What makes re-polling
  idempotent and removals detectable. (ADR 0007; data-model.md)
- **de-listing** — The observed removal of a previously listed victim claim
  from a leak site or aggregator. Detected by re-polling and diffing;
  recorded as a `removal` observation and correction event. Ambiguous
  signal: may indicate payment, a pulled false claim, or a takedown — never
  an automatic retraction. (ADR 0007)
- **disclosure** — A breach-disclosure claim from a regulatory or corporate
  channel: SEC 8-K Item 1.05/8.01, state AG notice, HHS OCR portal entry,
  company statement. Disclosures are observations like any other —
  attributed, evidenced, reconcilable. Breach-disclosure *ingest* is
  post-MVP (docs/mvp-scope.md, non-goal 2).

## Identity and classification

- **threat group** — A ransomware operation as an entity (`entity_kind=
  threat_group`). Group identity is tracked through rebrands and seizures
  via aliases and group-identity observations; a listing that "disappears"
  from one group identity and reappears under a successor is one chain, not
  two incidents. (ADRs 0005, 0007)
- **vendor** — A third-party product or service provider implicated in an
  incident (`entity_kind=vendor`). The basis for vendor-concentration
  analysis: which vendors' products appear across incidents.
- **sector** — An industry classification of a victim entity, carried on the
  NAICS spine (`entity.naics_code`). Sector mapping (NAICS/Wikidata/OpenFIGI
  enrichment) is post-MVP (docs/mvp-scope.md, non-goal 5).
- **coverage boundary** — The honestly documented limit of what xevents
  resolves well (public companies, LEI holders, notable firms) versus what
  it systematically misses (SMEs without LEIs, Wikidata entries, or SEC
  filings; non-Tor extortion channels; municipalities/schools/hospitals
  without identifiers). Published as a versioned public statement; fed by
  `source.known_limitations`. A documented limitation, not a hidden one.
  (ADR 0005; docs/mvp-scope.md item 7)
- **review task** — A unit of human review: an ambiguous entity match, an
  unresolvable subject, a contested correction. Queued, worked, and resolved
  with a recorded outcome — the queue itself is auditable. In MVP the
  reviewer is the project lead. (ADR 0005; data-model.md)

## Time and analytics

- **two clocks** — `observed_at` (when xevents recorded it; immutable) vs
  `source_claimed_at` (when the source says the event occurred; nullable).
  Kept distinct everywhere. What makes honest lag computation possible.
  (ADR 0006)
- **incident timeline** — The four anchor events recorded as separate
  observations, each with its own provenance: **compromise** (intrusion
  occurred), **listing** (victim appeared on a leak site), **notification**
  (affected parties / regulators notified), **disclosure** (public
  acknowledgment: 8-K, AG notice, company statement). Compromise-to-disclosure
  lag is computed only where both anchors are evidenced; the rest is
  unknown, never imputed. EDGAR's 4-day clock runs from the unobservable
  materiality determination — lag is never computed from EDGAR alone.
  (ADR 0006)
- **vulnerability linkage** — The mapping from a CVE (notably CISA KEV
  entries flagged for ransomware use) to the specific incidents where it
  was exploited. CVEs are entities (`entity_kind=cve`); KEV rows become
  `vuln_exploit_claim` observations; the CVE→incident link is an
  `incident_membership` row when an incident's observations reference the
  CVE. KEV ingest is post-MVP (docs/mvp-scope.md, non-goal 6).
- **newly reported victim** — A victim entity whose incident has the most
  recent `first_observed_at` in the corpus. A corpus query, not a push
  feature in MVP (push/alerting is non-goal 9).
- **vertical exposure** — Sector-pattern analysis over the incident corpus
  (e.g. disclosure patterns by sector). Long-term analytic; post-MVP
  (docs/mvp-scope.md, non-goal 4).
- **vendor concentration** — Analysis of which vendors' products recur across
  incidents. Long-term analytic; post-MVP (docs/mvp-scope.md, non-goal 4).

## Surfaces and process

- **operational surface** — The MVP's read/query layer: incident list and
  detail, correction-ledger view, JSON export. Serves the evidence trail,
  not analytics. (docs/mvp-scope.md item 7)
- **research surface (long-term)** — The public analytics layer: trend
  queries over the incident corpus (new victims, sector patterns, lag,
  vuln mentions, vendor concentration, vertical exposure). Explicitly
  post-MVP (docs/mvp-scope.md, non-goal 4). Not built, not promised, until
  its own ADR.
- **model version** — A registered version of any versioned component
  (ingest pipeline, entity resolution, incident resolution, confidence
  model), recording its parameters — including the independence-class set —
  so every derived record is re-derivable. (data-model.md: `model_version`)
- **claim framing** — The mandatory practice that every public-facing
  rendering states whose claim it is. Never present an attacker's listing
  as an established breach. (ADR 0004)
