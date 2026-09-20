# xevents

Evidence-first incident intelligence: record, preserve, and reconcile **public**
claims about cyber incidents — starting with ransomware victim listings and
breach disclosures. Never treat a single source's claim, or echoed claims, as
established fact.

## Docs

- [AGENTS.md](AGENTS.md) — operating manual: the doctrine, scope discipline,
  licensing/ToS discipline, evidence-handling rules, scar tissue, dependency
  and docs discipline. Read this before touching anything.
- [docs/mvp-scope.md](docs/mvp-scope.md) — **the approved build target:**
  tightly-scoped MVP definition with acceptance criteria and an explicit
  non-goals list. If it's not here, it's not approved work.
- [docs/open-decisions.md](docs/open-decisions.md) — four decisions only the
  user can make. Undecided; do not resolve by assumption.
- [docs/adr/](docs/adr/) — Architecture Decision Records (all `proposed`,
  pending user redline):
  - 0001 — immutable observations vs cautiously-resolved incident records
  - 0002 — licensing-clean ingestion architecture
  - 0003 — capture-at-ingest evidence preservation
  - 0004 — corrections, denials, removals, retractions as first-class history
  - 0005 — entity-resolution strategy
  - 0006 — explainable, independence-aware confidence model
  - 0007 — de-listing/removal detection via re-polling and diffing
  - 0008 — PostgreSQL as the system of record
- [docs/data-model.md](docs/data-model.md) — core schema: source, observation,
  evidence artifact, listing state, entity, alias, incident, membership,
  evidence, correction event, confidence assessment, review task, model
  version; plus the observation→incident and correction propagation
  lifecycles, coverage-boundary contents, and the vulnerability-linkage
  pattern.
- [docs/glossary.md](docs/glossary.md) — precise definitions; the authoritative
  home for what terms mean.
- [research/landscape-report.md](research/landscape-report.md) — the evidence
  base (Sep 17, 2026): source landscape, licensing findings, gaps, blockers.
  Every architectural claim in the docs traces to a finding here.

## Status

Docs only. No code yet. Second pass complete: scope locked to the MVP doc,
four open decisions awaiting the user, all ADRs marked `proposed` pending
redline.
