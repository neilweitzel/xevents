# ADR 0031: The screenshot reference is not part of a listing's claim

Status: accepted

Date: 2026-10-08

Approval: operator approved on 2026-10-08 ("we need to not let that fail since
we don't care about screenshots") and approved it by merging this ADR.

## Context

ADR 0028 stopped collecting screenshots. The collector still treated the
source's `screen` value as part of a known listing's identity: any change to a
stored listing, including that field, was recorded as `changed_source_item`,
marked the capture `partial` and withheld that cycle's release.

The source routinely fills the reference in after first publishing a listing.
290 of the first 562 retained listings had no reference when first captured.
On 2026-10-08 three listings came back identical except for a newly added
reference, and the cycle stopped. Across every retained capture, `screen` is
the only field that has ever changed on a known listing. The reference is not
a classification input, is never fetched, and is often an image whose served
media type does not match its contents.

## Decision

A new collection policy, `claim`, applies to new captures. It is the ADR 0028
metadata policy with one change: a listing's claim is every source field except
`screen`.

- A known listing whose bytes differ only in `screen` is a duplicate with code
  `known_item_metadata_refresh`. It is not an error and does not make the
  capture partial. The first-seen observation, its `item_hash` and its evidence
  are unchanged; the refreshed bytes remain in the new capture's exact evidence.
- A change to any other field is still `changed_source_item` and still needs
  the correction path. A `screen` change never masks a change elsewhere.
- Copies of one listing in a single response that differ only in `screen` are
  not a conflict. Copies that differ in the claim are still all rejected.
- `screen` is opaque under this policy: any JSON value is retained exactly in
  private evidence, never parsed, fetched or validated as a path.
- The decision uses only carried listing state, so it survives retention.
  Listing state written under this policy carries a claim hash. State written
  earlier has none; a change is then accepted only when restoring a null
  reference reproduces the stored hash exactly, meaning the source added a
  reference and changed nothing else. Anything else fails closed.
- The registry records `claim_identity: all_fields_except_screen`, so each
  transaction verifies against the exact policy it ran under. Captures recorded
  under earlier policies, including the partial capture of 2026-10-08, replay
  unchanged.

## Unchanged controls

The 100-record window, six-hour guard, API transport protections, metadata
indicator screen (which still reads every string field), grouping,
eligibility, G5, signed proof, write set and deployment are unchanged. No new
source, endpoint, credential or public field is introduced.

## Consequences

Screenshot references no longer stop collection or publication. A listing
first captured before this policy with a non-null reference, whose reference
later changes, still fails closed while it remains in the recent window,
because its earlier reference value is not carried in state. Re-enabling
images, or treating any other field as non-claim metadata, needs a new ADR.
