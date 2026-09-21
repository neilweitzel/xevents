# Source spec: RansomLook API (MVP ingest)

**Status:** draft, 2026-09-20. Endpoint and schema verified live
2026-09-20 (`/api/recent/3`, `/api/last/1`); re-verify at build time —
aggregator APIs change without notice.

## Access

- Base: `https://www.ransomlook.io/api` — **no key** for public endpoints
  (optional `RANSOMLOOK_API_KEY`; only `/api/export/{db}` requires auth).
- Docs: `https://www.ransomlook.io/doc/`.
- MVP endpoints:
  - `/api/recent/{n}` — latest n posts (verified: returns a JSON list).
  - `/api/last/{days}` — posts from the last N days (verified: 14 items for
    1 day on 2026-09-20).
  - `/api/posts/period/{start}/{end}` — bounded backfill window (documented;
    not yet exercised — verify before relying on it for backfill).
  - `/api/group/{name}`, `/api/search` — on-demand lookups (not polled).
- Licensing: all content (website, API responses, datasets) is **CC BY 4.0**
  (maintainers confirmed in writing, ransomlook issue #590). Attribution is
  required in xevents outputs — see the attribution registry (ADR 0002).

## Record schema (verified)

Each item is a JSON object with exactly these fields:

| field | type | notes |
|---|---|---|
| `post_title` | string | victim name as listed (verbatim → `observation.subject_raw`) |
| `group_name` | string | threat group string (verbatim; normalization is entity resolution's job, ADR 0005) |
| `discovered` | string | e.g. `2026-09-20 17:44:25.273479` — **UTC, no timezone marker** (source convention; treat as UTC, do not re-offset) → `observation.source_claimed_at` |
| `description` | string | free text; sector hints sometimes appear here (no dedicated sector/country fields) |
| `link` | string | relative path, e.g. `/entity/E759D68D977D4EE5` — the canonical post page |
| `magnet` | string | magnet URI or the string `"None"` |
| `screen` | string | relative path, e.g. `screenshots/audit team/AUDIT ENTITY: TEK SPB.png` — the source's own screenshot |
| `private` | string | `"True"` / `"False"` (string, not bool) |
| `misp_uuid` | string | UUID per post — **the idempotency key** (`observation.source_item_key`) |

## Poller rules (MVP)

1. **Idempotency:** key on `misp_uuid`. A re-poll that finds an already-
   recorded UUID updates `listing_state.last_seen_at` and creates nothing.
2. **Skip non-victim entries:** `group_name` of `audit team` (verified:
   2 of 14 items in the 2026-09-20 sample) are operational notices, not
   victim listings — filter them out, but log the skip in `poll_run`.
3. **Skip private entries:** `private == "True"` items are not ingested.
4. **Evidence capture per observation** (ADR 0003, API adaptation):
   - the raw API response body for the item (byte-faithful, content-hashed);
   - the source screenshot fetched from
     `https://www.ransomlook.io/<screen>` (CC BY 4.0 — archival is permitted);
   - fetch metadata (URL, timestamp, HTTP status, poller version).
   For API sources the raw response *is* what the source showed, so this
   satisfies the capture-at-ingest minimum without a synthetic screenshot.
5. **Backfill:** on first run, page `/api/posts/period/{start}/{end}` over
   the full available history (verify the endpoint first). Backfilled rows
   get `observed_at` = backfill time; `source_claimed_at` = `discovered`.
   The two clocks keep backfill provenance honest.
6. **Cadence (DECIDED open-decisions.md #5, 2026-09-20):** 2-hour trigger
   with a 6-hour effective-cadence guard (the 2-hour trigger follows
   RansomLook operator guidance; the guard holds the effective interval
   at 6 hours).
7. **Failure handling:** every run writes a `poll_run` row; partial failures
   (item-level parse faults) are counted in `items_errored` and logged, not
   fatal to the run.

## Known limitations (feeds the coverage-boundary statement)

- Single vantage: RansomLook sees only what its scrapers reach; DLS churn
  and Tor volatility mean silent gaps.
- No country/sector fields — sector appears only inside free-text
  `description`, if at all.
- `discovered` has no timezone marker; the UTC convention is the source's
  documentation, not a verified timestamp guarantee — record it as claimed.
- Audit-team and private entries are noise the poller must filter; any
  change to those conventions upstream must surface as a poller-version
  bump, not a silent behavior change.
- **No public full-index endpoint** (verified 2026-09-21 against the
  operator's documented API surface). Unaffected public endpoints are
  `recent`/`last`/`period` queries plus `group` and `search` lookups;
  `/api/export/{db}` requires an operator-issued API key and is not a
  runtime dependency. The de-listing rule (open-decisions.md #3/#11) is
  therefore implemented as the operational equivalent: three consecutive
  missed polls **plus** absence from a rolling `/recent` window **plus** a
  negative direct `/search` for the item — never a single missed poll.
