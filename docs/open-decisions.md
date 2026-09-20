# xevents — Open decisions

Decisions only the user can make. Nothing in the docs that touches these
items is final; each section names the assumption currently baked in (marked
PROPOSAL) so a future agent knows exactly what would change if the user
decides differently.

## 1. Confidence band granularity

- **Assumed in docs (PROPOSAL, ADR 0006):** bands
  `unverified / low / moderate / high / disputed`; bands only, no bare
  numbers; weights are internal model inputs.
- **Question:** Is this the right set and granularity? Alternatives include
  collapsing `unverified`/`low`, or adding granularity at the top end.
- **Unblocks:** ADR 0006 finalization; MVP scope item 5.

## 2. ransomware.live manual cross-checks

- **Assumed in docs (PROPOSAL, ADR 0002):** manual, query-level cross-checks
  of individual facts are acceptable; bulk derivation, storage at scale,
  republication, and any build/run-time dependency are not.
- **Question:** Is even manual query-level use too close to the line, or
  acceptable under the documented constraints (minimal, documented, never
  automated at bulk)?
- **Unblocks:** ADR 0002 finalization. (If the answer is "no contact at all,"
  the carve-out paragraph in ADR 0002 is deleted.)

## 3. De-listing detection threshold

- **Assumed in docs (UNSET, ADR 0007):** the threshold is parameterized —
  N consecutive missed polls and/or confirmation across independent pollers —
  but N is unset and the confirmation rule is unwritten.
- **Question:** What counts as a removal? N consecutive missed polls (and
  N = ?), multi-poller confirmation, or something else?
- **Unblocks:** ADR 0007 finalization; MVP scope item 6. (Decide once polling
  cadence is chosen.)

## 4. Dispute-channel response SLA for v1

- **Assumed in docs (UNDECIDED, ADR 0004):** a published dispute/correction
  process ships from day one with manual handling; no response-time
  commitment is stated.
- **Question:** Should the v1 docs state a response-time commitment (e.g.
  acknowledge within N days), or state best-effort with no SLA?
- **Unblocks:** ADR 0004 finalization; MVP scope item 6.
