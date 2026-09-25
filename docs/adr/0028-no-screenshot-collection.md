# ADR 0028: Listing metadata only, no screenshot collection

Status: accepted

Date: 2026-09-25

Approval: operator approved dropping screenshots on 2026-09-25 ("yes go ahead
with dropping screenshots") and approved it by merging this ADR.

## Context

ADR 0020 archived source-provided screenshots as supplementary private
evidence, and ADR 0027 capped attempts at ten per capture. None has ever been
captured: the source serves its PNG files with an `image/gif` media type, which
the strict transport check refuses. Images were never classification inputs,
they can contain samples of stolen data, and the source spec already treats the
captured API response as the evidence for an API source.

## Decision

Stop requesting, storing or claiming screenshots. New captures record a
provided screenshot reference as `not_collected` and an absent one as
`not_provided`; observations report the same status. `not_collected` is not a
retrieval failure and is not counted as one. The collection registry records
`screenshots: not_collected`, so each transaction still verifies against the
exact policy it ran under. Transactions from the earlier ten-record and
100-record policies, including any `unavailable` or `deferred` image records,
continue to verify unchanged.

The screenshot transport path is removed from the collector. Image
verification remains only to check historical records.

## Unchanged controls

The 100-record window, six-hour guard, API transport protections, grouping,
eligibility, G5, signed proof, write set and deployment are unchanged. No new
source, endpoint, credential or public field is introduced.

## Consequences

Evidence for each observation is the exact captured listing metadata. There is
no image review, OCR or visual confirmation, which was already the case in
practice. Re-enabling images would need a new ADR covering media handling and
the privacy of stolen-data samples.
