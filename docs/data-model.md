# xevents — Data Model

**Status:** draft, 2026-09-18 (revised 2026-09-20: `poll_run` table,
`incident_membership` currency rule, JSON export contract, ADR 0008).
Implements ADRs 0001–0008. No code has been
written against this schema; field names are proposals for redline.

## Design principles

- **Observations are immutable** (ADR 0001). Corrections append; nothing
  rewrites history.
- **Everything derived is re-derivable**: incident records, entity resolution,
  and confidence assessments must be reproducible from observations +
  correction events + recorded model/pipeline versions.
- **Provenance is a field, not a comment**: every enrichment, resolution, and
  assessment records its source, timestamp, and version.
- Timestamps are UTC (`timestamptz`). Two clocks are kept distinct everywhere:
  when *we* observed/recorded something vs when the *source* claims it happened.
- **Versioned components are registered.** `pipeline_version`,
  `resolution_model_version`, and `model_version` text fields reference rows in
  the `model_version` registry — versions are records, not free text.
- **System of record is PostgreSQL** (ADR 0008). Column types below
  (`timestamptz`, `jsonb`, `text[]`, enums) are PostgreSQL types.

## Entities

### model_version

Registry of every versioned component, so derived records stay re-derivable.
**Append-only.**

| field | type | notes |
|---|---|---|
| `version` | text PK | e.g. `confidence/v0.3`, `ingest-ransomlook/v1.1` |
| `component` | enum | `ingest_pipeline` \| `entity_resolution` \| `incident_resolution` \| `confidence` |
| `params` | jsonb | the parameters that define this version — including the independence-class set for confidence models |
| `decided_at` | timestamptz | |
| `decided_by` | text | pipeline author, reviewer id, or ADR reference |
| `notes` | text | |

### source

The registry of ingest sources and their terms. Mutable; changes are
administrative, not historical.

| field | type | notes |
|---|---|---|
| `id` | uuid PK | stable |
| `name` | text | e.g. `ransomlook_api`, `ca_ag_csv`, `edgar_efts`, `tor_crawler` |
| `kind` | enum | `aggregator` \| `primary_crawler` \| `regulator` \| `company` \| `vuln_feed` \| `breach_catalog` \| `journalism` \| `directory` |
| `tier` | enum | `freely_usable` \| `paid` \| `restricted` (landscape classification) |
| `license_summary` | text | terms in plain language, with link to the source terms |
| `attribution_required` | bool | true for CC BY 4.0 sources (RansomLook, HIBP catalog) |
| `attribution_text` | text nullable | the exact attribution string to publish |
| `access_method` | text | endpoint / scrape pattern / bulk file |
| `rate_limit_note` | text | e.g. EDGAR 10 req/s + descriptive User-Agent |
| `status` | enum | `active` \| `degraded` \| `dead` |
| `last_polled_at` | timestamptz nullable | |
| `known_limitations` | text | feeds the published coverage-boundary statement (see below): what this source systematically misses or distorts |
| `notes` | text | |

### poll_run

Run-level auditing for every ingest execution (de-listing math, failure
debugging, and the "did the poller actually run?" question all hang off
this table). **Append-only**; the `source.last_polled_at` field is a cached
view of the latest successful run.

| field | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `source_id` | uuid FK → source | |
| `started_at` | timestamptz | |
| `finished_at` | timestamptz nullable | null while running |
| `status` | enum | `running` \| `ok` \| `partial` \| `error` |
| `items_seen` | integer | distinct source items encountered |
| `items_new` | integer | new observation rows written |
| `items_errored` | integer | items that failed ingest (each logged in `error_log`) |
| `poller_version` | text | registered in `model_version` |
| `error_log` | text nullable | run-level failures (timeouts, HTTP errors, parse faults) |
| `created_at` | timestamptz | |

### observation

One source's claim, seen once. **Immutable.** The system of record (ADR 0001).

| field | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `source_id` | uuid FK → source | |
| `independence_class` | enum | ADR 0006: `tor_primary` \| `aggregator_ransomlook` \| `aggregator_ransomfeed` \| `regulatory_filing` \| `company_statement` \| `breach_catalog` \| `analyst_journalism` \| `vuln_feed` (versioned set) |
| `observed_at` | timestamptz | when xevents recorded it — **immutable** |
| `source_claimed_at` | timestamptz nullable | when the source says the event occurred (e.g. RansomLook `discovered`); null when the source gives none |
| `claim_type` | enum | `ransomware_listing` \| `breach_disclosure` \| `company_statement` \| `vuln_exploit_claim` \| `enrichment` \| `removal` \| `correction_notice` \| `other` |
| `source_item_key` | text | stable per-source identity of the listed item (group + victim + URL); the dedup/diff key (see `listing_state`) |
| `subject_raw` | text | entity string exactly as the source gave it (e.g. "Thames Water") |
| `entity_id` | uuid FK → entity, nullable | resolved entity; null = unresolved |
| `claim_summary` | text | one-paragraph normalized statement of the claim |
| `raw_payload` | jsonb | the source's raw record, verbatim |
| `pipeline_version` | text | ingest pipeline version that wrote this row |
| `created_at` | timestamptz | == `observed_at` in practice; kept for audit |

Relationships: one observation → many `evidence_artifact`; one observation →
many `incident_membership` (an observation can bear on multiple incidents, e.g.
a correction); one observation → many `correction_event` (as target).

### evidence_artifact

Proof captured at ingest (ADR 0003). **Immutable.**

| field | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `observation_id` | uuid FK → observation | |
| `kind` | enum | `screenshot` \| `raw_html` \| `warc` \| `pdf` \| `metadata` \| `other` |
| `sha256` | char(64) | content address; storage key |
| `byte_size` | bigint | |
| `captured_at` | timestamptz | |
| `storage_uri` | text | content-addressed location |
| `redaction_note` | text nullable | what was redacted/excluded and why; null if nothing |
| `created_at` | timestamptz | |

### listing_state

Per-source-item polling memory: what makes re-polling idempotent and
removals detectable (ADR 0007). **Mutable** — updated on every poll; the
history of what was observed lives in `observation`, not here.

| field | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `source_id` | uuid FK → source | |
| `item_key` | text | matches `observation.source_item_key`; unique per source |
| `first_seen_at` | timestamptz | first poll on which the item was present |
| `last_seen_at` | timestamptz | most recent poll on which the item was present |
| `first_missing_at` | timestamptz nullable | first poll on which a previously seen item was absent |
| `consecutive_misses` | integer | reset to 0 whenever the item is seen |
| `status` | enum | `listed` \| `missing` \| `removed_confirmed` |
| `latest_observation_id` | uuid FK → observation, nullable | the listing observation this state tracks |

### entity

A canonicalized real-world subject (victim org, threat group, vendor, CVE
as entity where useful). **Mutable**, but every material change (merge, split,
rename, status change) is a `correction_event` (ADRs 0004, 0005).

| field | type | notes |
|---|---|---|
| `id` | uuid PK | stable |
| `canonical_name` | text | |
| `entity_kind` | enum | `company` \| `subsidiary` \| `municipality` \| `hospital` \| `school` \| `government` \| `nonprofit` \| `threat_group` \| `vendor` \| `cve` \| `other` |
| `jurisdiction` | text nullable | |
| `country_code` | char(2) nullable | ISO 3166-1 alpha-2, when evidenced |
| `lei` | char(20) nullable | GLEIF LEI |
| `wikidata_qid` | text nullable | |
| `cik` | char(10) nullable | SEC CIK |
| `naics_code` | text nullable | sector spine (ADR 0005) |
| `naics_confidence` | enum nullable | `direct` (SIC-mapped/filer) \| `heuristic` \| null |
| `status` | enum | `candidate` \| `resolved` \| `merged` \| `split` |
| `resolution_confidence` | enum | `low` \| `moderate` \| `high` |
| `resolution_model_version` | text | |
| `created_at` / `updated_at` | timestamptz | |

### alias

Name variants tied to an entity, with provenance. **Mutable** (grows
monotonically in practice); misnamings are aliases, never silent fixes
(ADR 0005).

| field | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `entity_id` | uuid FK → entity | |
| `alias_text` | text | e.g. "Thames Water (as listed by Clop)" |
| `alias_kind` | enum | `legal_name` \| `dba` \| `domain` \| `misnaming` \| `abbreviation` \| `other` |
| `source_observation_id` | uuid FK → observation, nullable | where this variant was seen |
| `first_seen` / `last_seen` | timestamptz | |

### review_task

The human-review queue (ADR 0005): ambiguous entity matches, unresolvable
subjects, contested corrections. The queue itself is auditable — tasks are
resolved with a recorded outcome, never silently dropped.

| field | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `target_kind` | enum | `observation` \| `entity` \| `incident` |
| `target_id` | uuid | |
| `reason` | text | why this needs a human (e.g. "fuzzy match below threshold", "no LEI/Wikidata/SEC hit") |
| `status` | enum | `open` \| `resolved` \| `deferred` |
| `created_at` | timestamptz | |
| `resolved_at` | timestamptz nullable | |
| `resolution_note` | text nullable | what the reviewer decided and why |
| `resolved_by` | text nullable | reviewer id |

### incident

The resolved record: what we believe happened, and why. **Mutable**, with
rationale-carrying revisions (ADR 0001).

| field | type | notes |
|---|---|---|
| `id` | uuid PK | stable across re-resolution |
| `status` | enum | `candidate` \| `active` \| `contested` \| `retracted` |
| `title` | text | claim-framed, e.g. "Clop lists South Staffs Water (as 'Thames Water')" |
| `summary` | text | evidence-grounded narrative; claim-framing mandatory (ADR 0004) |
| `primary_entity_id` | uuid FK → entity, nullable | |
| `first_observed_at` | timestamptz | earliest linked observation |
| `last_updated_at` | timestamptz | |
| `resolution_rationale` | text | why these observations form one incident |
| `resolution_model_version` | text | |
| `created_at` / `updated_at` | timestamptz | |

### incident_membership

Typed links between observations and incidents. **Immutable rows**; a changed
judgment is a new row (the old link stands as history, annotated by any
`correction_event` targeting it — see `correction_event.target_kind`).

**Currency rule.** A membership row is *current* unless a `correction_event`
with `target_kind = incident_membership` and `event_type` in
(`correction`, `retraction`) targets it; withdrawn rows remain in the table
as history. Current-membership views filter them out. Adding a row with the
same (`incident_id`, `observation_id`) as a withdrawn row re-opens the link
with a fresh rationale (e.g. a relist after a removal — see ADR 0007).

| field | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `incident_id` | uuid FK → incident | |
| `observation_id` | uuid FK → observation | |
| `link_type` | enum | `supports` \| `duplicates` \| `refutes` \| `corrects` |
| `rationale` | text | why this link was drawn |
| `added_at` | timestamptz | |
| `added_by` | text | pipeline version or reviewer id |

### correction_event

First-class correction history (ADR 0004). **Append-only.**

| field | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `target_kind` | enum | `observation` \| `incident` \| `entity` \| `alias` \| `incident_membership` |
| `target_id` | uuid | |
| `event_type` | enum | `correction` \| `denial` \| `removal` \| `retraction` \| `dispute_opened` \| `dispute_resolved` |
| `asserted_by` | text | who asserted it: source name, victim org, "xevents-review", … |
| `source_id` | uuid FK → source, nullable | |
| `observed_at` | timestamptz | when xevents recorded the correction |
| `note` | text | what changed and why |
| `created_at` | timestamptz | |

### confidence_assessment

Versioned, explainable confidence (ADR 0006). **Immutable; superseded, never
edited.**

| field | type | notes |
|---|---|---|
| `id` | uuid PK | |
| `target_kind` | enum | `incident` \| `observation` |
| `target_id` | uuid | |
| `band` | enum | `unverified` \| `low` \| `moderate` \| `high` \| `disputed` |
| `model_version` | text | |
| `inputs_hash` | char(64) | hash of the observation/correction set assessed |
| `independence_classes` | text[] | classes that contributed (echoes collapsed); the set is defined by the row's `model_version` |
| `supporting_weight` | numeric | internal model input, non-negative; **never published** — the band is the published output |
| `refuting_weight` | numeric | internal model input, non-negative; **never published** |
| `rationale` | text | human-readable evidence → conclusion |
| `assessed_at` | timestamptz | |
| `superseded_by` | uuid FK → confidence_assessment, nullable | |

## Lifecycle: observation → incident

1. **Ingest.** A poller fetches a source, captures
   evidence (screenshot + raw HTML/metadata, ADR 0003), and writes one
   immutable `observation` row per claim, with `subject_raw` verbatim and
   `source_claimed_at` when the source provides it. **Ingest is idempotent:**
   each item is keyed by `source_item_key`; a re-poll that finds an already-
   recorded item updates `listing_state.last_seen_at` and creates nothing.
   The poller's version is registered in `model_version` and recorded on
   every observation it writes.
2. **Entity resolution.** The ADR 0005 pipeline attempts to resolve
   `subject_raw` → `entity_id`, recording each enrichment step as its own
   observation. Unresolvable subjects stay null with the raw string preserved.
   New variants become `alias` rows with provenance.
3. **Incident resolution.** Observations about the same real-world event are
   grouped into an `incident` via `incident_membership` rows with typed links
   and rationales. A ransomware listing, the victim's 8-K, and a state AG
   notice for the same org and timeframe become one incident with three
   supporting observations from three independence classes.
4. **Confidence assessment.** A versioned assessment is computed over the
   incident's observations and any correction events, counting independence
   classes once each, and stored immutably with its rationale.
5. **Publication.** The public surface renders incidents with claim-framing
   language, the confidence band, the evidence trail, and the correction
   history. Attribution strings from the source registry accompany
   CC BY 4.0-derived content.

## Lifecycle: correction propagation

1. A correction arrives (victim denial, source retraction, observed
   de-listing, dispute outcome) → new immutable `observation`
   (claim_type `correction_notice` or `removal`) + evidence capture.
2. A `correction_event` is appended targeting the affected observation,
   incident, entity, or alias.
3. The incident is re-resolved: new `incident_membership` rows as needed
   (e.g. a `refutes` link), status transition with rationale
   (`active` → `contested` → `retracted`), updated summary.
4. A new `confidence_assessment` supersedes the old one (`superseded_by`
   link); the old assessment remains queryable.
5. Entity-level corrections (merge/split/rename) update `entity`/`alias` and
   trigger re-resolution of every incident touching that entity.
6. Nothing is deleted. A retracted incident remains visible with its full
   history — the ledger is the product.

## Coverage boundary (published statement)

The coverage boundary (glossary) is not a table — it is a **versioned public
statement** rendered on the operational surface, fed by
`source.known_limitations`. Required contents, all of them:

1. Entity classes resolved well vs systematically missed (public companies /
   LEI holders / notable firms vs SMEs, municipalities, schools, hospitals
   without identifiers).
2. Source coverage windows (which sources, since when, at what cadence).
3. Known blind spots: non-Tor extortion channels (Telegram/clearweb/forums),
   seizure/takedown silence, aggregator metadata gaps (e.g. RansomLook has no
   country/sector fields).
4. What "unresolved" means: an honest null `entity_id` with the raw string
   preserved — never a confident mis-resolution.

The statement is re-issued whenever a source is added/removed or a
limitation is discovered. MVP acceptance requires it published
(docs/mvp-scope.md item 7).

## Vulnerability linkage (post-MVP)

The schema reserves the pattern; the ingest does not exist yet
(docs/mvp-scope.md, non-goal 6):

1. A CVE is an `entity` with `entity_kind=cve`.
2. A KEV catalog row becomes an `observation` with
   `claim_type=vuln_exploit_claim`, `subject_raw` = the CVE ID, and the KEV
   entry's ransomware-use flag in `raw_payload`.
3. The CVE→incident link is an `incident_membership` row, added when an
   incident's observations reference the CVE (e.g. an 8-K or disclosure names
   it, or KEV ransomware-use overlaps a victim's timeframe with supporting
   evidence). The rationale must state the basis for the link — co-occurrence
   alone is not linkage.

## JSON export contract

The MVP's operational surface (mvp-scope.md item 7) offers JSON export of
incident records. The export is a fixed contract — consumers pin against it,
so fields are added, never renamed or removed, without a contract version
bump. **Excluded by construction:** internal confidence weights
(`supporting_weight`, `refuting_weight`), reviewer identities
(`resolved_by` → published as "xevents-review" only), and any redacted
bytes. The export root carries `exported_at`, `contract_version`, and the
published coverage-boundary statement (see above), so a downloaded file is
self-describing.

Per incident:

- `id`, `status`, `title`, `summary`
- `primary_entity` — resolved entity (id, name, kind) or null with the raw
  subject string preserved as `subject_raw`
- `first_observed_at`, `last_updated_at`
- `confidence` — `band`, `rationale`, `model_version`, `inputs_hash`,
  `independence_classes` (contributing classes only; echoes collapsed)
- `observations[]` — id, source name, `claim_type`, `subject_raw`,
  `observed_at`, `source_claimed_at`, `confidence` (observation-level band +
  rationale), evidence artifact hashes and kinds (bytes only by separate
  retrieval; redaction notes included)
- `corrections[]` — the append-only ledger rows touching this incident or
  its observations, in event order
- `attribution[]` — per-source attribution strings (source registry),
  satisfying CC BY 4.0 for RansomLook-derived content

## Interoperability notes

- VCDB/VERIS schema is the reference for incident-level fields; align naming
  where it costs nothing (landscape §3.1).
- STIX 2.1 export compatibility is desirable (OpenCTI precedent; ransomfeed.it
  already ships an OpenCTI connector) — observations map naturally to STIX
  sightings/reports with `created_by` provenance. Not a v1 requirement.
