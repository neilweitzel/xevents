# ADR 0043: Weekly private retention checkpoints with preserved research counts

Status: accepted

Date: 2026-10-10

Approval: operator requested implementation of the weekly checkpoint migration
and preservation tests on 2026-10-10, with detailed records kept at least twelve
weeks. Implementation may activate only after the tests below pass.

Supersedes ADR 0029's whole-month timing for stores without a legacy checkpoint.
The minimum retention duration, private evidence boundary, history-preserving
current-tree deletion, and verified signed removal manifest remain unchanged.
This implements the retention work described in the
[acquisition and retention proposal](https://github.com/neilweitzel/xevents/pull/135),
not small-first reads.

## Decision

### Eligibility and historical authority

An entire UTC week is eligible only twelve weeks after its end. Every removed
transaction must also have been recorded at least twelve weeks earlier. Keep
the latest capture, and retain any original transaction needed by a surviving
replay. Never split a week or infer UTC from source-claimed times.

Version 1 whole-month checkpoints retain their exact reader and maintenance
path. They cannot be silently converted to version 2 because a withheld cell
does not reveal the exact statistics needed for a partial monthly rollup.
Conversion requires recovered, verified historical evidence. New stores and
stores already using version 2 take the weekly path.

### Private sufficient statistics

Version 2 checkpoints retain the chain anchor, exact removal manifest,
methodology identifier, previous-checkpoint hash, historical suppressed cell
snapshot, cumulative group accounting, and carried listing state.

They also retain candidate fingerprints with first-observation week, sector,
eligibility, fixed reason codes and withdrawal state. These private statistics
permit exact monthly recomputation without publishing small counts. They contain
no names, descriptions or source URLs, but fingerprints are sensitive linkage
data, not an anonymization guarantee. They remain private and subject to the
existing derived-file size cap.

The public projection still applies the same weekly floor, complementary
monthly suppression, cumulative assessment bands and display horizons.
The full before/after public projection must match byte for byte for a freeze
at the same evaluation time, including live rows and header values.

### Corrections and repeat claims

Keep correction records and allow suppression to target frozen candidate
fingerprints. A suppression already effective before freezing is preserved.
A later suppression of a previously eligible frozen claim withholds the
affected weekly and sector-month cells rather than revealing a small numeric
subtraction. The historical pre-correction snapshot remains in private history.
Withdrawal state persists into later checkpoints; no automatic restoration.

An exact normalized group reappearing under a new source listing key does not
add another assessed claim or move its first-observation week. Different sector
evidence or new adverse eligibility evidence for a frozen group refuses the
affected release for explicit correction, rather than silently rewriting it.
This does not implement fuzzy identity matching or independent-source matching.

### Verified application and cleanup

Plan on verified history. Apply to a scratch copy and verify the retained chain
and entire public projection before modifying the live checkout. Recheck after
application. If live application or verification fails, restore the exact
pre-maintenance bytes before returning failure.

The remote store changes only in its signed expected-head data commit, carrying
the new checkpoint and precisely its declared removals. A cancelled local job
cannot publish a partial cleanup.

Remove eligible transaction files, unshared evidence, superseded checkpoints
and regenerable processing snapshots. Do not remove release receipts, outcomes
or correction records: unresolved dependency pruning needs a separate reviewed
ledger and is not part of this migration.

Eligible maintenance runs before source acquisition, including a cadence-only
invocation if required. It does not authorize public publication without a new
complete capture. This amends ADR 0035's no-maintenance cadence-skip path.
Noneligible invocations retain the ordinary skip behavior.

## Verification required before activation

- Two consecutive week freezes preserve the entire public projection and
  link their checkpoint hashes.
- Freezing one of two withheld weeks preserves the legitimate monthly total
  without exposing either exact count.
- No transaction is removed before both week-end and recording-age requirements.
- Suppression before freeze, suppression after freeze, and later freezes keep
  correction state; affected frozen public cells are withheld.
- Same normalized group under a different source key is not double counted;
  groups spanning the boundary remain assigned to their original week.
- Scratch failure leaves live bytes unchanged; post-apply failure restores
  every original byte.
- Retained replays preserve their required originals; legacy checkpoints replay
  unchanged and reject unsupported automatic conversion.
- Unresolved release receipts remain; a near-cap freeze works without any source
  request; malformed statistics and removal paths fail closed.
- Existing private suites, strict types, implementation seal, pinned public
  authority and public admission checks pass.

## Limits

Weekly cleanup reduces the pre-freeze retention tail, not the twelve-week
minimum. It does not cure a burst that exceeds capacity inside that minimum.
History, processing, G5 and checkpoint hard caps remain unchanged.
Adaptive capacity profiles and a cap-safe large-state maintenance redesign
remain separate work.

No source requests, new source activation, cron frequency changes or history
rewrites are introduced. Old sensitive records remain in private git history,
as previously chosen. Long-term research replay and repository growth must be
accounted for separately from current-tree cleanup.
