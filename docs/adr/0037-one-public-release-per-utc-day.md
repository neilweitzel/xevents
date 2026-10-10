# ADR 0037: One verified public release per UTC day

Status: accepted

Date: 2026-10-10

Approval: operator approved on 2026-10-10 by choosing "first complete capture
per UTC day" with same-day retry after a failed attempt, and approved it by
merging this ADR.

Amends ADR 0035, which prepared a public release after every complete capture.
Capture-only publication, the `generated_at` reader contract and the recovery
rules of ADR 0035 otherwise stand.

## Context

xevents is longitudinal research. With ADR 0036 the collector reads the source
up to three times a day; publishing after each read would produce up to three
public releases a day whose aggregates differ little, and each release is an
exposure of the proof, admission and deployment path. The operator wants one
public release a day, does not need it at a particular hour, and wants a day
with nothing new or a failed attempt to be visible as such rather than hidden.

## Decision

- Release preparation requires, in addition to ADR 0035's complete capture in
  the same invocation, that no `deployed` outcome has been recorded in the
  private release-outcome audit for the current UTC day. The gate reads only
  private audit records; it needs no public checkout and introduces no new
  external dependency.
- When the gate is closed, the complete capture is still verified, retained,
  processed and persisted privately exactly as before. The run writes a
  `publication_deferred` receipt beside the cadence receipts and succeeds. The
  release and audit jobs are skipped and no App token is minted, the same path
  ADR 0035 uses for cadence-limited runs.
- Only a recorded `deployed` outcome closes the gate. A refused, failed,
  cancelled or unrecorded release does not, so the next complete capture that
  day prepares a fresh, fully verified release. A day with no complete capture
  publishes nothing and the last verified release stays on the site. Manual
  dispatch obeys the same gate.
- A corrupt or unreadable outcome record is an integrity failure that stops
  release preparation for that run; it is never read as "no deployment".
- The release that does publish aggregates the entire retained window, so
  deferred captures are included. "Latest published capture" keeps meaning the
  `generated_at` of the capture that prepared the release; `evaluated_at`
  keeps its meaning. The existing fourteen-day stale warning is unchanged and
  is not a daily uptime promise.

## What the public can and cannot see

A duplicate-only daily release still publishes, so a day with nothing new is
visible as an unchanged release with a newer capture time. A day with no
release means no complete capture or no verified deployment that day; the
reason is retained privately in the receipts and outcome audit. Publishing a
per-release intake status (captures since the previous release, whether an
attempt was incomplete) would change the aggregate schema, the reader and the
exact-output scan together and must be checked against the small-cell rule
before any count is exposed. It is deliberately not part of this decision and
remains an open question for the operator; recording it in the decision log
requires rebinding the documentation evidence that pins that file, which is
left to that separate change.

## Trade-offs

An outcome that was deployed but whose audit record failed to persist can be
followed by one more verified release the same day; the duplicate is harmless
and is visible in the audit. Public visibility of a new listing can lag up to
about a day behind collection, which matches the research pacing of ADR 0035.
The daily boundary is UTC, so the release hour drifts with the capture clock
and will usually fall in the first scheduled read after 00:00 UTC that GitHub
actually starts.

## Verification

Test a second complete capture on the same UTC day (deferred, persisted,
receipt written, no outputs), the first complete capture of the next UTC day
(published), a refused attempt earlier the same day (retried), a deployment
recorded just before midnight (does not block the next day), the gate not
applying when release is disabled or the capture is incomplete, and a corrupt
outcome record failing closed. Observe a real deferred run and the next day's
real deployment before claiming the change is live.
