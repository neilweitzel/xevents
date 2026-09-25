# ADR 0024: Run completion timestamp in public snapshots

Status: accepted

Date: 2026-09-25

Approval: operator requested the "accurate as of" display on 2026-09-25 and
approved it by merging this ADR with its coordinated reader.

## Context

The page shows only the latest source capture. The private store refuses a
new capture within six hours of the previous one, so a scheduled run that
completes without a new fetch still publishes a signed release, but the page
looks unchanged. Viewers and the operator cannot tell from the page that the
most recent run completed. ADR 0023 stated that the capture timestamp
describes freshness, not workflow health.

## Decision

Extend only the aggregate header to `xevents-view1-display/v3`, adding
`evaluated_at`: the whole-second UTC time at which the private release run
evaluated the snapshot. It equals the `Release evaluation` time already
published in the coverage-boundary statement. The producer rounds the clock
up to the next second, so `evaluated_at` is never earlier than
`generated_at`. The reader requires the field in v3, requires whole-second
form, refuses values earlier than the capture or more than five minutes
ahead of the viewer's clock, and displays it as "Accurate as of".

This supersedes ADR 0023's statement that no public field describes run
completion, only for this one timestamp. It adds no per-run counts, outcome
codes, failure reasons, next-run estimate or delayed/health status. A failed
run publishes nothing, so the timestamp simply stops advancing. No inference
about why is displayed.

## Unchanged controls and rollout

All other v2 header and row constraints remain unchanged, including the
assessment band and the cell floor of five. The three-file write set,
eligibility rules, immutable evidence, exact-byte G5 scan, private signed
proof, protected merge and verified Pages deployment remain mandatory. No new
source, credential, permission, manual gate, public name or record-level
identifier is introduced.

Land the reader, which keeps v1 and v2 support, before activating the v3
producer. Update the private reviewed-code seal. The next admitted data
release deploys both. Reader-only rollback requires retaining v3 support or
first reverting the producer to v2.

## Limitations

The timestamp shows that a release run completed and was admitted. It does not
assert complete coverage, source availability or that every scheduled
execution ran. The 14-day stale-capture notice is unchanged.
