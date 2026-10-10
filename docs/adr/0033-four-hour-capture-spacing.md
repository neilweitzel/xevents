# ADR 0033: Four-hour minimum spacing between source captures

Status: accepted

Date: 2026-10-09

Approval: operator approved on 2026-10-09 by choosing "Yes, 4 hours" after
reviewing the measured schedule analysis, and approved it by merging this ADR.

## Context

ADR 0020 set a two-hour GitHub Actions trigger with a six-hour minimum between
successful source captures, intending about four reads per day. Burn-in
measured something different (2026-09-24 to 2026-10-10, private issue #33):

- GitHub started 68 of about 192 scheduled slots, about 4.3 runs per day, with
  a median start delay of about 53 minutes. xfeeds, scheduled at a different
  minute, shows the same rate, so the cron minute is not the bottleneck.
- Because runs arrive roughly every six hours with jitter, many land just
  under six hours after the previous capture and are skipped. 24 runs were
  skipped by the guard after the window was widened, most of them 3.3 to 6.0
  hours after the last capture.
- Since 2026-09-25, real captures averaged 2.9 per day. Gaps between captures
  had a median of 7.6 hours, a 90th percentile of 11.4 hours, and a maximum of
  14.2 hours. Twelve gaps exceeded ten hours.

Every capture since the 100-record window still overlapped the previous one,
so the risk is delay and reduced margin in bursts, not observed loss.

## Decision

- A new collection policy, `spaced`, applies to new captures. It is the ADR
  0031 `claim` policy with one change: the minimum time between successful
  captures is four hours. The registry records
  `effective_cadence_seconds: 14400` for this policy.
- Each capture is verified against the spacing of the policy it ran under.
  Captures under earlier policies still verify against six hours. The spacing
  check compares a new capture with the previous capture, whatever policy that
  one used.
- The two-hour trigger, the cron minute and the 100-record window are
  unchanged. The guard still never allows more than six reads per day.

Replaying the measured run start times under a four-hour guard gives about 3.9
captures per day, a median gap of about 6.2 hours, a 90th percentile of about
8.3 hours, and two gaps over ten hours. That is close to the one read per six
hours ADR 0020 intended.

## Consequences

Source load rises from about 2.9 to about 3.9 bounded requests per day. Overlap
between captures increases, so more listings are seen as duplicates, which is
the intended coverage margin. Changing the schedule, the spacing or the window
again needs a new ADR.
