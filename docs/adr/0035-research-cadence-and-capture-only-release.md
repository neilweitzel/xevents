# ADR 0035: Eight-hour capture spacing and capture-only releases

Status: accepted

Date: 2026-10-10

Approval: operator explicitly approved both eight-hour spacing and
capture-only publishing on 2026-10-10.

Supersedes ADR 0033 for new captures and ADR 0024's per-run heartbeat
publication and display. Earlier decisions remain the historical record.

## Context

xevents aggregates evidence for longitudinal research, not real-time
blocking. Releasing on every timer invocation creates unnecessary public
changes even when collection was cadence-limited and no source was read.
The four-hour spacing in ADR 0033 optimized collection frequency rather than
the research requirement. Eight hours is the operator's chosen compromise.

The two-hour GitHub schedule is a retry opportunity, not a promise of a read
every two hours or three fixed daily read slots. If a trigger is dropped,
the next actual invocation checks elapsed time from the last saved capture.
More frequent opportunities do not bypass the minimum spacing.

Observed overlap supports reducing read frequency, but neither historical
overlap nor a recent-100 endpoint guarantees future completeness. A burst
or sufficiently long platform outage can still overrun the window. No cron
minute, freshness guarantee or external recovery service is introduced.

## Decision

- New captures use the `research` policy: the existing metadata-only
  claim-identity policy with `effective_cadence_seconds: 28800`.
  The `spaced` policy retains 14400 seconds; earlier policies retain 21600.
  History verification uses the policy of each capture. Raw evidence and
  previous records are never rewritten to fit the new cadence.
- Keep `59 */2 * * *` and the recent-100 request. Collection is due when
  at least eight hours have elapsed since the previous committed capture.
  Manual dispatch obeys the same guard. Partial captures remain durable
  evidence and advance that capture clock just as before.
- A cadence-limited invocation verifies the current private history,
  persists its existing private cadence receipt through the signed,
  expected-head data-only write, and succeeds without retention, processing,
  release preparation or release outputs. Public release and its outcome
  audit are skipped; no App token is minted for those jobs.
- Public release preparation requires an actual complete capture in this
  invocation and successful prerequisite stages. A complete capture containing
  only duplicates still qualifies: the source was genuinely read. Failed or
  partial captures never authorize publication.
- Retention and processing continue on actual capture attempts. Integrity,
  privacy, proof and deployment failures remain failures, not cadence skips.
  The last verified public release remains available.

## Timestamp semantics

Show **Latest published capture** using `generated_at`, the trusted source
retrieval time already present in every supported aggregate schema. It means
the latest capture represented in the displayed published snapshot, not the
time of deployment or the latest invocation.

Keep `evaluated_at` and all schema validation unchanged: it remains release
evaluation time, not a new capture time, deployment time or successful-run
heartbeat. Older heartbeat-only releases are read honestly using their original
capture timestamp. The existing fourteen-day stale-data warning is unchanged;
it is not an eight-hour uptime promise.

## Recovery and trade-offs

A failed preparation or publication after a committed capture is not retried
by a cadence-only heartbeat. The next complete capture prepares a fresh,
fully verified release; it can include earlier retained evidence. Append-only
corrections become public at that next complete capture too. This avoids
silently reintroducing heartbeat releases as a recovery mechanism. An urgent
withdrawal or different recovery policy requires an explicit reviewed decision,
not a bypass of the capture or publication gates.

Two reads per day is an operating expectation, not an SLA. Platform outages
and source bursts remain visible limitations. Reconsider the policy if overlap
erodes; do not infer missing records solely from elapsed time.

## Verification

Test just below and exactly at eight hours, historical four- and six-hour
policy replay, mixed-policy history, no-source/no-release cadence runs,
duplicate-only captures, partial and failed attempts, no job outputs on
failure, and unchanged privacy and signing controls. Verify a real
cadence-limited workflow has skipped release and audit jobs. A fresh-capture
deployment must be reported separately, only after it is observed.
