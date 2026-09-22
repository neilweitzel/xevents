# ADR 0016: Documentation context and current-ruling clarification

- Status: proposed (pending user redline)
- Date: 2026-09-22
- Deciders: project lead
- Clarifies: ADRs 0002, 0004, 0007, and the WS9 documentation diagnostics

## Context and authorization

The operator reviewed the documentation findings and authorized preparation
of focused cleanup PRs on 2026-09-22. This authorizes an implementation for
review, not a merge, required-check activation, or a new publication policy.
The source of truth remains the existing user rulings in
[the decision log](../open-decisions.md).

Five current-language findings refer to three already-recorded rulings.
Other diagnostics conflate unrelated Markdown rows, explicit token examples,
child-document status, and preserved historical text with active uncertainty.
Reference-existence findings additionally need an ownership and milestone
contract before any of them can safely be downgraded.

The research basis is the existing licensing, correction-history, and
de-listing ADRs, not new source ingestion or new external research. This
increment implements the documentation-quality intent in ADR 0010 and the
privacy-preserving placement of checks in ADR 0015.

## Current rulings, not new decisions

| Historical location | Operative authority | Current interpretation |
|---|---|---|
| ADR 0002, Decision item 2 | Decision #2 | No contact with ransomware.live by default, including manual queries. Any minimal, documented, single-fact manual lookup requires separate explicit approval. Bulk derivation, bulk queries, republication, and dependency use remain excluded. |
| ADR 0004, Decision item 5 | Decision #4 | Acknowledge within two business days, or one for wrongful-listing claims; initial assessment within ten business days. The manual dispute process ships from day one. |
| ADR 0007, Consequences | Decision #5 | A two-hour trigger and a six-hour effective-cadence guard are complementary controls, not alternative intervals. |

The accepted ADR bodies are preserved byte-for-byte. This document makes the
existing rulings easy to find but does not relabel, rewrite, or silently
supersede those bodies. Their historical diagnostics remain visible in the
strict checker until a separately approved disposition contract exists.
The operating manual and draft source specification can state these existing
rulings directly without reopening them.

## Implemented parser corrections

- Read list items, nested list items, and table rows separately. Wrapped
  text remains attached to its unit so a wrapped authority reference is
  not lost. Unrelated items no longer borrow each other's authority.
- Recognize the plain and bold preamble status spellings used in this
  repository. Remove only a known status value; additional policy claims
  on that line, unknown values, and body-section status claims remain checked.
- Recognize narrowly scoped detector descriptions such as detecting quoted
  tokens. Merely quoting a policy statement is not a waiver.
- Treat struck text as historical only when an explicit uppercase, bold
  supersession, deferral, or lifting marker immediately follows the
  strikeout. The marker can include a date. Unrelated or negated markers
  do not qualify; current text in the same unit is still checked.
- Distinguish the exact past-tense description of a formerly open question
  from present-tense uncertainty. A new unresolved clause still fails.
- Keep reference existence independent of language interpretation. A
  historical or quoted reference to a nonexistent ADR or local document
  still produces a finding.

These are deterministic diagnostics with a bounded Markdown reader, not a
CommonMark implementation or semantic proof of policy consistency. Indirect
authority inherited from remote headings and cross-paragraph reasoning still
need review. No regex can replace the recorded decision and its context.

The checker adds no file-specific exception list, private checkout, network
lookup, external dependency, or permanent debt suppression. Existing missing
reference findings still make the command exit nonzero.

## Reference ownership contract for later approval

The following is a proposal, not implemented pass behavior:

| Reference class | Required evidence before any status change |
|---|---|
| Required local | Target exists in the audited snapshot; missing targets block. |
| External public | Explicit repository or URL ownership; verification provenance and offline/network behavior must be specified. A local miss is not remote verification. |
| Private-owned | Public output says not checked here, never verified. Private checks validate exact targets against the private snapshot and a pinned public revision. |
| Planned | Declared owner, milestone, and machine-readable completion state. Absence remains visible; claiming the milestone complete without delivery blocks. |
| Example or template | Explicit example intent or a bounded variable contract, concrete backing data, and path-safety validation. Unknown expressions do not receive a blanket exemption. |
| Preserved decision history | Exact linkage to a current ruling without editing the historical body or hiding new drift. |

Approval must settle the schema, trustworthy source of milestone completion,
owner designation, behavior on ambiguous context, and stale-disposition
detection before changing the CLI's failure semantics. No automatic
classification from a nearby word such as private or future is sufficient.

## Execution clarification and sequencing

The WS10 corpus-completeness command must resolve to an implemented private
test entrypoint. The private companion change records and exercises that
mapping without changing the public checklist or its pinned corpus contract.
This is not a claim that corpus completeness proves production G5 outcomes.

The public-safe [boundary operations guide](../boundary-operations.md)
fulfills the existing runbook reference. It describes current controls and
activation prerequisites without publishing private implementation details.
It does not authorize live transport.

Review the public cleanup first. The dependent private cleanup must use an
explicit public code revision and keep all private diagnostics private.
Public CI still receives no private checkout or credential.

## Non-goals

No workflow is added or dispatched. No GitHub App permission, key, token,
ruleset, required status, or publication behavior changes. No accepted ADR,
accepted implementation plan, corpus fingerprint, G5 input, fixture, or
correction ledger is rewritten. No proof contract, correction-export
contract, or future ingestion/aggregation milestone is implemented.

The public G5 gate remains fail-closed for every boundary-related PR. This
cleanup does not complete WS9, WS10, or live publication acceptance.
