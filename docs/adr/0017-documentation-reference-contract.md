# ADR 0017: Explicit documentation reference ownership and disposition

- Status: proposed (pending user redline)
- Date: 2026-09-22
- Deciders: project lead
- Scope: preparation for M1 AC1.15 and WS9, not CI activation

## Recommendation and authority

Adopt explicit, source-bound reference dispositions instead of broad filename
exceptions or copying private artifacts into the public repository. Preserve
the distinction between a real required target, a future deliverable, a bounded
example, and a target that this audit is not authorized to inspect.

The operator requested preparation of the next increment after public PR #26.
This ADR prepares the contract anticipated by [ADR 0016](0016-documentation-context-and-current-rulings.md);
it does not approve new failure semantics. The existing Docs QA command remains
strict and unchanged. A successful inventory test means the proposal is complete
and its source anchors still match, not that its findings have been resolved.

The supported MVP requirement is documentation consistency under AC1.15 in the
[implementation plan](../implementation-plan.md). No accepted ADR body or pinned
implementation-plan/checklist bytes are edited.

## What this preparation implements

The public inventory is [reference-findings.json](../reference-findings.json).
It covers the 23 diagnostics at public revision
`4471d5273674ef3c158c6f1c6ffc160ddf4bd0d3`, with links back to the original review
IDs. Each entry retains the raw source path, diagnostic code, detail, line and
SHA-256 of the entire source document. This deliberately conservative binding
requires renewed review even when an unrelated part of the source changes.

The validator checks a closed versioned field set, unique IDs, explicit ownership,
milestones for planned items, and exact coverage of the supplied raw diagnostics.
Missing, duplicate, newly untracked, or stale records fail inventory validation.
Deleting a finding from the proposal is not a way to hide it.

Its output always says `proposal_only: true` and `resolved_findings: 0`. Neither
runner consumes the inventory. The existing raw diagnostics and exit codes
remain authoritative. This is review tooling, not an allowlist.

The validator does not prove that an ownership choice, action, or authority
description is correct. Those are human-review fields. It does not authenticate
Git revisions, approve doctrine, inspect remote files, or verify milestone
completion. Trusted callers must independently load and identify their snapshots.

## Proposed classification contract

The following behavior needs explicit approval and later implementation. In all
cases, an unmapped or ambiguous reference remains blocking; nearby words such as
private, future, historical, or example never grant an exemption.

| Class | Required evidence | Proposed reporting, not current CLI behavior |
|---|---|---|
| Required local | Exact owner, safe canonical path, expected file/directory type; existing target and requested section in the audited snapshot. | Missing target, wrong type, empty required directory or missing section blocks. Presence alone does not prove operational readiness. |
| External public | Explicit repository, immutable revision, exact path, content digest, and a separately reviewed public evidence record. | Offline audit reports external-not-checked until matching evidence is available; no network fallback, floating-main verification or local-copy requirement. |
| Private-owned | Explicit private owner; private verification against a pinned public revision. | Public audit reports private-not-checked, never verified. The private audit must validate the exact target and requested section/type without public export of its report. |
| Planned | Owner, deliverable ID, due milestone, acceptance criteria, and trusted milestone-state evidence. | Absent artifact remains visible as planned-outstanding, not existing or verified. Missing state is unknown/blocking. Once its milestone is claimed complete, absent or untested delivery blocks. |
| Bounded template | Exact literal spelling, a fixed variable grammar, authoritative finite expansion set and expected target structure. | Validation belongs to the owner; reject unknown expressions, empty sets, traversal, absolute paths, symlinks and missing concrete targets. Never evaluate workflow expressions or shell text. |
| Example | Exact source unit, pedagogical purpose and a named executable negative test. | Report example-validated only after that evidence exists; never exempt unrelated nearby references or create fake documents. |
| Preserved history | Immutable historical body plus exact current-ruling section and hashes of both source and authority. | Report historical-ruling-linked, not text rewritten. New active uncertainty elsewhere still blocks. |
| Historical target | Exact old source spelling and an approved execution mapping, with owner-side evidence for the actual entrypoint. | Report execution-mapped, not old-path-exists. Require the real test to run with zero skips; keep the old absence visible. |

Ownership and reference kind are independent. In particular a private future
deliverable is planned and private-owned, not a verified private target. Two
references to one future artifact represent one delivery obligation, not two.

## Trusted state and anti-waiver design

Use a version-controlled milestone registry, reviewed separately from the
untrusted candidate. Its proposed fields are: milestone ID, owner role, state
(not-started/in-progress/complete), complete deliverable-ID set, acceptance
criterion IDs, immutable evidence revisions, and operator acceptance reference.
The role is project lead; personal identity is not needed in public output.

No current milestone is marked complete by this preparation. Initial registry
state must be reviewed rather than inferred from missing files, checkbox prose,
test totals, or a successful merge. Missing evidence is unknown, not not-started.
Advancing to complete requires every deliverable and acceptance criterion,
including owner-private verification where applicable.

A future trusted CI consumer reads policy, parser, inventory and milestone
registry from a separately approved base revision. Candidate PR metadata or a
candidate-edited registry cannot approve its own missing deliverables. A PR that
changes both a target and its disposition requires staged policy review; it
cannot use its new disposition to pass that same PR. Base-to-head downgrade or
deletion of a completion assertion must be rejected absent a separately accepted
change record. Missing/stale evidence fails closed.

For preserved decisions, validate the exact decision number and section hash in
the current authoritative log, in addition to the historical source hash. A
changed current ruling requires a newly reviewed linkage, not continued reliance
on an old blanket disposition. Never edit accepted history merely to clear lint.

An eventual enforcement schema must replace free-text authority/action fields
with typed, hash-bound evidence objects and expected section/type selectors.
The preparation inventory is deliberately not that enforcement schema.

## Privacy and report scope

Public records contain only locations and obligations already stated in public
documents. They include no private repository revision, fixture IDs, replacement
entrypoint, private inventory, raw report, or evidence digest.

The private companion may retain its exact targets and evidence locally. A
same-named public file cannot satisfy a private-owned obligation; target lookup
must select one owner tree rather than merge namespaces. No public job gains a
private checkout, credential, private-result API, or success attestation from
this proposal.

Public-not-checked is not an end-to-end pass. Any later scoped public success
must explicitly distinguish what was checked from owner-private obligations.
Cross-boundary proof and aggregation of private outcomes remain a separate
unapproved contract under [ADR 0015](0015-private-invariant-verification.md).

## Proposed implementation sequence and acceptance

- Approve or redline this contract and each inventory disposition first.
- Implement typed evidence validation in shadow mode, alongside raw findings;
  preserve the existing strict command and nonzero exit semantics.
- Test missing/moved targets and sections, wrong owner despite same-name files,
  duplicate IDs, source/authority hash drift, malformed templates, unsafe paths,
  zero template expansions, incomplete milestones and self-authorizing changes.
- Validate execution mappings and concrete template targets privately, using a
  pinned public checker revision. Keep full private test evidence private.
- Review the shadow report before separately approving any CLI-policy switch.
  Define precisely whether scoped not-checked and outstanding items block each
  command; do not manufacture a global all-clear.
- Only then consider WS10 wiring and separately authorized required checks.

Completion of this preparation means every current finding has a reviewable
disposition and the anti-staleness tests pass. It does not mean zero raw
findings, resolved milestone deliverables, accepted doctrine, completed WS9,
completed WS10, or permission to publish.

## Non-goals

No workflow or status-check activation, dispatch, App credential use, branch
protection change, boundary write, public proof, correction-export contract,
future ingestion pipeline, or empty placeholder target is added. G5 remains
fail-closed for boundary-related public PRs. This document does not settle any
unrelated release, source, privacy or publication decision.
