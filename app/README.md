# xevents research application

Research reader plus a separate synthetic demonstration. The reader defaults
to a same-origin released aggregate file, with explicit waiting and failure
states. The synthetic interface remains available only at `?demo=1`.
The browser is not a publication gate. Server-side release controls must
authorize the data before it is deployed.

## Run

Serve this directory with any static HTTP server; open `index.html`.
Node 20.20.1 was used for the dependency-free model tests:

```sh
node --test app/tests/model.test.mjs app/tests/aggregate.test.mjs
```

Optional browser and accessibility regressions (development tooling only;
serve this directory locally on port 3000 first):

```sh
npm --prefix app ci --ignore-scripts
npm --prefix app exec -- playwright install chromium
npm --prefix app run test:browser
npm --prefix app run test:accessibility
npm --prefix app run test:research
```

There is no application build step, server component, package installation,
credential, browser storage, telemetry or external network dependency required
to run the app. The optional development tests use the pinned lockfile. Hash
routes work on ordinary static hosting. Filter and theme state is transient.
The verified Pages workflow packages only reviewed app assets and admitted
public release files. Its activation is separate from installing the code;
see [the RC contract](../docs/adr/0022-unattended-research-rc.md).

## Data boundary

- Demo fixture counts are invented, labeled synthetic in the UI and downloads.
- The fixture is authored aggregate data, not derived from any private input.
- Six sectors, twelve weeks; cells are integers >= 5 or `null`. No hidden
  subthreshold counts are bundled. Partial totals count visible cells only.
- Illustrative activity thresholds are not production scoring policy.
- The demo schema `xevents-synthetic-preview/v1` is distinct from the
  counts-only research reader contracts `xevents-view1-display/v1`, `/v2`
  and `/v3`.
  V2 adds only a bounded global `assessed_claims_floor`, displayed in bands of
  25. V1 remains readable with its assessment metric explicitly not reported.
  The activity panel uses the whole snapshot, not selected table rows.
  V3 adds only the whole-second `evaluated_at`, shown as "Accurate as of"
  (ADR 0024). It is never earlier than the capture.
- The research reader requests `data/aggregates/view1.jsonl` once at startup
  with no credentials, no cache and no redirects. Waiting/error states offer
  a manual retry. It never requests a private repository or a source API.
- Missing file: no published dataset yet. Failed/invalid/oversized file:
  unavailable. Empty released file: no released cells. Never demo fallback.
- Reader data has a closed canonical JSONL schema, fixed sector vocabulary,
  complete sector/week matrix and null or integer counts >= 5. Data older than
  two weeks is marked stale. Attribution and uncertainty survive JSON export.
- `release_state: released` is a format marker, not cryptographic authority.
  Publication must be authorized by the separate boundary before hosting.
- No source records, actor/victim names, evidence receipts or private reads.
- This preview does not implement production G5 enforcement or change its limits.

The active RC release path enforces the separate signed-publication
prerequisites. The reader itself does not supply these. Never replace
this fixture with raw source data or interpret a successful UI test as release
authorization. The second exploitation view, correction ledger and evidence
manifest browser are outside this first runnable slice.

## Assets

The only vendored third-party assets are IBM Plex Sans Latin normal 400/500/600
WOFF2 fonts from `@fontsource/ibm-plex-sans@5.3.0`, licensed OFL-1.1.
License text is retained in `fonts/LICENSE`; fonts load locally.
Package source: https://registry.npmjs.org/@fontsource/ibm-plex-sans/-/ibm-plex-sans-5.3.0.tgz
Package integrity:
`sha512-CbE4CbbEEZJX860XyUiRpsksXIQR8Rp2XDva2VO53NJox9tVNtusrysd2x5YkUEY3ErQ66W1IiiQL8/wihhw5w==`

Development only: Playwright 1.59.0 (Apache-2.0) and axe-core 4.13.0
(MPL-2.0), pinned with integrity hashes in `package-lock.json`. Neither is
served with the app. Chromium is downloaded separately by Playwright for tests.

## QA inventory

Research mode additionally covers: missing/empty/blocked/corrupt/oversized
and unreachable data; retry; no automatic demo import; strict dates and
duplicate-key rejection; rectangular matrix; filters, sorting, downloads and
sector routes; all-withheld cells and stale releases. Browser network fixtures
are entirely invented and are never saved as public release files.

- Overview metrics, chart values and rows reconcile to model calculations.
- Search by name/code; empty result and reset; count/name sorting.
- Selected reporting week and 1/4/12-week windows, including truncated history.
- Sector navigation and return; invalid route recovery; browser back.
- Methodology and dataset navigation; preserved filter state.
- JSON download content matches current selection, including null cells.
- Light/dark theme cycle; keyboard focus and skip link; reduced motion.
- Desktop, 375px and 320px layouts, all pages, long sector labels and table scroll.
- No external data requests, uncaught browser errors or document-level overflow.
- Required module-load failure and successful reload recovery.
- Automated WCAG 2 A/AA and 2.1 AA checks across pages, themes and viewports.

Tests and browser checks do not establish production privacy or source accuracy.

## Verification

On 2026-09-23, initial delivery: 12 model tests passed; Chromium interactions and actual downloaded
JSON were checked, with no uncaught browser errors or external requests.
Overview, sector detail, methodology and dataset views were visually reviewed
at 1440px and 375px, plus dark-mode overview. Existing repository suites passed:
129 invariant/protection tests and 238 offline proof tests, with 100% statement
and branch coverage for the proof core. This is local validation, not hosted CI
or a production release approval.

Follow-up audit on 2026-09-23: 13 model tests passed, including 2,304 exhaustive
sector-subset/reporting-week/lookback combinations. Browser regression passed
at 1440px, 375px and 320px, including injected module failure and reload recovery.
All 24 automated accessibility scans (four views, two themes, three widths)
returned no WCAG 2 A/AA or 2.1 AA violations. Automated scans are not an
accessibility certification. Fixed navigation-number contrast, misleading
sort indicators and missing startup-error recovery; pinned optional QA tooling.
