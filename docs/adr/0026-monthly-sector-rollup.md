# ADR 0026: Monthly sector rollups with complementary suppression

Status: accepted

Date: 2026-09-25

Approval: operator requested a monthly rollup on 2026-09-25 ("Let's do #1 and
#2 now") and approved it by merging this ADR with its coordinated reader.

## Context

The published view has one sector-week matrix with a cell floor of five. At
current intake, most sector-week cells stay below five and are withheld, so the
public site shows little beyond the largest sectors for the foreseeable
future. The same claims summed over a month would clear the floor in many more
sectors. Publishing both views naively would let a reader subtract published
weekly cells from a monthly total and recover a withheld weekly count.

## Decision

Extend the aggregate to `xevents-view1-display/v4`. The header is unchanged
from v3 apart from the schema version. After the complete weekly matrix, v4
adds a complete sector-month matrix of closed rows with exactly `sector`,
`month` (`YYYY-MM`) and `claim_count`.

- **Nesting, not calendar splitting.** A month contains exactly the retrieval
  weeks whose Monday falls in that UTC calendar month. A week that crosses a
  month boundary counts once, in the month it began. Monthly values are sums
  of the same eligible claims as the weekly cells, never additional claims.
- **Coverage.** Months are the distinct months of the published weeks, every
  vocabulary sector appears for every month, and there are at most 25 months.
  Absent cells cannot silently become zeros.
- **Floor.** A monthly cell below five, including zero, is `null`.
- **Complementary suppression.** For each sector-month let `S` be the sum of
  the published weekly cells in it and `k` the number of withheld weekly cells.
  If `k = 0` the monthly value is published and equals `S`. If `k > 0` the
  monthly value is published only when its total is at least five **and** the
  withheld remainder (total minus `S`) is at least five; otherwise it is
  `null`. Every quantity derivable from the pair of views is therefore either
  an exact value of at least five or the range zero to four, the same
  information a withheld cell already gives.

The private producer applies the rule. The public reader independently
refuses any v4 file that violates it, that has missing, duplicate or extra
months, or whose monthly sum exceeds the assessment band's upper bound. It
reads v1 to v3 unchanged, and refuses month rows in earlier schema versions.

The app defaults to the monthly view when a snapshot provides it, keeps the
weekly view one selection away, and adds a "Published sector-month counts"
activity metric. "Claims in published counts" keeps summing weekly cells only,
so monthly rollups are never counted twice. Exports record `period: "month"`
when monthly rows are selected.

## Unchanged controls and rollout

The weekly matrix, the floor of five, eligibility rules, the assessment band,
`evaluated_at`, the three-file write set, immutable evidence, exact-byte G5
scan, private signed proof, protected merge and verified Pages deployment all
remain unchanged and mandatory. No new source, credential, permission, manual
gate, public name or record-level identifier is introduced.

Land the reader, which keeps v1 to v3 support, before activating the v4
producer. Update the private reviewed-code seal. The next admitted data
release deploys both. Reader-only rollback requires retaining v4 support or
first reverting the producer to v3.

## Limitations

Complementary suppression covers inference between the weekly and monthly
views within one snapshot. It does not stop inference across successive
releases: a cell that changes between two snapshots still reveals how many
eligible claims arrived in between, as the weekly view already does (ADR
0023). A withheld month next to published weeks shows only that its withheld
weeks hold zero to four claims in total. Rollups make more sectors visible;
they do not make counts complete, representative or a risk ranking.
