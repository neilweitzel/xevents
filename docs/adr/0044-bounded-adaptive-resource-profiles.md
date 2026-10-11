# ADR 0044: Bounded automatic resource-capacity profiles

Status: accepted

Date: 2026-10-10

Approval: operator requested implementation of bounded capacity growth on
2026-10-10. Only tested profiles may activate.

## Scope

This changes application resource envelopes, not publication policy or physical
provider storage. Source reads remain at 200 records, the network response
bound remains 1 MiB, and the capture event bound remains 4 MiB.
Source-window expansion and the independent-source pilot remain separate work.

## Decision

The reviewed code contains exactly three resource profiles:

| Profile | Retained history | Derived-file envelope | Live observations | G5 entries |
|---|---:|---:|---:|---:|
| baseline | 50 MiB | 8 MiB | 10,000 | 10,000 |
| expanded | 96 MiB | 16 MiB | 15,000 | 32,000 |
| ceiling | 128 MiB | 24 MiB | 20,000 | 50,000 |

All four dimensions must fit; raising history alone is insufficient. G5 entries
include subjects, actors and static names. This is a bounded allocation limit,
not a change to matching, normalization, ordering, refusal rules or the match
count ceiling. The entire larger name set is scanned, never sampled or truncated.

### Selection and provenance

After ordinary eligible maintenance, measure verified history and current
processing requirements. Derivative sizing also conservatively accounts for
frozen statistics, correction-record overhead and the public matrix envelope.
Cold archived receipts are not treated as growing work.

Reserve a possible 4 MiB next transaction, 200 new observations, 400 new G5
entries and 4 KiB per new observation for derivative growth. These are bounded
next-acquisition allowances, not an exact arrival forecast.

- At 70 percent of current usage, report a private warning.
- At 85 percent of projected usage, select the smallest larger reviewed
  profile whose projected usage is below 70 percent in every dimension.
- Permit at most one promotion per seven days. A promotion may skip a tier
  when the intermediate profile cannot provide that margin.
- If projected usage reaches 95 percent and no permitted profile safely fits,
  refuse further acquisition visibly. Preserve valid maintenance and the last
  verified public release. There is no recursive or unlimited growth.
- Never automatically demote a profile.

Promotions are immutable, content-addressed private decisions containing the
input commit, verified source-head hash, predecessor hash, measurements,
reservation estimates, selected literal bounds, UTC time and reason code.
The journal is sequence-checked, cooldown-checked and limited to two promotions.
It is not executable configuration. Unknown bounds, corrupted records,
regressing clocks or broken links fail closed rather than falling back.

### Maintenance and research preservation

Try eligible verified maintenance first. If its planning refuses specifically
because an observation or checkpoint resource budget is too small, allow one
tested promotion and maintenance retry. Projection, evidence, integrity and
privacy failures never authorize that retry.

Retain the twelve-week floor, original source bytes, historical capture
registries, frozen research counts, correction state and replay checks of
ADR 0043. No younger evidence is discarded to fit a budget.

Scheduled processing still validates and serializes its deterministic snapshot
for sizing, but does not persist that redundant full derivative every capture.
Raw history, checkpoint lineage, code/profile seals and the release receipt
remain the replay authority. Existing snapshots remain readable and eligible
for ordinary verified cleanup.

### Safety and transport

Capacity measurement is not a G5 or release pass. It must not evaluate away a
pending frozen classification conflict; real preparation still requires the
unchanged eligibility/correction checks and full exact-output G5.

Public suppression, complementary monthly suppression, display horizons,
file bounds, proof freshness, proof expiry, admission and deployment authority
remain unchanged. Resource profiles cannot override those safeguards.

The 24 MiB raw private commit envelope remains fixed. Reserve space before
source I/O, and check the exact pending additions plus serialized receipt before
archival. Base64 encoding adds roughly a third to the request payload; this
application budget is not a guarantee of an undocumented provider payload limit.
Do not automatically increase transport or network budgets.

Capacity blocks produce a fixed private refusal receipt and a failed job, not a
misleading healthy skip. Promotion and capacity status appear in private
telemetry. No new issue permissions, external monitor or scheduler are added.

### Runtime budgets

Benchmark every profile across the same sixteen-week horizon, including a
unique actor per observation to stress both sides of the name set. Measure full
verification, processing, preparation, G5, cleanup, memory and payload sizes.
Preserve the full projection through cleanup in the stress fixtures.

Derive workflow limits from the largest tested envelope with the existing
runner calibration and at least a twofold margin. Keep the admission/Pages
waits and 300-second signing freshness and 900-second proof expiry unchanged.
The budget table and workflow must agree in CI.

The profile fixtures use 4,000, 12,000 and 18,800 invented observations across
the same sixteen-week horizon. All pass full G5 and preserve the complete
projection through eligible cleanup. At the ceiling fixture, the full scan
of 37,608 entries takes approximately 496 seconds and peak resident memory is
453 MiB. A separate near-history-ceiling fixture verifies 124,320,913 bytes
in approximately 39 seconds with the source response bound unchanged.
These are synthetic local measurements, not production promotion claims.

Collection receives 28 minutes and release receives 57 minutes, derived from
the measured stage table and setup allowance; audit remains seven minutes.
These are maximum job limits, not expected daily duration. No shorter proof
window is extended to cover a slow scan: scanning still precedes signing.

## Activation requirements

- Exact threshold and cooldown boundaries, coupled constraints, tier skips,
  ceiling refusal and no arbitrary cap overrides.
- Canonical journal hashes, predecessor/sequence checks, clock monotonicity,
  invalid-state refusal, and effective limits even during cached verification.
- No source request or publication outputs after a capacity block.
- Resource-only maintenance retry; no promotion after an integrity refusal.
- Snapshot validation without redundant persistence preserves raw evidence.
- The larger scan finds a planted name beyond the former ten-thousand-entry
  boundary and still refuses the release.
- Pending frozen classification still refuses real preparation while sizing
  remains separate.
- All existing private suites, G5 equivalence/coverage, public authority,
  implementation seal and measured profile benchmarks pass.

Observe the normal baseline in production; do not fabricate pressure to claim
a live promotion. Synthetic promotion tests remain explicitly labeled.

## Limits

These profiles buy bounded headroom, not indefinite retention or completeness.
Repository git history, correction ledgers, long-term checkpoint partitions,
source-window pressure and provider outages require separate accounting.
At the tested ceiling the correct outcome is an honest stop and review, not
shorter retention, skipped checks or unlimited limits.

A stress test also exposed a pre-existing pathological runtime in metadata
indicator matching on a long unbroken string within the response envelope.
The tracked follow-up must preserve every indicator predicate rather than
truncate text or weaken screening. The ordinary formatted-payload benchmarks
do not certify adversarial worst-case screening runtime.
