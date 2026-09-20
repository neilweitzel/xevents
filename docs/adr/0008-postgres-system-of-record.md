# ADR 0008: PostgreSQL as the system of record

- Status: **superseded by ADR 0009** (2026-09-20) — retained for the record.
- Date: 2026-09-20
- Deciders: project lead

## Context

The data model (docs/data-model.md) was written with PostgreSQL types
throughout — `timestamptz`, `jsonb`, `text[]`, enums — but no database choice
was ever recorded. This ADR ratifies the implied choice so the build has a
named target and the rationale is reviewable rather than accidental.

## Decision

PostgreSQL is the system of record for xevents. There is no second database
in the MVP: the operational surface (mvp-scope.md item 7) reads from the same
PostgreSQL instance the pipeline writes to.

## Rationale

1. **The schema already assumes it.** `raw_payload jsonb` (arbitrary source
   JSON, queryable), `timestamptz` two-clock semantics, `independence_classes
   text[]`, and the append-only ledger patterns are all native PostgreSQL.
   Choosing anything else would mean rewriting the schema, not the ADR.
2. **jsonb matches the ingest reality.** Source payloads (RansomLook API
   responses today, EDGAR filings tomorrow) are irregular JSON we must
   preserve byte-faithfully *and* query. jsonb gives both without an ETL
   layer or a document store bolted on.
3. **Append-only correctness.** The correction ledger, immutable
   observations, and supersession chains lean on transactional guarantees
   and constraints (FKs, exclusion where needed). A single ACID store keeps
   the audit story simple.
4. **One store, one backup story.** Evidence bytes live on disk / object
   storage with content hashes in the DB (ADR 0003); everything else is
   rows. Disaster recovery is `pg_dump` plus the artifact store — no
   cross-database consistency problem to solve.

## Considered and rejected

- **SQLite:** attractive for a local-only tool, but the append-only ledger
  and concurrent poller/reader access patterns, plus the likelihood of a
  public surface later (open-decisions.md #7), make Postgres the safer
  single choice. If the surface decision lands on local-only *and* single
  user, SQLite remains a documented fallback — but it is not the plan.
- **A document store (MongoDB et al.):** buys nothing the jsonb columns
  don't already provide, and loses FK-enforced ledger integrity.

## Consequences

- docs/data-model.md now names PostgreSQL explicitly; column types are
  PostgreSQL types, not pseudocode.
- The build plan must include Postgres provisioning (local dev and wherever
  the surface runs) and a backup/restore procedure for DB + artifact store
  before any public serving.
