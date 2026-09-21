# xevents — Evidence storage strategy

**Status:** draft, 2026-09-21. Rewritten for the two-repo architecture
(open-decisions.md #11); supersedes the 2026-09-20 single-repo version.
The logical requirements are ADR 0003's; this document is the physical plan.

## The split

Evidence lives in **two** places, divided by the naming policy
(docs/naming-policy.md):

| what | where | why |
|---|---|---|
| Raw artifacts (screenshots, raw API JSON, fetch metadata) — **may contain organization or actor names** | `xevents-internal` (private): `evidence/<sha256>`, content-addressed, write-once | Fidelity for audit and re-derivation; names as claimed are evidence |
| Evidence manifest (`evidence-manifest.jsonl`) — hashes + provenance, **name-free** | `xevents` (public) | Public audit commitment without republication (data-model.md) |

There is no separate public evidence repo. The manifest is small text; it
lives in the public repo beside the aggregates it backs.

## Capture (private pipeline)

Per observation, captured at ingest (ADR 0003), before anything is stored:

- the raw API response body for the item (byte-faithful, content-hashed);
- the source screenshot fetched from the source (CC BY 4.0 — archival is
  permitted for RansomLook);
- fetch metadata (URL, timestamp, HTTP status, poller version).

The automated PII screen (ADR 0010, G2) runs at capture: incidental
personal data in free-text fields is flagged for the review queue. Raw
bytes are stored as-retrieved in the private repo — redaction-before-
storage applied to the *public* derivatives, not to the audit record.
The redaction note travels with the observation row.

**Backfill rule:** backfill captures metadata + raw JSON for all items;
screenshots are fetched for new items going forward only (a deliberate,
rate-limited historical fetch may be enabled explicitly — default off).

## Publication (across the boundary)

What crosses to the public repo per observation: the manifest row
(`manifest_id`, `observed_at`, `source_name`, `payload_sha256`,
name-free `source_ref`, `retrieved_at`). The name-scan gate (ADR 0010, G5)
covers manifest rows the same as aggregates — a name-bearing `source_ref`
is withheld, with the omission noted.

**Practitioner retrieval workflow** (the answer to "how do I check one
artifact"): (1) find the aggregate on the dashboard; (2) follow its
`manifest_refs[]` to the manifest rows; (3) take the `payload_sha256` and
`source_name`/`retrieved_at`; (4) fetch the source record yourself (or
from a web archive) and hash the payload bytes; (5) compare. A match
proves we retrieved what we claim we retrieved. The manifest is the
proof; the source is the drill-down.

## Volume plan

Steady-state ingest is small: ~14 RansomLook items/day, one screenshot
each (~100–500 KB) → single-digit MB/day, ~1–2 GB/year. The private repo
absorbs this without a split trigger — GitHub's soft ~5 GB guidance is
years away, and the private repo has no Pages artifact to bloat. The
scheduled pipeline logs `evidence/` size in every run manifest; if growth
ever threatens the guidance, that is a new ADR, not a silent migration.

## Retention mapping

The retention policy (docs/retention-policy.md) tiers map to storage as
follows:

| tier | physical form |
|---|---|
| hot/warm/cold | `evidence/` in `xevents-internal` (private) |
| ledger | `data/*.jsonl` in `xevents-internal` (private), forever; the public manifest rows in `xevents`, forever |

The cold-review gate (no auto-delete) is unchanged: deletion removes bytes
only, hashes and ledger rows remain, and the deletion is recorded as an
`administrative_note` correction event.

## What this does not do

- No Git LFS (breaks the "any clone is a complete checkable state"
  property and complicates the pipeline).
- No external object store in the MVP (no credentials to manage, no bill).
- No public raw evidence. Ever. The naming policy is the reason; this
  document is the mechanism.
