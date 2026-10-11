# ADR 0045: Near-ceiling runtime budget calibration

Status: accepted

Date: 2026-10-11

Approval: operator authorized bounded capacity implementation and green-check
merges. This calibrates its runtime envelope to the final stress measurements.

## Context

ADR 0044's sixteen-week profile tests passed. Before activating the private
implementation, an additional final-code test combined near-ceiling history
with a larger reporting horizon and ordinary formatted synthetic source bodies.
Its complete scan and verified maintenance passed, but several stages exceeded
the measurements used for the provisional 28/57-minute job limits.

The final fixture contains 124,320,913 history bytes, 15,321 live observations
and an estimated 30,530 G5 entries. Cold verification takes 28.95 seconds;
capacity sizing 29.74 seconds; processing 2.29 seconds; preparation after
verification 27.75 seconds; full G5 561.47 seconds; verified cleanup
167.79 seconds. Peak resident memory is 619.5 MiB.

Without maintenance its next-acquisition reservation correctly refuses at the
history high-water mark. Verified cleanup reduces history to 107,081,399 bytes
and live observations to 9,521 while preserving the complete projection
byte-for-byte. No real source requests, production promotions or public
research releases are inferred from this synthetic fixture.

## Decision

Supersede only ADR 0044's provisional job-budget numbers. Retain the existing
1.8 runner calibration multiplied by at least two, round stage budgets upward,
and keep budget/workflow agreement enforced by CI.

| Collection stage | Seconds |
|---|---:|
| verify | 300 |
| capacity | 120 |
| capture | 60 |
| retention | 720 |
| processing | 30 |
| preparation | 120 |
| headroom | 120 |
| persist | 240 |

| Release stage | Seconds |
|---|---:|
| reconstruct | 300 |
| scan | 2,160 |
| publish | 300 |
| admission | 420 |
| Pages | 420 |

Setup remains 180 seconds per job; audit remains 240 seconds. Derived job
maxima are **32 minutes collection, 63 minutes release, seven minutes audit**.
The complete maximum serial path is 102 minutes including these setup
allowances, below the two-hour trigger interval. Queuing and service outages
remain provider-dependent; the six-hour source guard remains the authority.

Budgets are warnings and maximum job limits, not expected ordinary runtimes.
The headroom budget covers the same sizing work measured by the capacity stage.
No check is sampled, skipped or terminated merely for exceeding its advisory
stage budget. Scanning remains before signing, with unchanged signing
freshness and proof expiry.

## Unchanged scope

All resource profiles, thresholds, promotion provenance, cooldown, ceiling
refusal, twelve-week detailed retention, replay, correction, publication,
transport and privacy requirements of ADR 0044 remain unchanged. Source reads
stay at 200 and the independent-source and small-first pilots stay inactive.

The previously discovered pathological unbroken-metadata runtime remains a
separate follow-up. These measurements do not certify adversarial worst-case
screening, physical repository growth or unlimited reporting horizons.
