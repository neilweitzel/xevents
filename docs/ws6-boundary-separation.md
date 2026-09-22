# WS6 boundary workflow separation

Status: proposed (pending user redline).

Authority: M1 WS6, ADR 0012's retained private-workflow isolation rule,
ADR 0013, and ADR 0014. The operator approved preparing this clarification
on 2026-09-22; merging and live execution require separate approval.

## Clarification

The M1 checklist's “public checkout only” restriction applies to the
public site build, not to the private scanning job. The private boundary
workflow needs read-only access to its scanner and inputs. This does not
give the public build access to private data.

The boundary workflow must not use the native workflow token for repository
writes. A separate private archival workflow may use a private-scoped native
token, under ADR 0012's private-workflow isolation rule. It must not receive
the App key, write to the public repository, execute downloaded artifacts,
or accept evidence from pull requests or untrusted branches.

Archival must bind evidence to the exact originating workflow, repository,
commit, run, and attempt. Reports are immutable; retries are idempotent only
for identical bytes. The private log and correction ledger remain append-only.
Incomplete evidence or unsuccessful archival is an error, never a publish pass.

## Implementation sequence and remaining gates

The initial WS6 increment may run the synthetic scan, write-set preflight,
and private evidence archival with no App credential access or publisher.
An operational receipt is not a WS8 machinery-invariants attestation.
Missing WS8 reporting is recorded explicitly, not represented as a successful
report. This increment does not complete WS6 or any live publication criterion.

The remaining WS6 increment must add and test App-authenticated transport
only after the WS7 protection, WS8 reporting, and WS9 required-check contracts
exist. It must verify those dependencies before accessing the App key.
Required checks and the public build must be implemented and verified before
live publishing. There is no enable flag or manual override.

The existing three-path public write set is unchanged. No private report,
internal identifier, or correction-ledger corpus becomes public through this
clarification. The unresolved correction-export contract stays blocked.

## Implementation surfaces

This clarification authorizes private integration helpers under `scripts/`,
a separate `.github/workflows/archive-boundary.yml`, per-attempt operational
receipts under `ingest-logs/boundary-attempts/`, immutable G5 reports in the
existing report directory, and per-attempt correction JSONL records in the
existing correction ledger. The established boundary-check log remains the
append-only per-attempt index. These private surfaces do not expand the public
write set.

Accepted ADR bodies and the accepted checklist remain unchanged. This document
is an explicit clarification alongside them, not a silent rewrite.
