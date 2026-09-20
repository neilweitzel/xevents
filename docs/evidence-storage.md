# xevents — Evidence storage strategy

**Status:** draft, 2026-09-20. Implements ADR 0009 (static-first). The
logical requirements are ADR 0003's; this document is the physical plan.

## Layout

- **In-repo, content-addressed:** `evidence/<sha256>` — raw bytes of each
  artifact (screenshot PNG, raw API JSON, fetch metadata). The path *is*
  the hash; `observation` rows record the hash, so any consumer can verify
  bytes against the record. No file extensions, no metadata in filenames.
- **Excluded from the Pages artifact.** The deploy workflow uploads only
  `site/`. Evidence is retrievable from the git repo (and its hashes are on
  every observation), but it is not served to site visitors as static
  files — the site links artifact hashes, not bytes.
- **Redaction before commit.** The redaction step (ADR 0003) runs inside the
  scheduled pipeline, before bytes are written. The redaction note travels
  with the observation row.

## Volume plan

Steady-state ingest is small: ~14 RansomLook items/day, one screenshot each
(~100–500 KB) → single-digit MB/day, ~1–2 GB/year. GitHub's soft guidance
is ~5 GB per repo; the Pages site cap (1 GB) never sees this directory.

The risk is **backfill**: the full RansomLook history is thousands of items,
and fetching every historical screenshot would add gigabytes in one commit
and hammer the upstream. Rules:

1. Backfill captures metadata + raw JSON for all items; screenshots are
   fetched for new items going forward only. (A `--backfill-screenshots`
   flag exists for a deliberate, rate-limited historical fetch — default
   off.)
2. **Split trigger:** if `evidence/` approaches 2 GB, new evidence goes to
   a dedicated `xevents-evidence` public repo; existing bytes stay where
   they are (history is not rewritten). The observation rows' hashes are
   repo-independent, so the split is transparent to consumers.
3. The scheduled pipeline logs `evidence/` size in every run manifest; the
   split trigger is checked, not eyeballed.

## Retention mapping

The retention policy (docs/retention-policy.md) tiers map to storage as
follows under the static-first architecture:

| tier | physical form |
|---|---|
| hot | `evidence/` on `main` |
| warm/cold | `evidence/` on `main` until the split trigger; then `xevents-evidence` |
| ledger | `data/*.jsonl` on `main`, forever (hashes included) |

The cold-review gate (no auto-delete) is unchanged: deletion removes bytes
only, hashes and ledger rows remain, and the deletion is recorded.

## What this does not do

- No Git LFS (breaks the "any clone is a complete checkable state"
  property and complicates the Actions pipeline).
- No external object store in the MVP (no credentials to manage, no bill).
  If evidence ever outgrows the two-repo plan, that is a new ADR.
