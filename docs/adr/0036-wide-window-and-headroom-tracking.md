# ADR 0036: 200-record window, six-hour spacing and headroom tracking

Status: accepted

Date: 2026-10-10

Approval: operator approved on 2026-10-10 after reviewing the measured capture
history and scheduler replay below, choosing six-hour spacing and a 200-record
window, and approved it by merging this ADR.

Supersedes ADR 0035's spacing and ADR 0027's window for new captures. Earlier
decisions remain the historical record for the captures made under them.

## Context

ADR 0035 set eight hours between source captures and kept the two-hour GitHub
trigger as a retry net. The private capture history and the scheduler record
were measured before changing anything (2026-09-23 to 2026-10-10):

- Over 14 days at 100 records, 40 complete captures saw 514 new listings
  (about 36.7 per day): a median of 8 and a 90th percentile of 42 new per
  capture, a maximum of 46, and a duplicate floor of 54. No 100-record window
  was ever filled by new listings after the initial widening.
- The source's own timeline over the same period peaked at 73 listings in any
  24 hours, 128 in 48 hours, 186 in 72 hours and 221 in 96 hours. A 100-record
  window therefore survives roughly one day of missed reads at peak; 200
  survives about three.
- GitHub started 70 of 200 scheduled slots (35 percent), and the misses are
  slot-dependent: two of the twelve daily slots never started in 17 attempts.
  Replaying the observed starts against the eight-hour guard gives 2.1 real
  captures per day with a longest gap of 14.5 hours; against a six-hour guard,
  2.95 captures per day with a longest gap of 13.2 hours.
- Replaying the same starts with a four-, six- or eight-hour trigger instead of
  two hours gives 0.7 to 1.5 real captures per day and longest gaps of 25 to
  144 hours. The trigger density is what keeps reads happening; the guard is
  what spaces them.

The earlier finding that reading every two hours was not fruitful is correct
and already addressed by spacing. It does not support widening the trigger.

## Decision

- A new collection policy, `wide`, applies to new captures: the ADR 0035
  `research` policy with two changes. Each capture requests up to 200 recent
  records through the same fixed endpoint, and the minimum time between
  successful captures is six hours. The registry records
  `maximum_records: 200` and `effective_cadence_seconds: 21600`.
- Every earlier policy keeps its exact registry record, 100-record limit and
  spacing. History verification uses the policy each capture ran under, and a
  capture can never be wider than the registry record it will verify against.
  Raw evidence and previous records are never rewritten.
- The `59 */2 * * *` trigger, its minute, and the rule that the two-hour
  trigger is a retry net rather than a read schedule are unchanged. Three reads
  per day is the ceiling the guard allows, not a promise; GitHub scheduling
  remains the accepted dependency.
- Every complete capture writes a private, advisory window-headroom report
  derived only from trusted retrieval times and new/duplicate counts over the
  trailing 14 days: arrival rate, maximum new per capture, duplicate floor,
  peak new listings in 24, 48 and 72 hours, longest gap, and fill time at the
  peak 24-hour rate. The report flags `review_window` when any complete
  capture overlapped its predecessor by less than half the window, when the
  72-hour peak would fill the window, or when fill time at peak is less than
  twice the longest observed gap. A flag adds a run annotation with fixed
  reason codes only.
- The report never changes the window. Widening, narrowing or re-spacing again
  requires a new ADR citing the report. Applied to the measured history, a
  100-record window flags (171 new in a 72-hour span); 200 records does not
  (fill time about 61 hours against a 14-hour longest gap).

## Consequences

Source load rises from about 2.1 to about 3 bounded requests per day, each
reading twice as many records (about 123 KB per response against a 1 MiB
limit). Overlap between captures increases, which is the intended margin
against missed scheduler starts and bursts. Partial and failed captures, the
privacy, signing and admission controls, and the `generated_at` reader contract
are unchanged. Public text that states the window or spacing is updated in the
same change as this ADR.

## Verification

Test the exact six-hour boundary for the new policy and the exact eight-hour
boundary for `research` captures, mixed six-, four-, eight- and six-hour chain
replay, a 200-record capture, refusal of 201, refusal of a 200-record request
under any earlier policy before any network call, the headroom report's
insufficient-data, adequate and each flagged case, and that the report path is
inside the private write set but outside the retention-removable set. Observe
a real 200-record capture and its report before claiming the change is live.
