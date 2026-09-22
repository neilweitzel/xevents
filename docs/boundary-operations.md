# Boundary operations guide

Status: proposed (pending user redline)

This public-safe guide documents the current boundary posture and the
conditions for future operation. Its authority is ADR 0012's retained
boundary and key-management provisions, ADR 0014's PR transport design,
ADR 0015's privacy-preserving verification increment, and
[the WS6 separation](ws6-boundary-separation.md).

## Current operating state

The system has a private scanning and archiving implementation, public
invariant-check code, and a baseline public branch ruleset. These are not
a live publication pipeline. Unit tests and fixture runs are not evidence
that a real batch was published.

The public G5 check deliberately refuses every boundary-related PR until
a separately approved public-proof contract exists. Renaming a branch,
changing its author, pasting a report, or adding a report URL cannot make
the unimplemented validator return success.

No public job may check out private state, import private code, or receive
a credential for private reads. Scanning, private archiving, and public
publishing remain separate operations; the presence or historical name of
a private workflow is not evidence that publishing is implemented.

## Before an operator runs anything

1. Identify the intended action: read-only inspection, private synthetic
   testing, private scanning, private archival, or publication. Do not
   substitute one action's evidence for another's acceptance criteria.
2. Verify the exact repository, branch, and full commit ID. Use trusted
   checker code and record separately which revision's data is audited.
3. Confirm the action has been authorized. A merged test implementation
   does not authorize a workflow dispatch or live publication.
4. Keep raw evidence, scan reports, logs, internal identifiers, and
   credentials private. Use the approved private operator instructions
   for private commands; do not paste their output into public PRs.
5. Treat a failed, missing, stale, or unimplemented required control as
   blocked. Correct inputs or implementation through a reviewed change;
   never disable a gate to move a batch through.

## Public read-only checks

Run from a trusted public code checkout using full 40-character revisions.
These commands read snapshots; they do not dispatch a workflow or mint
a token.

```sh
python -B tests/invariants/run_checks.py boundary-write-set --head HEAD_SHA
python -B tests/invariants/run_checks.py jsonl-headers --head HEAD_SHA
python -B tests/invariants/run_checks.py nygard-immutability --base BASE_SHA --head HEAD_SHA
python -B tests/invariants/run_checks.py docs-qa --head HEAD_SHA
```

Docs QA currently has unresolved reference and preserved-history findings.
Its nonzero exit is intentional until the applicable cleanup and
interpretation contracts are approved. Do not install it as a required
check by hiding or grandfathering those findings.

The PR-scoped checks additionally require a PR number and the exact head
SHA. They fetch public metadata, bind it to that head, and reject changes
while the check is reading the PR.

```sh
python -B tests/invariants/run_checks.py boundary-write-set-in-diff --pr NUMBER --head HEAD_SHA
python -B tests/invariants/run_checks.py g5-report-present-and-valid --pr NUMBER --head HEAD_SHA
```

A successful documentation-only no-op is not a passing publication check.
The latter command must fail for a boundary-related change at this stage.

## Failure response

- Stop the affected operation; preserve private diagnostic evidence and
  the exact candidate, input, and code revisions.
- For a data or scanner failure, correct the upstream input or code and
  rerun the approved private checks. Quarantine is not a reviewer override.
- For a suspected write outside the authorized boundary, follow the
  severity-1 response and correction-accounting doctrine in ADR 0010 and
  the decision log. This guide grants no emergency force-push authority.
- For suspected credential exposure, halt affected use and follow the
  private rotation procedure immediately. Never place key material in
  logs, screenshots, comments, issues, or this repository.
- Before resuming, reconcile what actually happened with the intended
  write set and retain evidence of the correction privately. Publish
  only approved name-free accounting through the eventual gated path.

## Key and installation hygiene

Key storage and rotation instructions belong in the private operator
documentation. Rotate on suspected exposure or relevant security events;
the existing 180-day maximum remains a calendar backstop, not permission
to wait after an incident.

After any authorized App configuration change, verify its installation
scope and permissions against the approved boundary design. Any expansion
needs separate approval before the configuration changes, not afterward.
This cleanup neither changes the App nor uses its credentials.

## Activation prerequisites

The following are prerequisites, not steps this document authorizes:

- A separately reviewed public-proof contract with exact candidate/head
  binding, trustworthy provenance, and replay/staleness handling.
- Working transport and public build behavior tested on real positive and
  negative PR cases without leaking private artifacts.
- Trusted CI producers, verified job behavior, and an explicitly approved
  required-check configuration.
- Resolution of the correction-export blocker and any remaining
  milestone acceptance criteria that apply to the proposed activation.
- Reviewed operator procedures and a demonstrated private failure,
  quarantine, correction, and recovery path.

Required-check activation and live publication require their own explicit
approval. See [the M1 checklist](m1-execution-checklist.md),
[current decisions](open-decisions.md), and
[the documentation cleanup clarification](adr/0016-documentation-context-and-current-rulings.md)
for scope and sequencing.
