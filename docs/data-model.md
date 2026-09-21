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
- **System of record is git, not a database server** (ADR 0009,
  superseding ADR 0008). Tables below are *logical*; their physical form is
  append-only JSONL under `data/` (see "Physical mapping (static-first)").

## Physical mapping (static-first, two-repo)

The logical schema above is implemented without a database server. Mapping:

| logical type | physical form |
|---|---|
| `timestamptz` | ISO-8601 UTC string, e.g. `2026-09-20T17:44:25.273479+00:00` |
| `jsonb` | nested JSON value |
| `text[]` | JSON array of strings |
| `enum` | JSON string (values as documented) |
| `uuid` | lowercase canonical string |
| `numeric` (weights) | JSON number; never published (see export contract) |

**Two repositories** (open-decisions.md #11). The trust boundary is the
aggregation boundary:

| repo | visibility | contents | write pattern |
|---|---|---|---|
| `xevents-internal` (private) | owner-only | `data/observations.jsonl`, `data/correction_events.jsonl`, `data/confidence_assessments.jsonl`, `data/poll_runs.jsonl`, `data/listing_state.json`, entity/alias/incident registries, `review_tasks.jsonl`, `evidence_artifacts.jsonl`, `sources.jsonl`, `model_versions.jsonl`, `evidence/<sha256>` raw bytes | append-only (registries as documented); raw bytes write-once |
| `xevents` (public) | public | `data/aggregates/*.jsonl` (sector × time-window aggregates — **no organization or actor names, ever**), `evidence-manifest.jsonl`, `site/` (generated) | aggregates recomputed per run and committed; manifest append-only |

The public build never reads the private repo. Aggregation runs privately;
only the aggregate output crosses to public, after the name-scan gate
(ADR 0010 §1, G5) asserts zero organization/actor names in the outgoing
batch. No internal identifiers appear in public outputs — the only
cross-boundary references are content hashes from the evidence manifest.

### Evidence manifest (public)

`evidence-manifest.jsonl` in the public repo is the audit commitment for
every internal observation: one row per observation, append-only.

| field | notes |
|---|---|
| `manifest_id` | uuid, public identifier for this manifest row |
| `observed_at` | when xevents recorded the observation |
| `source_name` | e.g. `ransomlook_api` |
| `payload_sha256` | SHA-256 of the raw source payload bytes — the verifiable commitment: anyone holding their own copy of the source record can hash it and compare |
| `source_ref` | name-free source reference (numeric post id, API path) **only if it carries no organization or actor name**; otherwise omitted, with the omission noted |
| `retrieved_at` | when the payload was fetched |

The manifest proves *that we retrieved what we claim we retrieved* without
republishing names. Drill-down to victim-level detail happens via links
back to the sources, not via the manifest.

File layout (private repo, committed to `main` by the pipeline):

| path | contents | write pattern |
|---|---|---|
| `data/observations.jsonl` | one JSON object per line, immutable | append-only |
| `data/correction_events.jsonl` | append-only ledger | append-only |
| `data/confidence_assessments.jsonl` | superseded, never edited | append-only |
| `data/poll_runs.jsonl` | run manifests (replaces the `poll_run` table) | append-only |
| `data/listing_state.json` | `source_item_key` → last-seen map (replaces the `listing_state` table). **Pivot note:** governs *internal* observations only — when an internal listing observation transitions to `removed_confirmed` (open-decisions.md #11) | rewritten atomically per run |
| `data/entities.jsonl`, `data/aliases.jsonl`, `data/incidents.jsonl`, `data/incident_membership.jsonl`, `data/review_tasks.jsonl`, `data/evidence_artifacts.jsonl`, `data/sources.jsonl`, `data/model_versions.jsonl` | registries | append-only (registries), rewritten only where the logical table is mutable (`source`) |
| `evidence/<sha256>` | raw artifact bytes, content-addressed (private — may contain names) | write-once |

File layout (public repo):

| path | contents | write pattern |
|---|---|---|
| `data/aggregates/*.jsonl` | sector × time-window aggregates | recomputed per run, committed |
| `evidence-manifest.jsonl` | audit commitments (hashes + provenance) | append-only |
| `site/` | generated HTML + JSON snapshots for Pages | regenerated per run |

Immutability is enforced by convention + CI (a test asserts that a pipeline
run never rewrites a line in an append-only file), and is publicly auditable
via git history for the public repo. A SQLite file may be built at pipeline time as a
*derived* convenience artifact; it is never authoritative.

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
| `sector` | text | NAICS 2-digit spine (versioned taxonomy); `unclassified` when the evidence does not support a classification — never a guess. The sector is what the **public** surface publishes (open-decisions.md #8) |
| `attack_vector` | enum | **internal-only after ADR 0011.** Retained for private-corpus continuity and internal analytics. The public surface now uses `attack_class` (view 1) and the exploitation-detail fields (view 2). Versioned: `phishing_social_engineering` \| `public_facing_app_exploit` \| `credential_stuffing_bruteforce` \| `usb_removable_media` \| `supply_chain` \| `insider` \| `ransomware_deployment` \| `cryptomining_payload` \| `other` \| `unknown` |
| `malware_class` | enum | **internal-only after ADR 0011.** Retained for internal analytics; never published under the naming policy. Values: `ransomware` \| `cryptominer` \| `wiper` \| `stealer_exfiltrator` \| `rat_backdoor` \| `rootkit_bootkit` \| `unknown` |
| `attack_class` | enum | **View 1 vocabulary (ADR 0011).** Coarse public-surface classification. Controlled by `docs/attack-class-vocabulary.md`: `ransomware` \| `data_extortion` \| `phishing_compromise` \| `social_engineering` \| `credential_abuse` \| `supply_chain` \| `exploitation_public_facing` \| `insider` \| `unspecified`. One value per observation. |
| `cve_ids` | jsonb | **View 2 vocabulary (ADR 0011).** Array of CVE identifiers named in the source or a linked advisory. Format `CVE-YYYY-NNNNN`. Empty array when none. |
| `cisa_kev_present` | boolean | **View 2.** True if any `cve_ids` entry is in the CISA KEV catalog at extraction time. Snapshot version recorded in `pipeline_version`. |
| `vendor_advisories` | jsonb | **View 2.** Array of vendor advisory URLs. Each URL's destination page is scanned against the denylist at publish time (naming-policy.md, ADR 0013). |
| `mitigation_refs` | jsonb | **View 2.** Array of mitigation reference URLs (patch notes, hardening guides, sector CERT bulletins). Same publish-time destination scan. |
| `appliance_class` | enum nullable | **View 2.** Controlled by `docs/exploitation-vocabulary.md`: `ssl_vpn` \| `edge_firewall` \| `managed_file_transfer` \| `remote_access` \| `email_gateway` \| `identity_provider` \| `application_server` \| `network_appliance` \| `unspecified`. Null when no appliance is implicated. |
| `misconfiguration_class` | jsonb | **View 2.** Array (zero or more) from controlled enum: `exposed_service` \| `weak_authentication` \| `unpatched_public_facing` \| `misconfigured_permissions` \| `unauthenticated_api` \| `legacy_protocol`. |
| `victim_acknowledged` | enum | `acknowledged` \| `unacknowledged` — sourced strictly to the victim's own public disclosure (SEC 8-K Item 1.05, company press statement, state AG breach notice, HHS OCR entry). Orthogonal to confidence (open-decisions.md #9). **Binary:** every incident is `unacknowledged` until a cited victim disclosure confirms it, at which point it becomes `acknowledged`. No intermediate states, no inference from silence — the scale of unacknowledged claims is itself a research finding. Default: `unacknowledged`. |
| `data_classes_claimed` | jsonb | array of `{class, status}`; class from the controlled taxonomy (email, name, postal_address, phone, dob, national_id, financial_account, payment_card, health_info, credentials, government_id, biometric, other); status `claimed` (as the source asserts) or `victim_confirmed` (only when the victim's own public disclosure confirms it). Never published as breach contents (open-decisions.md #10) |
| `raw_payload` | jsonb | the source's raw record, verbatim |
| `pipeline_version` | text | ingest pipeline version that wrote this row |
| `load_kind` | enum | `live_ingest` (the default, forward-going ingest) \| `backfill_load` (RansomLook first-run historical backfill, ADR 0010 §2). Backfilled observations are held internal-only and do not contribute to the 500-observation burn-in count (open-decisions.md #17). |
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
| `event_type` | enum | `correction` \| `denial` \| `removal` \| `retraction` \| `dispute_opened` \| `dispute_resolved` \| `administrative_note` (retention actions, severity-1 responses, and other non-claim lifecycle events; carries action/authority/reason in `note`) |
| `asserted_by` | text | who asserted it: source name, victim org, "xevents-review", … |
| `source_id` | uuid FK → source, nullable | |
| `observed_at` | timestamptz | when xevents recorded the correction |
| `source_asserted_at` | timestamptz nullable | when the *source* claims the corrected event occurred, if it says; null when it doesn't — the two-clock doctrine applies to corrections too |
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
statement** rendered on the public surface, fed by
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

The MVP's public surface (mvp-scope.md item 7) offers JSON export of the
**sector aggregates**. The export is a fixed contract — consumers pin
against it, so fields are added, never renamed or removed, without a
contract version bump. **Excluded by construction:** organization and actor
names (docs/naming-policy.md), internal confidence weights
(`supporting_weight`, `refuting_weight`), reviewer identities
(`resolved_by` → published as "xevents-review" only), internal identifiers,
and any redacted bytes.

The export root carries the framing, so a downloaded file is
self-describing even separated from the site:

- `dataset`: `xevents` sector-aggregated incident-claim research data
- `framing`: "Public claims about cyber incidents, aggregated by sector.
  Confidence bands describe corroboration of claims, not verification of
  breaches. No organization or threat-actor names are published."
- `methodology_url`, `exported_at`, `contract_version`, `license`
  (CC BY 4.0 attribution chain for derived content)
- the published coverage-boundary statement

Two aggregate exports (ADR 0011). They do not cross-reference.

**View 1 aggregate (sector × time window):**

- `sector`, `window_start`, `window_end`
- `claim_count`, `confidence_breakdown` (counts per band),
  `victim_acknowledged_breakdown` (acknowledged / unacknowledged counts)
- `attack_class_breakdown` (counts per view 1 enum value)
- `data_classes_claimed` (claimed vs victim_confirmed counts)
- `corrections[]` — correction-ledger rows touching the underlying
  observations, in event order (no names)
- `manifest_refs[]` — evidence-manifest ids backing the aggregate
- `attribution[]` — per-source attribution strings (source registry),
  satisfying CC BY 4.0 for RansomLook-derived content

**View 2 aggregate (technique × time window):**

- `technique_key` — either a CVE identifier, an `appliance_class` value,
  or a `misconfiguration_class` value
- `technique_kind` — `cve` \| `appliance` \| `misconfiguration`
- `window_start`, `window_end`
- `observation_count`
- `cisa_kev` — boolean if `technique_kind == cve`
- `vendor_advisories[]`, `mitigation_refs[]` — deduped URLs referenced by
  the underlying observations; each verified against the destination-scan
  gate at publish time
- `sector_distribution` — present ONLY when the entry's total count is
  large enough that every included sector cell independently clears the
  small-cell floor (open-decisions.md #13). Otherwise omitted, not
  suppressed-with-note. See ADR 0011 non-cross-index rule.
- `manifest_refs[]`, `attribution[]` — as above

## Interoperability notes

- VCDB/VERIS schema is the reference for incident-level fields; align naming
  where it costs nothing (landscape §3.1).
- STIX 2.1 export compatibility is desirable (OpenCTI precedent; ransomfeed.it
  already ships an OpenCTI connector) — observations map naturally to STIX
  sightings/reports with `created_by` provenance. Not a v1 requirement.
