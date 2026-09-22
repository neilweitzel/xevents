# Machinery-first audit procedure

Status: proposed (pending user redline).

Authority: [M1 WS9](m1-execution-checklist.md#ws9) and the machinery-first
ruling in [open decisions](open-decisions.md#18-approval-doctrine--machinery-first-under-solo-operation).
This is a soft PR reminder, not an extra human approval gate.

## For every proposed control

Describe the failure it prevents, its input, its automated test, and its
fail-closed outcome. A new gate, review or human step must either be
automatable in CI or have an explicit open-decisions entry marked
`machinery-first-inappropriate` explaining why automation is inappropriate.
Do not add an override or silently substitute manual review for a hard gate.

Keep public checks public-only. Private comparisons execute privately; do
not copy private evidence into public logs, artifacts, PR bodies or comments.
Check both old and new names for renames, and bind checks to the exact PR head.

## What a green result proves

A unit-test result proves the tested implementation behavior, not a live
required-check configuration. Activation needs positive and negative PR
evidence, exact producer identity, no bypass, and up-to-date branch protection.
Changes to workflows, checker code or dependencies need a trusted-base
execution design so a PR cannot replace its own checker with a success stub.

The first WS9 increment contains no workflows and changes no protection.
Its `g5-report-present-and-valid` implementation intentionally rejects all
boundary-related PRs until a public-proof contract exists. Never replace
that refusal with a placeholder green check.

## Offline check entrypoints

Use Python 3.14.3, without new third-party dependencies:

```sh
python -B -m unittest discover -s tests/invariants -p 'test_*.py'
python -B tests/invariants/run_checks.py boundary-write-set
python -B tests/invariants/run_checks.py docs-qa
python -B tests/invariants/run_checks.py jsonl-headers
python -B tests/invariants/run_checks.py nygard-immutability --base BASE_SHA --head HEAD_SHA
python -B tests/invariants/run_checks.py boundary-write-set-in-diff --pr PR_NUMBER --head HEAD_SHA
python -B tests/invariants/run_checks.py g5-report-present-and-valid --pr PR_NUMBER --head HEAD_SHA
```

PR checks read only the public GitHub API, require an exact expected head,
paginate and reconcile the entire changed-file count, and reject a moving
head/base or incomplete result. They use the ADR from the base revision, not
a widened declaration in the proposed change. The runner emits fixed error
codes rather than PR body contents or raw API errors.

The documentation audit reports unresolved references and possible
decision-language drift with locations. Future file references can appear
as unresolved findings; they need explicit disposition before CI enforcement.
There is no baseline allowlist or automatic accepted-document rewrite.
Reference extraction currently covers ADR numbers, backticked repository
paths under the documented source directories, and local Markdown links.
It is not a complete Markdown parser: arbitrary bare prose paths, link
anchors, reference-style links and semantic glossary misuse remain outside
this first increment. Full AC1.15 acceptance is not claimed.
Glossary checks require real definitions and unique canonical terms, audit
their references, and report term usage counts; they do not infer semantic
correctness of arbitrary prose.

The Nygard checker allows HTML comment changes and narrowly recognized
top-of-document metadata, while preserving the historical body. Changing
an accepted status requires a valid supersession reference to an accepted
replacement ADR. It also protects partially/fully superseded history.
