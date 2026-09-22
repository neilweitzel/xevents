# ADR 0015: Privacy-preserving invariant verification

- Status: proposed (pending user redline)
- Date: 2026-09-22
- Deciders: project lead; safe first increment approved for implementation
- Clarifies: M1 WS9/WS10 verification placement and ADR 0014 check scope

## Context

The M1 checklist describes public CI fetching private state and inspecting
a full G5 report. The approved WS6 separation keeps private reports and
internal identifiers private. A branch-name-only G5 check also leaves a
gap: an operator could change boundary data on a differently named branch.

## Approved implementation scope

The operator approved this safe first increment on 2026-09-22. Public CI
must receive neither a private checkout nor a private-repository credential.
The three-declaration comparison and denylist validation run privately,
against an explicitly identified public revision. Public checks validate the
public declaration only; they must not claim to have inspected private state.

The public path check classifies a PR as boundary-related if either side of
any changed or renamed path touches the boundary, or its branch starts with
`boundary/`. A boundary-related PR may change only the existing three-path
write set. Documentation-only operator PRs take a scoped no-op path.

The public G5 gate applies to every boundary-related PR, regardless of
author or branch name. In this increment it returns a hard failure,
`public-proof-contract-not-implemented`. A pasted JSON claim, report link,
bot-like author string, or branch rename cannot turn that into success.
This is an intentional stop, not a working proof validator.

No change is made to the three authorized output paths. No private evidence
is newly authorized for public release. No App permission, credential,
override, review requirement, or private-read token is added.

## Remaining decisions and sequencing

A separately reviewed public-proof contract must specify minimal allowed
fields, verifiable provenance, exact candidate/head binding, replay and
staleness handling, and how the private scan version is bound without
publishing private state. This ADR does not design or authorize that proof.

WS9 first ships testable invariant implementations and offline runners.
WS10 must wire trusted CI producers, run real positive and negative PR tests,
and only then propose required-check activation. A unit-test pass does not
mean the gate is active on GitHub. Existing documentation findings are
reported rather than silently grandfathered or rewritten in accepted ADRs.

The Nygard check protects documents based on their base-revision status,
so deleting or downgrading a head status cannot avoid it. A supersession
notice does not authorize rewriting the historical body. Metadata/comments
and new ADRs remain independently testable.

## Consequences

Documentation and code development can continue without giving public jobs
access to private data. Boundary publication remains unavailable until the
proof contract, transport, required protections and public build are ready.
Full WS9, WS10, and live publication acceptance are not claimed by this
increment. There is no temporary success status for an unimplemented gate.

## Related

- [WS9 checklist](../m1-execution-checklist.md#ws9)
- [WS6 separation](../ws6-boundary-separation.md)
- [ADR 0012 boundary write set](0012-aggregation-boundary-transport.md)
- [ADR 0014 transport](0014-app-opened-pr-transport.md)
- [Machinery-first audit procedure](../machinery-first-audit-procedure.md)
