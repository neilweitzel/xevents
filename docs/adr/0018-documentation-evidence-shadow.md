# ADR 0018: Read-only documentation evidence shadow report

- Status: proposed (pending user redline)
- Date: 2026-09-22
- Deciders: project lead; shadow implementation authorized
- Scope: AC1.15 evidence inspection, no change to enforcement

## Authorization and boundary

After merging the reference-contract preparation, the operator authorized
implementation of evidence validation alongside the strict checker, conditional
on clean preflight verification. The preflight passed. This implements a bounded
shadow report under [ADR 0017](0017-documentation-reference-contract.md), not a
new waiver, approval mechanism, publication path or automatic resolution.

The original inventory, strict parser and runner remain unchanged. All accepted
history and pinned plans remain unchanged. The separate
[evidence policy](../reference-evidence.json) is typed, hash-bound review input;
candidate revisions cannot replace its authority while they are being audited.

## What is validated now

- Exact source-document and inventory hashes, with complete finding coverage.
- Current-ruling links to exact decision-log sections, including full-file and
  section hashes and unique decision headings.
- Owner-specific files and directories, exact directory membership, byte hashes,
  requested sections and finite template expansion. This happens only where the
  corresponding owner tree is available.
- Named Python test classes and methods using syntax inspection, not execution.
- The private historical entrypoint mapping and its explanatory document, while
  continuing to report that zero-skip execution evidence is separately required.

The public report never loads a private tree. The private report validates both
its own findings and private-owned public obligations, selecting exactly one
owner namespace for every target. A public namesake cannot replace a missing
private file.

## Honest report vocabulary

Bound means the selected bytes, section or test definition match the trusted
evidence policy. It does not mean production behavior is proven.

| Status family | Meaning |
|---|---|
| Historical ruling bound | Exact source and current ruling are linked; history remains untouched. |
| Owner target/tests bound | Selected target and named test definitions match; tests were not executed by this report. |
| Template targets bound | All finite expansions match the pinned concrete member set and bytes. This is not G5 outcome evidence. |
| Example test bound, not executed | A negative-test definition is linked; no run attestation is inferred. |
| Execution mapping bound, receipt required | The real entrypoint is identified; this tool has not authenticated a zero-skip run. |
| Private not checked | Public checker has no private evidence or read access. |
| External not checked | External ownership is explicit; no remote snapshot is fetched or attested. |
| Planned state unknown | Target presence/absence is reported only within its owner tree. Milestone completion has not been established. |
| Evidence invalid or stale | Binding, shape, membership, section, test definition or source no longer matches. |

Every report retains zero resolved findings. The shadow runner exits nonzero
while raw findings remain, regardless of how many evidence bindings are valid.
An invalid global policy produces a sanitized failed-or-blocked result.

## Trust and invocation

Run the runner itself from a trusted checkout. Supply full immutable revisions
separately for checker code, policy and candidate data; branch names are refused.
The runner checks project-code bytes against the code pin, then executes those
verified bytes directly. It does not load cached bytecode or re-read unchecked
project modules after verification.
Git snapshot loading rejects symlinks, submodules and nonregular entries, with
the existing size/count limits. No candidate module or workflow is executed.

The caller must select a genuinely trusted code/policy revision. A hash supplied
by a caller does not authenticate the caller's authority. This is offline
inspection, not a secure CI producer or a substitute for a reviewed workflow.
Passing a candidate as its own policy revision is not approval to enforce it.

Candidate inventory/policy changes are refused when compared with a distinct
trusted policy. A changed source remains a stale binding, not an automatically
refreshed exception. Evidence-policy changes require their own review.

```sh
python -B tests/invariants/run_reference_evidence.py \
  --code-ref TRUSTED_CODE_SHA --policy-ref TRUSTED_POLICY_SHA \
  --head CANDIDATE_SHA
```

## Deliberately not implemented

There is no milestone-completion registry yet: no state is invented from a merge,
missing artifact or test count. Typed planned obligations identify deliverable,
milestone and acceptance-criterion IDs, but these identifiers are not acceptance
evidence. Candidate-supplied completion/waiver fields are rejected.

The tool does not ingest test-run receipts, authenticate completed test runs,
fetch external evidence, assert semantic equivalence of rewritten documents,
or grant approved status to a mapping. Those require further reviewed contracts
before they could affect enforcement. Existing test execution remains separate,
recorded during PR verification.

## Safety and acceptance

Negative tests cover wrong-owner same-name files, missing or changed targets,
section drift/ambiguity, exact directory membership, malformed/unsafe/empty
template sets, test-definition drift, candidate-edited policies, completion
claims, and scope leakage. Report computation has no network or subprocess
access; only the runners read explicit local Git snapshots.

No workflow, credential, rule, required check, boundary output, G5 gate or live
transport is changed. No claim of completed WS9, WS10, or zero documentation
debt is made. Public first, then private retesting against its actual merge
commit, remains the required merge sequence.
