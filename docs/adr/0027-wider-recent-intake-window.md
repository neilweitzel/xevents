# ADR 0027: Wider recent-intake window

Status: accepted

Date: 2026-09-25

Approval: operator requested the intake fix on 2026-09-25 ("Let's do #1 and
#2 now") and approved it by merging this ADR.

## Context

ADR 0020 limited each automated capture to at most ten recent records. The
source currently lists roughly 20 to 35 claims a day, often in bursts, while
successful captures land 8 to 14 hours apart because scheduled runs are
delayed or dropped and the six-hour guard skips others. In the first burn-in
days, three of five real captures returned the full ten records, so listings
posted between captures were silently missed. A ten-record window covers only
a few hours of source activity.

## Decision

Raise the automated recent-post window from ten to 100 records per capture,
through the same fixed endpoint (`/api/recent/{n}`). At current volume 100
records span about two to three days, so a delayed or skipped run no longer
loses listings. Existing duplicate handling by source key is unchanged, so a
wider overlapping window cannot double-count a claim. A response that fills
the whole window is still recorded as possibly truncated.

Screenshot retrieval stays bounded at ten attempts per capture, taken in source
order among new records. Screenshots of further new records in that capture
are recorded as `deferred`, not failed and not fabricated. Their observations
report the screenshot as unavailable, as they would for a failed retrieval.
Images remain private supplementary evidence and are not classification
inputs.

The six-hour effective-cadence guard and the two-hour trigger from
open-decisions #5 are unchanged. The API body cap of 1 MiB, the 15-second
request deadline and all other transport protections are unchanged.

## Unchanged controls

This changes private collection only. Eligibility, grouping, classification,
the floor of five, G5, the signed proof, the three-file write set and
verified deployment are unchanged. No new source, endpoint family,
credential, permission or public field is introduced.

## Limitations

A wider window reduces gaps between captures; it is not backfill, complete
coverage or de-listing detection. A gap longer than the window, or a burst
larger than 100 records, can still lose listings. Higher intake brings the
private store's fixed capacity limits closer; those remain fail-closed.
