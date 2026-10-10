# ADR 0039: One chain verification per job, one G5 scan per release, measured stage budgets

Status: proposed (pending user redline)

Date: 2026-10-10

## Context

The Stage A benchmark found repeated work inside each private research cycle:

- The collect job verifies the complete private transaction chain five to seven
  times per run (before and after capture, inside retention planning and its
  scratch and live verification, processing, the headroom report and release
  preparation). Each pass replays every retained transaction; at a full
  retained window one pass takes about 20 seconds.
- On a publishing day the release preparation, including the full G5 scan,
  runs twice: once in the collect job, and again in the release job, which must
  reproduce the receipt and scan the exact outbound bytes before signing.
- The release job holds that second scan plus up to 840 seconds of admission and
  Pages waits inside a 20-minute limit. Job limits were chosen before these
  costs were measured, and stage durations are not recorded anywhere.

The operator accepts long runs as long as they are planned for and visible.

## Decision

### Verify the chain once per job

- Each job that reads private history verifies the complete chain once, from
  the retention checkpoint or the first transaction, exactly as today.
- Later steps in the same process receive that verified result instead of
  re-reading it. A step that writes a new transaction extends the verified
  result by verifying only that new transaction against the verified head, with
  the same checks a full pass applies to it.
- Before any persisted write, the job confirms that the files on disk still hash
  to the verified head and that the remote branch is still at the expected head.
  A mismatch fails closed, as a stale or changed store does today.
- Retention keeps its scratch-copy rule: it applies the change to a copy and
  requires the retained chain to verify from the new checkpoint and every frozen
  cell to reproduce byte for byte, before and after applying. Those two
  verifications are part of the freeze, not repeats.
- The release and audit jobs each verify once, because they run on separate
  runners and must not trust another job's memory.

### Scan once per release, before publishing permission

- The collect job derives and archives the deterministic release receipt
  without running G5. It never emits a receipt to the release job unless every
  other preparation check has passed.
- The release job verifies the chain once, re-derives the receipt and requires
  it to match the archived bytes exactly, then runs the single full G5 scan on
  the exact outbound files. This happens in the credential-free preflight step,
  before the boundary App token is minted.
- The scan result is written to the job's private temporary directory, bound to
  the outbound file hashes and the scan completion time. The publish step
  re-derives the files, requires the same hashes, and requires signing within
  the existing 300 seconds of scan completion. The proof's 900-second expiry is
  unchanged.
- The release outcome recorded by the audit job gains the SHA-256 of the G5
  report (excluding its timestamp) and the scan duration, so the report can be
  reproduced and checked later from the archived receipt and pinned code.
- A G5 refusal still prevents token minting, publication and any public change.

### Stage timing and budgets

- Every run records the duration of each stage (setup, verification, capture,
  retention, processing, headroom, preparation, scan, admission wait, Pages
  wait, audit) in its private record, using fixed stage names only.
- Each stage has a budget derived from measured durations at the largest
  retained window the benchmark supports, with at least a twofold margin. Job
  limits are set to the sum of their stage budgets plus setup, recorded in the
  workflow beside the budget table, and changed only with a new benchmark.
- The headroom report warns when any stage uses more than 60 percent of its
  budget over the trailing 14 days. A warning never shortens a check, skips a
  stage or relaxes a gate; it asks for a reviewed budget or performance change.

## Equivalence and safety tests required before merge

- One verification per job produces exactly the same accepted and refused
  histories as repeated full verification, including tampered transactions,
  broken chains, policy mismatches, cadence violations, changed evidence and
  files altered between verification and write.
- Release receipts, outbound files and G5 reports are byte-identical to the
  current two-scan design for the same store, apart from scan timestamps and
  the new outcome fields.
- A G5 refusal in preflight leaves no token, branch, pull request or public
  change. A changed store between collect and release fails `receipt_changed`.
- Stage budgets are present for every stage, and a run that exceeds a stage
  budget records it without changing the outcome.

## Consequences

At a full retained window the collect job saves about 100 seconds of repeated
verification, and a publishing day runs one G5 scan instead of two. With ADR
0038 the remaining scan cost is small, and the release job's waits keep their
existing limits inside a job limit that is now derived rather than guessed.
Stage durations become measurable, so future limit changes have evidence behind
them. The implementation seal, workflow and private CI pin change together.
