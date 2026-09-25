# ADR 0029: Rolling private retention with frozen public aggregates

Status: accepted

Date: 2026-09-25

Approval: operator approved a rolling window with aggregation beyond it, and
removal from the current tree without rewriting history, on 2026-09-25, and
approved it by merging this ADR.

## Context

The draft retention policy kept the private ledger forever. Private processing
snapshots and release receipts grow with every retained claim, and at current
intake they would reach their fixed size limits within months. Holding victim
names indefinitely is also more than this research needs.

## Decision

- **Retained window.** Detailed private records are kept for at least twelve
  weeks. A calendar month (holding the weeks whose Monday falls in it, as in
  ADR 0026) becomes eligible once its last week ended twelve or more weeks ago.
  The month of the latest capture always stays live. Months freeze whole and
  in order, so raw data lives about 12 to 16 weeks.
- **Freezing.** When a month is eligible, the private cycle computes the
  release as usual, then records that month's published weekly and monthly
  cells, exactly as published, in a single retention checkpoint. The checkpoint
  also carries: the hash of the last removed transaction, which anchors the
  retained chain; source keys still needed to recognize a repeated listing (not
  names); the cumulative grouped-claim count behind the assessment band; and
  the list of removed paths. It holds no names, descriptions, URLs or source
  text.
- **Removal.** The removed month's transactions, their unshared evidence
  files, superseded processing snapshots and release receipts, corrections for
  removed candidates and the previous checkpoint are removed from the working
  tree. Git history is **not** rewritten. The unattended writer removes only
  paths of those kinds, only when the same signed commit adds the new checkpoint,
  and only exactly the paths it lists.
- **Verification.** Before anything is removed, the cycle applies the change
  to a scratch copy and requires the retained chain to verify from the
  checkpoint and every frozen cell to be reproduced byte for byte. It checks
  again after applying. Any failure leaves the remote store unchanged and fails
  the run visibly.
- **Publication.** Releases combine frozen cells for frozen months with live
  cells for retained months. The assessment band is cumulative across
  checkpoints; its public bound rises from 10,000 to 1,000,000. To stay inside
  the reader's bounds, the oldest whole months drop off the public matrix once
  it would exceed 104 weeks or 25 months.
- **Size.** Derived private files may reach 8 MiB, instead of the 4 MiB
  source-transaction limit, which covers the 16-week worst case at current
  intake.

This supersedes the draft retention policy's indefinite ledger and hot, warm
and cold tiers for private records.

## Consequences

- A frozen cell can be withheld but not recalculated. Corrections that need
  record-level evidence must happen inside the retained window.
- Data removed from the tree remains in private git history, as chosen. Truly
  deleting it would need a separate, explicit history rewrite.
- A listing re-posted under a new source key after its month is frozen can be
  counted again. This is rare and small.
- Cross-release inference limits (ADR 0023, ADR 0026) are unchanged.
