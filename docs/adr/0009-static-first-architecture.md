# ADR 0009: Static-first architecture — GitHub Actions + Pages, git as the system of record

- Status: proposed (pending user redline)
- Date: 2026-09-20
- Deciders: project lead
- Supersedes: ADR 0008 (PostgreSQL as the system of record)

## Context

The project goal is to run like xfeeds: fully automated on a public static
site served by GitHub Pages. GitHub Pages is static hosting — there is no
server to run PostgreSQL on. ADR 0008 named the right *logical* model but
the wrong *physical* one. This ADR replaces the physical layer while keeping
every logical guarantee (immutability, append-only ledger, two clocks,
content-addressed evidence).

The xfeeds precedent (verified 2026-09-20 against neilweitzel/xfeeds):
scheduled `update-feeds` workflow (cron + internal guard), full-history
checkout, commits results to `main` via `GITHUB_TOKEN`, deploys Pages itself
(token pushes don't trigger other workflows; `pages.yml` is a
`workflow_run` safety net), human review via auto-opened GitHub issues with
checklists, keepalive workflow against GitHub's 60-day scheduled-workflow
disable.

## Decision

1. **Git is the system of record.** Observations, correction events,
   confidence assessments, poll-run manifests, and listing state are stored
   as append-only JSONL files under `data/` and committed to `main` by the
   pipeline. Every pipeline run is a commit; the commit history *is* the
   audit trail — content-addressed, immutable, publicly inspectable.
2. **No database server in the MVP.** The logical schema (docs/data-model.md)
   is unchanged; its physical mapping is JSONL/JSON with ISO-8601 UTC
   timestamps (see "Physical mapping" in data-model.md). A SQLite file may
   be built at pipeline time as a convenience artifact; it is derived, never
   authoritative.
3. **The pipeline runs on GitHub Actions cron**, mirroring xfeeds'
   mechanics: scheduled refresh workflow with an internal cadence guard
   (cron fires more often than the effective poll interval — GitHub's
   scheduler drops slots), `cancel-in-progress` concurrency, full-history
   checkout with rebase-retry on push, self-deploying Pages, keepalive
   workflow.
4. **The operational surface is a static site on GitHub Pages**, generated
   by the pipeline from `data/` into `site/` and deployed as a Pages
   artifact. The JSON export contract (data-model.md) is the published data
   format — the site is rendered from it, not beside it.
5. **Human review lives in GitHub Issues.** The `review_task` table becomes
   issues opened by the pipeline with review checklists (xfeeds
   `source-review.yml` precedent); resolutions are recorded as issue
   comments/closures and mirrored back into `data/` by the reviewer run.
6. **`poll_run` becomes Actions run logs + a committed run-manifest row**
   (`data/poll_runs.jsonl`). Same information, no table.

## Rationale

1. **Zero infrastructure.** Public repo → unlimited free Actions minutes,
   free Pages, CDN-backed distribution. No servers to operate, patch, or
   pay for — the xfeeds proof is running.
2. **The doctrine fits git better than a database.** Immutable observations
   and an append-only correction ledger are what git *is*. A database would
   need extra machinery to prove history wasn't rewritten; git proves it by
   construction and shows it to the public.
3. **Reproducibility.** Any commit is a complete, checkable state of the
   world: data + code + workflow definition that produced it. `git bisect`
   works on the pipeline's outputs.
4. **No secrets.** The MVP source (RansomLook) is keyless, so the scheduled
   pipeline needs no credential management.

## Consequences

- ADR 0008 is superseded (marked, not deleted — the rationale for rejecting
  Postgres stays in the record).
- Evidence bytes need a volume strategy: see docs/evidence-storage.md.
  Large binary evidence does not belong in the Pages deploy artifact.
- The Tor crawler (long-term primary, ADR 0002) cannot run on Actions (no
  Tor egress, ephemeral runners). It is scoped as an *external* component
  that publishes into the repo; the Actions pipeline never depends on it.
- Scheduler best-effort behavior (dropped slots) is handled the xfeeds way:
  cron fires every 2h, an internal guard holds effective polls to the
  decided cadence (open-decisions.md #5; default 6h until ruled).
- The pre-public-surface gate (ADR 0003: written lawful-basis /
  public-interest research memo) is now a launch blocker, tracked in
  mvp-scope.md item 7. No memo, no public data on Pages.
- Code quality bar mirrors xfeeds: pytest, Ruff (line-length 100), mypy
  strict, uv — enforced in CI on every PR (AGENTS.md).

## Research basis

- neilweitzel/xfeeds: `.github/workflows/update-feeds.yml` (cron+guard,
  self-deploy, rebase-retry), `pages.yml` (workflow_run safety net),
  `source-review.yml` (issues as review prompts), `keepalive.yml` (14-day
  quiet threshold vs GitHub's 60-day disable), `pyproject.toml` (ruff 100,
  mypy strict). All verified via the GitHub API 2026-09-20.
