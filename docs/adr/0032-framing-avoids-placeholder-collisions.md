# ADR 0032: Fixed release framing avoids words that collide with placeholder titles

Status: accepted

Date: 2026-10-09

Approval: operator approved on 2026-10-09 by choosing "Reword statement" for
the G5 false positive, and approved it by merging this ADR.

## Context

The 2026-10-10 00:21 UTC cycle collected a listing whose title is only the
word `private`, with an empty description. G5 adds every `subject_raw` in the
source window to its denylist (ADR 0013 §2). The fixed coverage-boundary
statement used `private` five times, and the evidence manifest carried the
fixed value `verified_private_chain`. G5 quarantined the release, as designed.

Nothing identifying would have been published: the match was a coincidence
between a placeholder title and our own fixed wording. Because G5 scans the
whole retained window, the same listing would have blocked every release for
at least twelve weeks (ADR 0029).

ADR 0013 §6 rules out an allowlist and directs false positives to an upstream
fix. The fixed framing is upstream of the export.

## Decision

- The fixed coverage-boundary statement no longer uses `private` or
  `privately`. It says "not published" and "internal" instead. The meaning of
  every sentence is unchanged.
- The evidence-manifest `evidence_binding` value becomes
  `verified_internal_chain`. It has no consumer other than readers of the
  manifest, and the binding it describes is unchanged.
- G5, its denylist sources, its match rules and its fail-closed outcome are
  unchanged. No allowlist is introduced.

## Consequences

The release blocked on 2026-10-10 can proceed. A future listing whose title
collides with any remaining fixed framing word, including `internal`, will
still be refused by G5. The refusal is now recorded privately as `g5_refused`
rather than a generic status, so the next collision is diagnosable from the
private record. Changing G5 itself, or treating placeholder titles as
non-identifying, needs a new ADR.
