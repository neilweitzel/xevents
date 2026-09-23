# ADR 0020: Bounded private intake and replay

- Status: proposed (pending user redline)
- Date: 2026-09-23
- Scope: first implementation slice of MVP items 1 and 2; not M3 completion
- Authority: operator approved implementing one bounded private intake followed
  by an identical-response replay on 2026-09-23.

## RC2 amendment: typed intake and unattended collection

Proposed implementation requested on 2026-09-23. The following supersedes
the manual-only and missing-screenshot rules below for the version-2 adapter:

- Accept native booleans and the explicitly supported legacy boolean strings.
  Link, magnet and screenshot fields may be null; other types stay strict.
  Keep the untouched source bytes and field values.
- A null or empty screenshot means `not_provided`, not a failed request.
  Admit the API metadata into private pending-review storage with that status.
  Attempt to fetch, bound, hash and archive a supplied screenshot.
  Failed retrieval records `unavailable` without discarding usable API metadata.
  Screenshot availability is supplementary, not a private-intake admission gate.
  Never manufacture source evidence or claim that failed image evidence exists.
  This changes private admission only, not G2 or publication eligibility.
- Verify old transactions with their original adapter. Explicit offline
  reprocessing may append newly understood observations with original retrieval
  time, never rewrite history, advance sightings or claim burn-in.
- Use a two-hour GitHub Actions trigger and six-hour effective polling guard.
  Persist append-only results on a dedicated private data branch, with serialized
  runs, signed commits and a data-only write-set check. No personal computer,
  boundary App key or public write token is required.
- The first automated window remains at most ten recent records. A full window
  reports possible truncation; this is not complete source coverage, backfill,
  de-listing detection or automatic research publication.
- Merge and schedule activation require explicit approval of this change.
  Private branch protection remains a hosting-plan limitation; checked,
  expected-head signed writes are compensating controls, not equivalent
  protection. Failure is visible as a failed private workflow run.

The remaining end-to-end work is classification, release-gate execution,
signed aggregate transport and automatic Pages updates from approved releases.
Neither an automated collector nor the synthetic Pages demonstration represents
that completed production path.

## Purpose

Implement the already-approved RansomLook source without activating a scheduler
or crossing the publication boundary. This serves the
[MVP's intake and evidence criteria](../mvp-scope.md) and M3 AC3.2–AC3.4 and
AC3.11 in the [implementation plan](../implementation-plan.md).
It does not change source licensing, the three-location boundary write set,
burn-in, correction doctrine, source count or launch gates.

Implementation is authorized; merge and live execution remain separate
approvals. This proposal records concrete storage and replay semantics before
their implementation. It does not turn a code review into a production approval.

## Bounded operation

- One manual recent-post request, default three records, maximum ten.
  No full-history load, search, de-listing inference or scheduled requests.
- Credential-free HTTPS to the approved aggregator only. No redirects, proxy
  inheritance, criminal-infrastructure access or following record links,
  magnet URIs, advisories or arbitrary user-supplied destinations.
- Capture exact API response bytes and available source-provided screenshots,
  with retrieval time, HTTP metadata and SHA-256 verification. Never represent
  canonicalized item JSON as original response bytes.
- Store source time independently of capture and processing time. Use
  `misp_uuid` as the source key in this slice; missing/invalid keys are rejected,
  not silently replaced with a guessed identity.
- Preserve immutable source claims, classify as `unclassified`, and make no
  incident-resolution, confidence, acknowledgment or aggregation inference.
- An exact duplicate creates no observation. Changed content under a known
  source key is held for correction handling; it never overwrites history.

## Atomic private storage

The initial writer uses immutable transaction envelopes inside the existing
private observation store, with separately content-addressed evidence. Each
envelope binds its poll result, newly admitted observations, evidence metadata,
listing-state updates and preceding transaction digest. A single atomic,
write-once installation is the commit point; readers ignore incomplete
temporary files. Failed attempts have private, sanitized receipts.

Logical tables remain those in the [data model](../data-model.md). This
physical representation supplements the older draft's single-file table
mapping; it does not introduce a database or change observation immutability.
The private implementation documents its precise file paths. Transaction
envelopes are not public manifests and are never boundary-writable.

Readers validate the complete chain and evidence bytes, then derive current
listing state. Concurrent writers are serialized. A crash before the commit
point may leave unreferenced evidence, but cannot admit half a transaction.
No automatic evidence deletion or history rewriting is introduced.

## Replay is not a new sighting

Replay processes captured bytes through the same parser and deduplication path,
without network access. It records a new processing attempt but retains the
original retrieval clock. It cannot advance `last_seen_at`, count as another
forward observation, contribute to burn-in, or authorize publication.
For a previously captured transaction, unchanged content must create zero new
observations and preserve every prior observation byte-for-byte.

## Review and privacy limits

Metadata screening records potential personal-data/secret indicators; it is
not a claim of complete G2 implementation. Screenshot inspection/redaction and
human capture review remain required. Every record from this slice is pending
review and explicitly ineligible for publication and burn-in credit.
Missing screenshots or failed screenshot retrieval must be recorded and keep
the associated item out of admission; a source with no screenshot is handled
as missing evidence, not silently waived.

No private provenance, source record, evidence hash, source identifier or
review result is transported publicly by this implementation. In particular,
the public evidence manifest remains untouched.

## Activation prerequisites

Before real execution, review the implementation and effective private
repository controls, re-verify source terms/attribution, confirm private
storage and evidence-review handling, and approve the bounded run.
Unavailable private branch protection is not bypassed by this ADR. There is
no production-signing key, publisher, App transport or live-data UI switch.

## Required tests

Exact-byte evidence; hash corruption; source-time handling; strict parsing;
duplicate keys; source schema drift; changed source content; duplicate UUIDs
within a response; atomic failure/recovery; concurrency; unsafe filesystem
objects; invalid timestamps; replay without network or sighting advancement;
sanitized failures; bounded transport; screenshot failure; complete per-item
accounting; and proof that publication paths remain untouched.
