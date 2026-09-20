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

- **Assumed in docs (PROPOSAL, ADR 0002):** no contact at all — no queries,
  manual or automated. A carve-out for minimal, documented, single-fact
  manual lookups (never automated, never at bulk) exists only if the user
  approves it; bulk derivation, storage at scale, republication, and any
  build/run-time dependency are excluded under every option.
- **Question:** Is even manual query-level use too close to the line, or
  acceptable under the documented constraints (minimal, documented, never
  automated at bulk)?
- **Unblocks:** ADR 0002 finalization. (If the answer is "no contact at all,"
  nothing changes; if a carve-out is approved, the rule becomes: minimal,
  documented, never automated at bulk.)

## 5. Polling cadence

- **Assumed in docs (UNSET):** the poller runs on a schedule, but the
  interval is unset. Proposals on the table: every 2 hours (RansomLook
  operator guidance, cited in ADR 0007) and every 6 hours (decision-brief
  Q3, ≈18h de-listing detection latency).
- **Question:** What is the MVP polling interval for RansomLook?
- **Unblocks:** ADR 0007 finalization; open decision #3 (the N-missed-polls
  threshold is calibrated against cadence); MVP scope item 6.

## 6. ransomwatch historical baseline

- **Assumed in docs (PROPOSAL, docs/mvp-scope.md item 8):** the frozen
  ransomwatch 2020–2025 archive (Unlicense) is loaded as observations to
  seed history; no live polling of the dead source.
- **Question:** Accept the baseline proposal, reject it, or defer it to
  post-MVP?
- **Unblocks:** MVP scope item 8; the archive independence-class question
  (data-model.md).

## 7. Operational surface form and audience

- **Assumed in docs (UNSET):** MVP scope item 7 describes what the surface
  shows, not what it is (local web UI, CLI, static export, hosted app — all
  unexamined) nor who it serves (project lead only, or public).
- **Question:** Is the MVP surface a local-only tool or a public surface?
  What form does it take?
- **Unblocks:** the build plan for scope item 7; ADR 0003's pre-public-surface
  gate (the written lawful-basis / public-interest research memo is required
  before any public serving — "no memo, no public surface"); auth/hosting
  decisions.

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
