# Reading xevents research

xevents is for security practitioners and researchers studying observed
incident claims across sectors. Start with the
[research app](https://neilweitzel.github.io/xevents/); use this guide when you
need to interpret or reuse its output.

## What the first release measures

The counts-only research RC groups listing claims from a bounded recent
RansomLook source window by sector and first-retrieval week, with monthly
rollups of the same weeks. It uses exact
normalized actor/subject grouping, not fuzzy identity resolution. A repeated
observation of that grouped claim is not another independent source.

The initial collector wakes every two hours but enforces at least six hours
between successful source captures. Each capture requests up to 100 recent
records, about two to three days of source activity, so a delayed run does not
lose listings (see [ADR 0027](adr/0027-wider-recent-intake-window.md)).
That is a sampling policy, not a promise of complete historical or real-time
coverage. Execution delays and upstream failures can make coverage less complete.

## Read the table carefully

- **Week:** Monday-based UTC week of first retrieval, not a compromise date.
- **Month:** every week whose Monday falls in that calendar month. A week that
  crosses a month boundary counts once, in the month it began. Monthly counts
  sum the same claims as the weekly cells; they are not additional claims.
  A month is withheld if it has fewer than five claims or if publishing it
  would reveal a withheld week (see
  [ADR 0026](adr/0026-monthly-sector-rollup.md)).
- **Sector:** conservative description-based classification using the fixed
  public taxonomy. Uncertain classifications remain unclassified.
- **Count:** eligible grouped listing claims, not verified breaches or a count
  of independently confirmed organizations.
- **Withheld:** a cell has fewer than five eligible claims, including zero.
  The JSON value is `null`, not zero.
- **Freshness:** the displayed generation time reflects the latest successful
  capture represented in the dataset, not merely a later site rebuild.

Do not rank sectors by likelihood of compromise from these counts. Sector size,
source selection, classification error, missed records and withheld cells all
affect comparisons. A change in a published cell may reflect a correction or
changed eligibility, not just new activity.

## Empty, missing and stale data

A missing release file means no published dataset is available at that address.
A valid release with no cells means no aggregate cells are available under that
release's rules. Neither means no incidents happened. An invalid or unreachable
dataset is reported as unavailable, never replaced by demo values.

The app flags data older than two weeks as stale. This is a display warning,
not a service-level promise or a claim that newer data is comprehensive. The
synthetic demo is a separate, labeled interface preview.

## Activity without disclosing small private totals

The activity panel describes the whole published snapshot, independently of
table filters. “Claims assessed privately” counts distinct normalized
actor/subject groups across retained intake, including ineligible and
suppressed claims. Repeated sightings of the same group do not add another
claim. This is not independent incident verification or a count for a single
reporting week.

The counter is rounded down to a multiple of 25 and displayed as a band:
“Fewer than 25” (zero through 24), “25–49”, and so on. An older v1 snapshot
does not report this counter; the app says “Not reported,” never zero.
Unavailable or invalid snapshots show no activity numbers.

“Claims in published counts” sums numeric cells only; “Published sector-week
counts” counts those numeric cells. Monthly rollups are not added to the
published total; “Published sector-month counts” counts numeric monthly cells. A zero in either means nothing numeric is
displayed, not that a withheld cell contains zero claims. Do not subtract these
measures to infer withheld counts or compute a publication rate: one describes
all assessed groups, while the other describes publishable cells.

Activity bands reduce precision, not all disclosure risk. Threshold crossings
and outside information can still support inference. There are no exact small
private totals, source-specific activity bands, or per-gate exclusion counters.
See the [activity amendment](adr/0023-coarse-research-activity.md).

## Downloading and citing a snapshot

Use **Dataset & export** to inspect the selected aggregate JSON or **Download
JSON** to save it. Preserve its metadata, retrieval-week basis and `null`
values. Do not convert withheld cells to zero or describe the visible total as
the total number of breaches.

For a research citation, record the app URL, the dataset generation timestamp,
the selected weeks and sectors, and the date you downloaded it. Credit
[RansomLook](https://www.ransomlook.io/about) as the initial derived source and
xevents for the aggregation. The published coverage statement and manifest
accompany the full release; a filtered download is a selection, not an
independently signed release.

## Privacy and verification

Names, original descriptions, source URLs, screenshots and record-level
evidence do not belong in public outputs. The private pipeline retains evidence
and per-record eligibility decisions. The public manifest checks exported
aggregate bytes; it deliberately does not publish private record hashes.

Name removal and a minimum cell size reduce disclosure risk but are not a
universal anonymity guarantee. Correlation with outside information and changes
between releases can reveal additional information. Treat these as research
outputs, not a reason to identify affected parties.

The [RC release contract](adr/0022-unattended-research-rc.md) specifies the
automatic eligibility, name-leak scan, signed proof and deployment controls.
The [correction process](dispute-process.md) explains exceptional review.
Never include affected-party identities or sensitive evidence in a public issue.
