# ADR 0023: Coarse research activity in public snapshots

Status: accepted

Date: 2026-09-23

Approval: operator approved the coarse activity disclosure and coordinated
deployment on 2026-09-23.

## Context

An empty research view does not explain the work preceding publication.
The operator requested a plain-English purpose statement and visible
private-assessment versus public-output activity. Exact small private counts
would undermine ADR 0022's disclosure limits.

## Decision

Extend only the aggregate header to `xevents-view1-display/v2`, adding the
integer `assessed_claims_floor`. It is the total number of distinct normalized
actor/subject claim groups in verified retained intake, rounded down to a
multiple of 25. Include ineligible and suppressed groups; repeat observations
of the same group do not increment it. The bounded processor permits at most
10,000 observations, so the field permits multiples of 25 from 0 to 10,000.

Display zero as “Fewer than 25,” covering zero through 24, not as an exact
count or a promise of positive intake. Other values describe the corresponding
25-wide band. Do not break it down by source, sector, period, eligibility gate
or correction reason. This is cumulative grouped-claim activity, not a count
of confirmed incidents or independent sources.

Numeric public-cell sums and numeric-cell counts are derived from already
published rows. Zero published counts means no numeric claims are displayed,
not zero private claims or zero incidents. Never derive a withheld count or
approval rate by subtracting these differently scoped measures.

The reader retains strict v1 compatibility, displaying its missing activity
field as “Not reported.” It rejects unknown keys, invalid bands and public
totals exceeding the assessment band's upper bound. The existing capture
timestamp describes freshness, not workflow health. Invalid and missing
snapshots must not acquire zero-valued metrics.

## Unchanged controls and rollout

All other header and row constraints remain unchanged. The cell floor remains
five. The three-file write set, eligibility rules, immutable evidence,
exact-byte G5 scan, private signed proof, protected merge and verified Pages
deployment all remain mandatory. No new source, credentials, permissions,
manual gate, public names or record-level identifiers are introduced.

Land the backward-compatible public reader before activating the v2 producer.
Update the private reviewed-code seal. The next normal admitted data release
deploys both the new header and the then-current app. Reader-only rollback
requires retaining v2 support or first reverting the producer to v1; never
silently reinterpret v2 as v1.

## Limitations

Bands reduce precision; they do not guarantee anonymity. Threshold crossings,
releases over time and outside information can support inference. No activity
counter asserts that a scheduled execution succeeded or that coverage is
complete. Reassess this narrow disclosure during RC burn-in.
