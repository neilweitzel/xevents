# xevents

Evidence-first incident intelligence: record, preserve, and reconcile **public**
claims about cyber incidents — starting with ransomware victim listings and
breach disclosures. Never treat a single source's claim, or echoed claims, as
established fact.

**Pivot (2026-09-21):** the public surface is **sector-aggregated** — no
organization names, no threat-actor brand names. Two repositories:
`neilweitzel/xevents` (public: app, research output, docs, evidence manifest)
and `neilweitzel/xevents-internal` (private: raw observations, raw evidence,
review decisions). The public build never reads the private repo. See
[docs/open-decisions.md](docs/open-decisions.md) #8–#11 and
[docs/naming-policy.md](docs/naming-policy.md).

## Docs

- [AGENTS.md](AGENTS.md) — operating manual: the doctrine, scope discipline,
  licensing/ToS discipline, evidence-handling rules, scar tissue, dependency
  and docs discipline. Read this before touching anything.
- [docs/mvp-scope.md](docs/mvp-scope.md) — **the approved build target:**
  tightly-scoped MVP definition with acceptance criteria and an explicit
  non-goals list. If it's not here, it's not approved work.
- [docs/open-decisions.md](docs/open-decisions.md) — user rulings. Never
  resolve an open question by assumption.
- [docs/naming-policy.md](docs/naming-policy.md) — the no-name boundary:
  what is never published, what the public taxonomy is, and how the
  private holdings differ.
- [docs/dashboard-spec.md](docs/dashboard-spec.md) — the public research
  surface: pages, practitioner jobs, growth strategy, runbook design.
- [docs/dispute-process.md](docs/dispute-process.md) — sector-appropriate
  dispute/correction handling.
- [docs/lawful-basis-memo-template.md](docs/lawful-basis-memo-template.md) —
  the launch-gate memo template. Unwritten; no memo, no public surface.
- [docs/adr/](docs/adr/) — Architecture Decision Records; each record carries
  its decision status. See [AGENTS.md](AGENTS.md) for the accepted and
  superseded decision rules:
  - 0001 — immutable observations vs cautiously-resolved incident records
  - 0002 — licensing-clean ingestion architecture
  - 0003 — capture-at-ingest evidence preservation
  - 0004 — corrections, denials, removals, retractions as first-class history
  - 0005 — entity-resolution strategy
  - 0006 — explainable, independence-aware confidence model
  - 0007 — de-listing/removal detection via re-polling and diffing
  - 0008 — PostgreSQL as the system of record (superseded by 0009)
  - 0009 — static-first architecture: GitHub Actions + Pages, git as the system of record
  - 0010 — quality assurance: gates, burn-in, review queues, incident response
- [docs/data-model.md](docs/data-model.md) — core schema: source, observation,
  evidence artifact, listing state, entity, alias, incident, membership,
  correction event, confidence assessment, review task, model version; sector
  classification fields; the observation→incident and correction propagation
  lifecycles; the two-repo physical mapping; the aggregate JSON export
  contract.
- [docs/source-spec-ransomlook.md](docs/source-spec-ransomlook.md) — the MVP
  ingest source, specified: verified endpoints, record schema, poller rules,
  backfill policy, known limitations. Re-verify at build time.
- [docs/retention-policy.md](docs/retention-policy.md) — **PROPOSAL:**
  evidence tiering and ledger retention in a git-native world (required by
  ADR 0003).
- [docs/evidence-storage.md](docs/evidence-storage.md) — physical evidence
  plan: raw evidence in the private repo, public hash manifest, volume
  strategy.
- [docs/glossary.md](docs/glossary.md) — precise definitions; the authoritative
  home for what terms mean.
- [research/landscape-report.md](research/landscape-report.md) — the evidence
  base (Sep 17, 2026): source landscape, licensing findings, gaps, blockers.
  Every architectural claim in the docs traces to a finding here.

## Status

Implementation is underway. Repository invariant checks, baseline branch
protection, and an offline signed-publication-proof verifier exist. The
[synthetic research preview](app/README.md) is runnable locally and uses only
invented aggregate fixtures.

This is not a live production service. Source ingestion, a trusted production
aggregate adapter, proof enforcement in required CI, and the publication/build
path are not yet integrated end to end. No public Actions workflows are
installed. Passing local tests or viewing the synthetic app does not authorize
live publication; the launch memo, review and burn-in gates still apply.
