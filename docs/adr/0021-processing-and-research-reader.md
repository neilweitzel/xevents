# ADR 0021: Private processing and the research data reader

- Status: proposed (pending user redline)
- Date: 2026-09-23
- Scope: implementation increment for MVP items 3, 4, 5 and 7
- Authority: operator requested connecting private processing, safe aggregates
  and the research application. Merge and deployment remain separate approvals.

## Implementation

Verify the immutable intake chain before deriving anything. Derive private
incident candidates by exact normalized actor and unresolved subject; do not
perform fuzzy identity resolution. Record every membership and rationale.
Repeated listings remain one independence class and cannot increase confidence.
Source-claimed dates do not replace retrieval dates. No removal is inferred.

Produce conservative sector suggestions from explicit words in descriptions,
not organization names. Conflicting or unsupported suggestions remain
unclassified. Suggestions are not accepted classifications. All incident
candidates enter a private review queue; no processing flag grants release.

Persist content-addressed private processing snapshots on the existing data
branch. Run processing after every collection attempt, including a cadence
skip, without another network request. Reuse a snapshot for unchanged input
and processor version. New processing snapshots are additions, not rewrites.
The data writer's scope expands only to `processing/snapshots/<sha256>.json`.

Derive a counts-only, private research projection with a closed schema and
nulls for every cell below five, including zero. Use retrieval-week windows
(Monday UTC), provisional incident candidates rather than listing totals,
and a fixed sector vocabulary. No raw names, URLs, identifiers, exact evidence
hashes or free-text source fields appear in that projection. Scan its exact
serialized representation with G5 in an offline integration test using the
entire source window's subjects and actor names. This is a draft, not a
release candidate: suggested classifications, G2/G3/G4, corrections, manifest
binding, coverage accounting and other launch controls remain unresolved.

## Reader contract

The application defaults to a same-origin request for
`data/aggregates/view1.jsonl`. No credentials or private endpoint is used.
A missing file means awaiting approved data. A malformed file, redirect,
oversized response or network failure means unavailable, never demo fallback.
Demo data requires the explicit `?demo=1` route.

The bounded RC display contract is `xevents-view1-display/v1`, not the complete
production export contract described in `data-model.md`. One closed header:
`file_purpose: sector_aggregate`, `schema_version`, `release_state`,
`generated_at`, `coverage: recent_only`, `time_basis: retrieved_at`,
`privacy_floor: 5`. Subsequent closed rows contain `sector`, `week_start` and
`claim_count` only. Dates must be real Monday UTC dates; counts are integers
from 5 to 1,000,000, or null. Maximum 104 consecutive weeks and the fixed
21-sector vocabulary, including unclassified. The rectangular matrix must
include every vocabulary sector for every window, so absent cells cannot
silently become zeros or reveal sector presence through omitted rows.

The private producer always marks `release_state: blocked`; the reader only
accepts `released`. That field is a format check, **not proof of authorization**.
No code in this increment can generate a released file from private records,
sign a release, write to the public repository or deploy real data. The
existing signed boundary must authorize the exact final bytes before any
future public write. The reader is not a substitute for that boundary.

Production mode omits demo activity bands. Exports preserve the selected
approved aggregate cells and attribution without claiming breach verification.
Data older than two weeks is visibly stale. Waiting, empty, withheld, invalid
and stale states are tested alongside the explicit synthetic demonstration.

## Unchanged controls and next release dependency

The three-location public write set, source count, k=5 floor, review doctrine,
lawful-basis requirement and signing/proof requirements are unchanged.
Accepted ADRs are not edited. The conflicting historical wording of burn-in
(`first ... published observations` versus `surface stays dark`) needs an
explicit launch ruling, not an invented processor interpretation.

This increment connects the private derivation and public reader interfaces.
It does **not** claim the intervening reviewed, signed publication path exists.
