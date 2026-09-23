# xevents — AGENTS.md

Operating manual for anyone (human or agent) working on this project. Concrete
rules; `docs/` is the theory, `research/landscape-report.md` is the evidence.

## What xevents is

- An evidence-first incident-intelligence application that records, preserves, and
  reconciles **public** claims about cyber incidents, starting with ransomware
  victim listings and breach disclosures.
- Every claim stays attached to its source, timestamp, sector classification,
  supporting evidence, confidence, and correction history.
- Observations resolve into cautious, explainable incident records (internal);
  the public surface shows **sector-aggregated research** — which verticals
  are hit, how, with what means — never organization or threat-actor names
  (open-decisions.md #8; docs/naming-policy.md).
- **Two repositories.** `neilweitzel/xevents` (public): the application, the
  research output, the docs, the evidence manifest. `neilweitzel/xevents-internal`
  (private): raw observations at full fidelity, raw evidence, ingest logs,
  review decisions. The aggregation boundary between them is the trust
  boundary (open-decisions.md #11; ADR 0010 §1). The public build never reads
  the private repo. Treat `xevents-internal` like a credential store: no
  public references, no public forks, no names in public issues or PRs.
- Long-term goal: a public research surface for defensible trend analysis —
  sector attack patterns, disclosure patterns by sector,
  compromise-to-disclosure lag, exploited-vuln mentions, vendor concentration.
- **The MVP is defined in `docs/mvp-scope.md`: one licensing-clean source
  (RansomLook) end to end, sector-aggregated.** If it is not in the MVP scope
  doc, it is not approved work.

## Scope discipline

- The only approved build target is `docs/mvp-scope.md`.
- Lifting any non-goal, adding any source, or changing any `accepted` ADR
  requires a **new ADR and the user's explicit approval**. An ADR without
  user approval is a proposal, not a decision. New ADRs land as
  `proposed (pending user redline)` and remain there until the user
  redlines them; per Nygard convention, an accepted ADR's body is
  never edited — decisions that change are superseded by a new ADR.
  The current accepted set is ADRs 0001–0007, 0009–0011, 0013, and 0014.
  ADR 0008 is superseded by 0009. ADR 0012 is superseded-in-part by 0014
  (§Mechanics and §Identity and audit only; boundary write set, rotation,
  G5 interaction, private-repo workflow isolation, non-goals still stand).
- A new feature proposal must cite which MVP acceptance criterion it serves.
  If it serves none, reject it or park it as a post-MVP ADR proposal.
- The items in `docs/open-decisions.md` record user rulings. Never resolve
  an open question by assumption, and flag any work that depends on a
  particular answer. Decisions #8–#11 (2026-09-21) reshaped the MVP toward
  sector aggregation; work predating them must be checked against the pivot.

## What xevents is NOT

- Not a breach verification service. We do not confirm intrusions; we record
  claims about them.
- Not a named-victim ledger. The public surface names no organizations —
  ransomware is a shaming business and we do not do its publicity work.
- Not a threat-actor billboard. No actor brand names on the public surface.
- Not a leak-data mirror. We never acquire, host, or redistribute stolen content
  or personal data. We index publicly visible listing metadata and screenshots
  only (raw evidence lives in the private repo; the public manifest carries
  hashes, not bytes).
- Not a second ransomware.live. We do not derive bulk datasets from
  terms-restricted aggregators (see Licensing below).
- Not an indicator platform. MISP/OpenCTI cover IoCs; xevents covers incidents
  and the claims made about them.

## The doctrine (non-negotiable)

1. **Observations are immutable.** Once written, an observation never changes.
   If it was wrong, append a correction event. (Narrow exception: severity-1
   personal-data/secret publication may rewrite public history, logged —
   ADR 0010 §3.)
2. **Echoes are not votes.** Repeated or re-aggregated claims do not corroborate
   each other. Confidence counts independence classes, not raw source count.
   (xfeeds heritage: independence classes over file counts.)
3. **Absence is not evidence.** A source going silent — takedown, seizure,
   scraper failure — means "not observed," never "inactive."
4. **Every claim is framed.** Public-facing text always says whose claim it is.
   Never present an attacker's listing as an established breach.
5. **Corrections are load-bearing.** The retraction ledger is a first-class
   output, not an afterthought.
6. **Names stay private.** No organization or threat-actor name crosses the
   aggregation boundary. The name-scan gate (ADR 0010 §1, G5) enforces this
   mechanically; the naming policy (docs/naming-policy.md) defines it.

## Source-of-truth rules

Authoritative reasoning: ADR 0001. This section is the rules.

- The observation log is the system of record. Incident records, entity tables,
  and confidence assessments are derived and must be re-derivable from
  observations + correction events + the recorded model version.
- Correction events are append-only. Incident records and entity resolution may
  be revised, but every revision carries a rationale and links the
  observations/corrections that caused it.
- Confidence assessments are versioned and superseded, never edited in place.
  Record the model version, the inputs hash, and the contributing independence
  classes.

## Licensing and ToS discipline

Authoritative reasoning: ADR 0002. This section is the rules.

- Ingest tiers come from the landscape report (`research/landscape-report.md`):
  FREELY USABLE / PAID / RESTRICTED. **Build the stored and published dataset
  only on FREELY USABLE sources.**
- **ransomware.live is excluded as a dependency.** No storage of its data at
  scale, no republication, no build-time or run-time dependency. Decision #2
  in docs/open-decisions.md establishes **no contact by default**, including
  manual queries. A minimal, documented, single-fact manual lookup requires
  separate explicit approval; no such exception is granted by this guidance.
  Automated bulk queries and bulk derivation remain excluded.
- **MVP builds on exactly one source: RansomLook** (CC BY 4.0). Attribution
  is mandatory; keep a per-source attribution record in the source registry.
  Adding a second source needs a new ADR + user approval.
- **ecrime.ch is paid-only** ($2,799/yr Pro; commercial re-use needs the
  custom tier). Paid enrichment option, never a foundation.
- Default for any new source: **RESTRICTED until a human clears it.** Verify
  terms before ingesting any new source; re-verify at build time — terms
  change. (Landscape is a September 2026 snapshot.)
- Legal posture notes in ADR 0002 / landscape §6 are reported considerations,
  not legal advice. Independent primary collection sidesteps aggregator
  database rights; get written permission before touching any RESTRICTED
  source at scale.
- Never interact with criminal infrastructure. Passive collection only: no
  engagement with threat actors, no negotiation chats, no probing leak sites.

## Evidence-handling rules

Authoritative reasoning: ADR 0003. This section is the rules.

Counts-only RC qualification: [ADR 0022](docs/adr/0022-unattended-research-rc.md)
authorizes a narrower public manifest of export hashes, bounded metadata
screening and automatic ordinary eligibility. The
[RC research/privacy memo](docs/research-privacy-memo.md) explicitly rejects
guaranteed anonymity and blanket perpetual retention. The operator approved
limited-RC activation on 2026-09-23; technical gates remain mandatory on every
release. Original ADR bodies remain historical decision records.

- **Capture at ingest, into the private repo.** Every observation gets its
  evidence then and there: raw API response (byte-faithful), source
  screenshot, fetch metadata — stored content-addressed (SHA-256) under
  `evidence/` in `xevents-internal`.
- **The public gets hashes, not bytes.** The evidence manifest
  (`evidence-manifest.jsonl`, public repo) carries hashes + provenance per
  observation. Raw name-bearing evidence never enters the public repo
  (docs/evidence-storage.md).
- **No stolen content, no personal data on the public surface.** The
  automated PII screen (ADR 0010, G2) runs at capture; the naming policy
  (docs/naming-policy.md) plus the name-scan gate (ADR 0010, G5) keep the
  public corpus name-free by construction.
- **Breach contents are never published.** Explicit non-goal
  (open-decisions.md #10). Characterize claimed data classes; do not
  acquire or redistribute payloads.
- **Retention is documented and applied** (docs/retention-policy.md):
  git history is the retention mechanism; the ledger is forever.
  Evidence for retracted or false claims is retained alongside its
  correction — deletion would destroy the audit trail.
- If a source's ToS forbids archival copying, do not archive it. Record the ToS
  constraint as an observation and fall back to linking with a fetched-at
  timestamp.
- **Pre-public-surface gate:** the written lawful-basis / public-interest
  research justification must exist and be reviewed before serving data
  publicly. No memo, no public surface.

## Scar tissue — known traps

1. **Licensing is the binding constraint**, not engineering. The richest free
   feed cannot be republished. Verify terms before ingesting any new source;
   when in doubt, treat as RESTRICTED until a human clears it.
2. **Hoax injection is live.** Maine's AG register went offline June 12, 2026
   after fabricated VRChat (2.4M claimed) and Discord (10M claimed) filings.
   Treat every inbound claim as attacker- or submitter-asserted until evidenced
   otherwise.
3. **Misnaming happens.** Clop listed "Thames Water"; the victim was South
   Staffs Water. Entity resolution must tolerate and record misnamings, not
   silently fix them.
4. **De-listings are invisible.** No source publishes removal history. Re-poll
   and diff; treat removals as first-class observations (payment, false claim,
   or takedown).
5. **EDGAR has no structured Item 1.05 field.** Item filtering is text search
   within 8-K results. The 4-day clock runs from the unobservable materiality
   determination — never compute compromise-to-disclosure lag from EDGAR alone.
6. **SMEs are a coverage boundary.** Free entity sources (SEC ~8k issuers, GLEIF
   ~3.36M mostly large/regulated entities, Wikidata's notable-company bias)
   systematically miss small-business victims. Document the boundary; resolve
   what you can; queue the rest for human review.
7. **Tor volatility.** Leak sites die, rebrand (DarkSide→BlackMatter→ALPHV;
   Royal→BlackSuit; Hunters International→World Leaks), and get seized
   (LockBit/Cronos). Track group-identity chains as observations. Silence is
   not inactivity.
8. **Rate limits are real.** EDGAR: 10 req/s, descriptive User-Agent with
   contact info or 403. GLEIF: ~60 req/min observed (unverified as official) —
   mirror the Golden Copy for batch work. Wikidata: 5 parallel queries per IP,
   60s timeout — use dumps for bulk.
9. **No off-the-shelf evidence archiving exists.** We are building it. Keep the
   design simple enough to audit.
10. **The correction channel ships on day one.** Published dispute/correction
    process before the public research surface. Reference posture: GalaxyWarden's
    published takedown policy; ransomware.live's §9 dispute process.

## Dependency discipline

- Pin everything. Lockfile with hashes; no floating version ranges on ingest
  dependencies.
- Verify the license of every dependency and data source before use. Record it
  in the source registry.
- **AGPL awareness:** RansomLook's platform code and CIRCL's AIL Framework are
  AGPL-3.0. Their *data* is CC BY 4.0 (RansomLook) — consuming the API/feed does
  not trigger AGPL; embedding or modifying their *code* does. Keep the boundary
  clean: consume feeds, don't fork AGPL code into this codebase without a
  deliberate decision recorded in an ADR.
- No mystery deps. If a library's provenance can't be established, don't add it.

## Determinism and reproducibility

- Ingest pipelines are deterministic: same inputs, same observations. Record the
  pipeline version on every observation.
- Entity resolution and confidence assessments record the model/code version
  that produced them.
- Never mutate history to "fix" a bug in derived data — re-derive, record a new
  version, and link the correction.

## Docs discipline

- Every ADR cites the landscape-report finding it rests on. Where the research
  was inconclusive, mark it UNVERIFIED and name what would settle it.
- Docs before code for anything touching the data model, licensing posture, or
  the public surface.
- The landscape report is a snapshot (September 17, 2026). Re-verify source
  terms before building; terms change.

## Automation (xfeeds pattern — ADR 0009)

> Phase note: private scheduled collection is operational. The unattended
> counts-only RC is approved in ADR 0022. Activation requires the reviewed
> public/private changes, production trust key, required head-bound check,
> Actions-based Pages and release-enable setting. The operator approved the
> research/privacy memo and GitHub-only reporting channels on 2026-09-23.
> Do not treat merged code or passing tests as a successful deployment.

The target is for xevents to run like xfeeds: fully automated on GitHub Actions
+ Pages.

The historical build-phase bullets below describe the earlier target, not the
new RC workflow. ADR 0022 uses an App-authored merge to trigger a separately
verified Pages deployment, serialized jobs, private exception records and no
second scheduler. Its concrete implementation takes precedence within that
approved RC scope once activated.

- The scheduled refresh workflow owns the pipeline: cron + internal cadence
  guard (cron fires more often than the effective poll interval — GitHub's
  scheduler drops slots), `cancel-in-progress` concurrency, full-history
  checkout, rebase-retry on push.
- A push made with `GITHUB_TOKEN` does **not** trigger other workflows.
  The refresh workflow therefore deploys Pages itself; `pages.yml` is only
  a `workflow_run` safety net.
- Routine RC eligibility is deterministic and unattended. Exceptional privacy,
  correction and calibration judgments remain human decisions and private;
  identities or evidence must never enter a public issue.
- `keepalive.yml` commits a timestamp only when the repo has gone quiet
  (14 days vs GitHub's 60-day scheduled-workflow disable).
- Never add a second scheduler, a server component, or a secret the
  pipeline doesn't strictly need without a new ADR.

## Code quality (mirrors xfeeds)

- `pytest` — a plethora of tests; no pipeline logic goes untested.
  Every PR adds or updates tests for the behavior it changes.
- `ruff` (line-length 100) and `mypy --strict` — clean on every PR, enforced
  by CI. No `Any` without a comment saying why.
- `uv` for dependency and Python version management.
- Append-only data files are sacred: CI asserts a pipeline run never
  rewrites a line in an append-only file.
