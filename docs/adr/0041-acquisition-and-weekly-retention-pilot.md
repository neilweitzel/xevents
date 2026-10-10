# ADR 0041: Pilot bounded acquisition and weekly research-preserving cleanup

Status: proposed (pending operator review)

Date: 2026-10-10

## Context

Smaller acquisition payloads could reduce private history growth. However,
newest-first ordering does not prove older entries are unchanged, and a source
may add a new entry with an earlier date. Overlap in a 50-item prefix is not
proof that a 200-item read would find nothing else. An unchanged top entry is
not a safe signal to skip the source.

An earlier proposal incorrectly inferred that 50 items were adequate from
counts of new observations alone. Validate raw identities, exclusions and
substantive changes across the whole saved window instead.

Detailed evidence must remain available for at least twelve weeks. Moving
eligible cleanup from whole months to weeks needs a new checkpoint contract;
it cannot discard information required to reconstruct monthly suppression or
carry corrections and provisional deduplication.

## Proposed decision

### Acquisition pilot

Keep the production 200-record capture unchanged during an offline shadow
evaluation. Compare hypothetical 50-record prefixes against the full saved
responses. Report known identities and changed payloads missed by the prefix,
including excluded rows, initialization and size transitions. Never call
retrospective zero observed losses a completeness guarantee.

The proposed next policy allows at most two source requests per acquisition:
an ordinary 50-record response and at most one expanded response. The expanded
tier is selected before that request: 200 ordinarily or 400 after a validated
long-gap/pressure trigger. Never make a recursive 50-to-200-to-400 chain.
Keep the existing source origin, per-response byte bound, a reviewed cumulative
byte bound, exact response evidence and trusted retrieval times.

If the prefix comparison is usable, overlapping and without a pressure
trigger, small-only capture may be considered only alongside periodic
full-window sweeps. Their maximum interval and acceptable missed-change
exposure must be explicitly reviewed after the shadow findings. Until then,
small-only acquisition remains disabled.

A failed normal fetch does not authorize a bigger retry. An unavailable
coverage comparison is unknown, not healthy. Widening history retains each
capture's exact original policy; old registry limits cannot change in place.

### Weekly retention pilot

Produce a read-only plan of weeks whose end is at least twelve weeks before
trusted evaluation time. Do not remove real evidence or write checkpoints in
the pilot.

Before activation, introduce a versioned checkpoint containing:

- immutable published weekly cells and release bindings;
- private sufficient statistics for unfinished monthly rollups;
- cumulative assessment totals, chain anchors and exact removal manifests;
- correction tombstones and approved, bounded late-matching state;
- historical methodology and policy versions.

Preserve public suppressed-versus-zero semantics and the rule preventing a
monthly total from revealing a withheld week. Private sufficient statistics
must never appear in the public checkpoint or output.

Cleanup must be eligible before acquisition and able to run independently of
source availability. Snapshot/receipt pruning is dependency-aware; unresolved
release attempts and their evidence cannot be removed merely because old.
No retained detailed record younger than twelve weeks can be removed.

Activation requires two consecutive synthetic week freezes, month-boundary
reconstruction, later corrections, replay, interrupted-write and near-limit
maintenance tests. Compare the full before/after public projection, not only
frozen rows.

## Boundaries

This ADR is a proposal, not approval to alter production capture, retention,
privacy limits, deletion permissions or source budgets. Existing ADRs 0029,
0036 and 0037 remain authoritative until a reviewed implementation passes.

Git history is not rewritten. Current-tree cleanup does not shrink repository
history. Monitor live-state capacity and repository growth separately.
