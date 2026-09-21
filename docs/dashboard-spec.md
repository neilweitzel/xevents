# xevents — Public dashboard specification

**Status:** draft, 2026-09-21. Implements open-decisions.md #7 (static
GitHub Pages surface), reshaped by #8 (sector-aggregated), further shaped
by ADR 0011 (two-view surface). The xfeeds precedent is the bar: easy to
read, easy to navigate, honest about what the data is. This spec describes
the surface; docs/mvp-scope.md item 7 defines its scope.

## Design principles

1. **Two views, one corpus, no cross-index.** View 1 (sector exposure)
   and view 2 (exploitation detail) are the same underlying observations
   rendered two ways. They do not cross-reference — a view 1 sector cell
   does not link to the CVEs from that specific cell, and a view 2
   technique entry does not link to the sector cells it appeared in
   unless the small-cell rule is comfortably cleared. See ADR 0011.
2. **Aggregates, not incidents, are the unit of every page.** The public
   never sees a victim record. Every number traces to aggregates with
   their confidence breakdowns.
3. **Every claim is framed, every page.** "Ransomware-listing claims
   aggregated by sector" — never "breaches by sector." The framing
   disclaimer (data-model.md, export root) appears on every page.
4. **Bands, not false precision.** Activity is shown as activity bands
   (`low` / `elevated` / `high`), computed against trailing baselines,
   versioned in the model registry. The computation is documented on the
   methodology page; the band is the output.
5. **Drill-down goes to sources and the manifest, not to victims.**
   Manifest hashes prove xevents retrieved what it claims; source links
   let a reader read the source themselves (source-side naming is the
   source's editorial choice, not ours).

## Pages

### View 1 — Sector exposure

Answers: how big of a target is my vertical, and what shape are the
attacks taking? CISO / board audience. Coarse `attack_class` vocabulary
(`docs/attack-class-vocabulary.md`); no CVEs, no vendor names, no
advisory links on this view.

#### 1a. Sector overview (site landing)

- Activity band per sector for the current week, with week-over-week
  movement: e.g. "Healthcare — **high**, 4 listings this week: 3
  ransomware, 1 phishing_compromise."
- A sector × week heat strip (trailing 12 weeks) for trend reading.
- Each sector links to its detail page.
- A prominent link to view 2 for the same reporting window — the only
  navigation between the two views. No per-cell links from view 1 into
  view 2.

#### 1b. Sector detail

- Listing counts by week (trailing 26 weeks), with the confidence-band
  breakdown stacked.
- **Attack-class breakdown** for the selected window (view 1 vocabulary
  only).
- **Victim-acknowledged overlay:** acknowledged / unacknowledged counts.
- Correction-ledger entries touching this sector's aggregates, newest
  first.
- No CVE detail, no vendor advisory links, no exploitation-vocabulary
  fields on this page.

### View 2 — Exploitation detail

Answers: what should my team fix or harden this week? Operational-
engineer audience. Specific vocabulary
(`docs/exploitation-vocabulary.md`); CVEs, advisory URLs, mitigation
references.

#### 2a. Technique overview

- CVEs and technique classes ranked by observation count in the current
  reporting window (weekly by default; 30-day rolling as a secondary
  view).
- Each entry displays: identifier or technique class, observation count,
  CISA KEV badge if applicable, vendor advisory link, mitigation
  reference link.
- No sector breakdown on this page. A reader wanting sector context
  navigates back to view 1 for the same window — they do not get a
  cross-indexed view.

#### 2b. Technique detail

- Rendered only for entries whose count comfortably exceeds the
  small-cell floor (dashboard-spec threshold documented on the page).
- Displays: technique or CVE, timeline across the trailing 26 weeks,
  linked advisories and mitigations, `misconfiguration_class` co-
  occurrences, `appliance_class` if relevant.
- **Sector distribution** appears here only when the total count is
  large enough that no sector cell would fall below the floor.

### Cross-cutting pages (serve both views)

#### 3. Methodology

- What xevents records (claims, not verified breaches), the two clocks,
  independence classes, the confidence bands with their criteria, the
  victim-acknowledged axis, the naming policy (both principles — stated
  plainly), the two-view design and the non-cross-index rule, the
  re-identification caveat (stated honestly), the coverage-boundary
  statement, attribution strings (CC BY 4.0).

#### 4. Correction ledger

- The append-only ledger, queryable by sector, technique, window, and
  event type. The credibility asset, not an afterthought (ADR 0004).

#### 5. Evidence manifest browser

- Manifest rows (hashes, source, retrieved-at) backing any aggregate,
  with the practitioner retrieval workflow documented inline (below).

#### 6. JSON export

- The aggregate export per the contract (data-model.md), with the
  framing root. Separate exports for view 1 aggregates and view 2
  aggregates; both downloadable as full snapshots.

## Publication cadence

Ingest cadence and publication cadence are decoupled
(open-decisions.md #12):

- **Ingest:** fast, per the source poller rules (decision #5: 2h trigger /
  6h guard) — speed serves de-listing detection, not readers.
- **Internal aggregation:** daily. Produces the sector × day rollups that
  feed the review queue and the weekly public build. Internal rollups are
  stale if older than 2 days (ADR 0010 §4).
- **Public publication:** weekly. The public build runs on a fixed weekly
  schedule and publishes sector × week aggregates, the 12-week heat strip,
  and the JSON export.
- **"Insufficient data" is per-cell.** A sector × week cell below the
  small-cell threshold (open-decisions.md #13: k=5 minimum claims,
  tunable) renders as "insufficient data"; its claims remain counted in
  the monthly rollup, sector totals, and all-sector aggregates. The
  surface as a whole always publishes — there is no global data gate that
  would make the site flicker between alive and dead. Thin data stays
  internal until there is enough to publish.
- **Review never blocks the schedule.** A weekly publish includes only
  reviewed observations. Unreviewed observations are excluded from the
  aggregates but counted in a visible "N observations pending review"
  line on the sector overview page.
- **Launch:** the public surface stays dark until burn-in completes
  (first 500 observations reviewed, ADR 0010 §5).

## Practitioner evidence-retrieval workflow

Documented on the manifest page and in the methodology:

1. Find the aggregate; note its `manifest_refs[]`.
2. Look up the manifest rows: `payload_sha256`, `source_name`,
   `retrieved_at`.
3. Fetch the source record yourself (source link, or a web archive for
   dead sources) and hash the payload bytes with SHA-256.
4. Compare. A match proves xevents retrieved what it claims it
   retrieved. A mismatch is a severity-2 incident (ADR 0010 §3) — report
   it via the dispute channel.

## Practitioner jobs (the honest MVP set)

The surface serves five jobs, and disclaims the rest:

1. **Sector exposure orientation (view 1)** — which verticals are being
   hit, how, over time.
2. **Exploitation awareness (view 2)** — what CVEs and technique classes
   are showing up across the corpus, and where to patch or harden.
3. **Sector trend research (view 1)** — attack-class shifts over time,
   by sector.
4. **Disclosure-lag research** — compromise-to-disclosure where both
   endpoints are evidenced (ADR 0006 §6: labeled unknown, never imputed).
5. **Offline dataset analysis** — the JSON export for independent work.

Explicit non-jobs: victim lookup ("are we listed?"), victim notification,
alerting, attribution verdicts, breach verification, cross-indexing view
1 sectors to view 2 techniques (the non-cross-index rule of ADR 0011).
The methodology page says this outright.

## Growth strategy (client-side limits)

The corpus is append-only; a monolithic export eventually exceeds
practical browser limits. The design, specified now:

- **Time-sharded aggregates:** `data/aggregates/<year>/<week>.jsonl` —
  the site loads the current window eagerly, older windows on demand.
- **Build-time search index:** a compact per-shard index (sector, vector,
  malware class, band) generated at build; no runtime search service.
- **Lazy claim detail:** sector detail pages fetch their window shards
  on navigation, not on landing.
- **Re-evaluation thresholds:** 10,000 claims/week sustained or a 50 MB
  full export — at either, the sharding granularity and index strategy
  are revisited in a new ADR. Specified now so growth is a planned
  event, not a surprise.

## Indexing policy

Aggregate and methodology pages are indexable (the research surface is
meant to be found). There are no victim or incident detail pages, so the
claim-page `noindex` question from the 2026-09-20 review dissolves — it
is recorded here as resolved-by-pivot. Manifest pages are indexable
(hashes are not sensitive); the dispute inbox and any non-public
operational pages are not.

## Operations appendix — runbook design

Written now; operative when execution is authorized. Failure modes,
detection, and response:

| failure | detection | response |
|---|---|---|
| Failed public build | Pages build status; G6/G7 gate failures in CI | No deploy; previous site stays live; diagnose from run manifest |
| Stale output (aggregates older than 2× cadence) | freshness SLO check (ADR 0010 §4) | review task (severity-3); investigate poller before republishing |
| Integrity mismatch (manifest hash ≠ recomputed) | publish-time verification | quarantine batch; roll back public repo to last good commit; severity-2 incident |
| Partial publish (aggregates without manifest rows, or vice versa) | G7 manifest gate | same as integrity mismatch |
| Name-scan gate trip | G5 failure | quarantine batch; severity-1 investigation (treat as potential naming-policy breach until proven otherwise) |
| Upstream convention change | schema-fingerprint check (ADR 0010 §4) | quarantine source; human sign-off + poller-version bump before resume |

**Rollback:** the public repo rolls back to the last good commit; the
rollback is announced on the site status line and recorded as an
`administrative_note`. Roll-forward only after the root cause is
understood — never re-push a quarantined batch unchanged.
