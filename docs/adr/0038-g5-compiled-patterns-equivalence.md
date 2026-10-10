# ADR 0038: Compile G5 match patterns once per scan, proven equivalent

Status: accepted

Date: 2026-10-10

Approval: operator reviewed this ADR and approved its implementation on
2026-10-10, and approved it by merging this ADR.

## Context

The G5 exact-output scan compares every text value in the outbound release
files with every name derived from the retained source window. Its cost grows
with retained weeks multiplied by retained names. The Stage A capacity
benchmark measured the scan on a calibrated synthetic load and projected it to
exceed the private collect job's 15-minute limit in December 2026, before the
first retention freeze.

Profiling a real preparation on the pinned private store showed that most of
the scan time is not matching. Of 162 profiled seconds, about 136 were spent
compiling regular expressions. The boundary and slug patterns are built from a
name and passed to the standard library as strings; its pattern cache holds
512 entries, and a scan uses thousands of distinct names, so the same pattern
is recompiled for every text value it is applied to.

Compiling each name's pattern once per scan, in an offline test on the pinned
real store, reduced preparation from 43.2 to 4.1 seconds and produced a
byte-identical release receipt, including the complete G5 report.

## Decision

- G5 compiles each derived name's boundary pattern and slug pattern once per
  scan and reuses the compiled pattern for every text value in that scan. The
  pattern text, flags, match rules, normalization, ordering of entries, match
  positions, match limits and fail-closed behavior are unchanged.
- The compiled-pattern store lives only for one scan. It is never persisted,
  shared between scans or seeded from earlier data.
- No allowlist, sampling, early exit on a first match, skipped value, skipped
  row or skipped rule is introduced. A larger input still fails on the existing
  value-count and match-count limits, not on a new budget.
- This is a performance change with no change to what G5 accepts or refuses.
  It must be proven, not assumed.

## Equivalence proof required before merge

A differential test runs the current implementation and the new one on the
same inputs and requires identical match reports, byte for byte after removing
the scan timestamp:

- the pinned real private store's release preparation, run offline before
  merge with the result recorded in the private pull request, because private
  CI deliberately has no access to source data;
- the existing G5 fixtures and adversarial corpus;
- generated cases that stress the change: more than 512 distinct names; the
  same name in many values; names containing regular-expression metacharacters,
  Unicode, confusables, digits and separators; names that are prefixes of other
  names; multi-token slugs; percent-encoded URL text; empty and single-character
  names; and inputs that reach the match-count limit;
- a refusing case for every existing refusal code, confirming the same code.

The old implementation is kept verbatim as the reference for as long as the
differential test exists, in its own private suite (`tests/g5_equivalence`) so
the documentation evidence that pins the existing G5 test set is unchanged.
Both suites run in the existing pinned private CI.

## Consequences

The scan stays exactly as strict and becomes roughly ten times faster at
current size, removing the projected December collect-job timeout without
changing workflow limits. Its cost still grows with weeks multiplied by names,
so stage timing and budgets (ADR 0039) continue to watch it. The implementation
seal and the private CI pin change with this code and are updated together.
