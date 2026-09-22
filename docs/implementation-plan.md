# xevents — implementation plan (v1)

**Status:** accepted, 2026-09-22. Machinery-first vertical-slice plan
from scaffolded state to first public publish. Milestones are named by
what they deliver end to end, not by which layer they touch. Each
milestone has CI-enforceable acceptance criteria; any AC that cannot
be enforced in CI is marked **[operator-verified]** and explains why.

Changes to this plan require an ADR or open-decisions.md entry. Adding
an acceptance criterion to a milestone that has not yet started is a
plan revision (PR to this doc); adding one to a milestone already
underway is a decision to defer or reject scope. This file does not
substitute for the ADRs and specs it references — it sequences them.

## Doctrine (recap, non-negotiable)

Everything below is under these constraints. If a milestone appears to
violate one, the milestone is wrong.

- **Static-first** (ADR 0009): no servers, no runtime database, no
  server-side dependencies. The public surface is GitHub Pages, built
  by GitHub Actions.
- **Two-repo boundary** (ADR 0011, 0012): the public build never
  reads the private repo. Only the aggregation-boundary GitHub App
  (`xevents-boundary[bot]`) crosses, writing to exactly three paths.
- **Machinery-first approval** (open-decisions.md #18): schedule work
  is minimized; event-driven full audit fires when the mechanical
  invariants change. No calendar-quarterly review substitutes.
- **Naming policy** (docs/naming-policy.md): the public surface names
  no organizations, no threat-actor brands, no malware families, no
  employee names.
- **Correction ledger** (ADR 0004): the private substrate is
  append-only; the public face renders through aggregate
  `corrections[]`.
- **Nygard immutability** (docs/adr/0000-template.md): accepted ADRs
  are superseded, never edited. Plan revisions that change what an
  ADR decided require a superseding ADR, not an edit to the plan.

## Vertical-slice sequencing

Every milestone delivers a working slice of the whole system, thinnest
first. The thin slice runs on **real machinery** — real Actions, real
Pages, real boundary workflow, real G5 gate — with placeholder or
narrow-scope data. Depth is added inside subsequent milestones by
widening what each stage handles, never by replacing a mock with a
real thing.

The corollary: **the boundary and G5 are proven before real data
crosses.** M1 stands up the load-bearing control (App + workflow + G5)
and hardens it against a designed adversarial corpus. Only after that
gate is proven does M2 build the public surface it will feed. Only
after the surface is proven does M3 introduce real observations.

Real data never touches an unproven boundary. This is what
machinery-first means at the sequencing level.

## Milestones

### M1 — Boundary contract proven against an adversarial corpus

**Goal.** The `xevents-boundary` GitHub App, the private-repo boundary
workflow, and the G5 name-scan gate are live and exercised against a
designed adversarial corpus that covers every G5 failure mode in
ADR 0013. No public surface, no real data — this milestone builds and
proves the load-bearing control before anything real crosses it.

**Rationale.** The boundary is the trust boundary of the whole design
(ADR 0012 §Context). G5's job is to fail closed against adversarial
inputs; the only way to know it does is to run it against inputs
designed to break it. Doing this against a synthetic corpus in M1 —
before real observations exist and before any public surface — means
the first real name-bearing content is caught by a gate that has
already been stress-tested.

**What ships:**

1. **`xevents-boundary` GitHub App registered** and installed on both
   repos. App private key stored in the private repo's Actions
   secrets. Minimum scopes per ADR 0012 (contents:write on the three
   boundary write set paths of the public repo; no other scopes).
2. **Public repo branch protection on `main`:**
   - Manual commits: only from the project lead's account.
   - `xevents-boundary[bot]` commits: allowed only against the three
     boundary write set paths (`data/aggregates/`,
     `evidence-manifest.jsonl`, `coverage-boundary-statement.md`).
     Any commit that touches a fourth path fails the protection
     check.
   - Signed commits required from both principals.
3. **Private repo boundary workflow**
   (`.github/workflows/publish-boundary.yml`) that:
   - Runs on `workflow_dispatch`.
   - Loads a batch from a staging directory
     (`tests/boundary/fixtures/<batch-id>/`).
   - Derives the denylist per ADR 0013 §2 from the fixture's
     synthetic private observations plus the static denylist.
   - Runs G5 (§3–§5) against every value in every fixture aggregate
     row, every evidence-manifest row, and the coverage-boundary
     statement.
   - Fetches every URL in `vendor_advisories` and `mitigation_refs`
     and scans the fetched destination (§5).
   - Emits `g5-reports/<batch-id>.json` with the required
     structure (ADR 0013 §9).
   - On G5 pass: uses the App installation token to push the three
     boundary-writable files to the public repo `main`.
   - On G5 fail: quarantines the batch, appends a correction-ledger
     entry, does not use the App token, and exits non-zero.
4. **Adversarial corpus** under
   `xevents-internal/tests/boundary/fixtures/`, structured as one
   directory per fixture batch, each with the private-side inputs
   (synthetic observations, denylist, homoglyph table version) and
   the expected G5 outcome (pass / quarantine with specific match
   record). Fixtures cover, at minimum:
   - **Trivial pass:** a batch with placeholder aggregates that
     contain zero name-bearing tokens.
   - **Exact-name match:** an aggregate row whose free-text field
     contains a static-denylist name verbatim. Expected: quarantine.
   - **Cyrillic homoglyph:** the same name written with Cyrillic
     lookalikes (per `denylist/homoglyphs.jsonl` v1.0.0). Expected:
     quarantine after normalization.
   - **Greek homoglyph:** analogous with Greek confusables.
   - **Mixed-script:** a name with one homoglyph swap among Latin
     letters. Expected: quarantine after normalization.
   - **Alias match:** a name matching an entity's alias in the
     derived denylist, not the canonical form. Expected: quarantine.
   - **Threat-actor brand:** a name matching a threat-group entity
     in the derived denylist. Expected: quarantine.
   - **Malware-family name:** a name matching the malware taxonomy.
     Expected: quarantine.
   - **URL destination poisoning:** an aggregate whose
     `vendor_advisories` URL resolves to a page containing a
     denylist name. Expected: URL-fetch step catches it; quarantine.
   - **URL unreachable:** a URL that times out or 404s. Expected:
     quarantine with `url_fetch_outcome: unreachable`.
   - **Manifest-row name leak:** an evidence-manifest row whose
     `source_ref` contains an organization name. Expected: quarantine.
   - **Coverage-boundary statement name leak:** the statement file
     itself contains a denylist name. Expected: quarantine.
   - **Boundary write-set violation:** a batch that attempts to
     write to a fourth path (e.g., `docs/`). Expected: refused by
     branch protection before G5 even runs; the App token push
     rejected at the GitHub API layer.
   - **Correction propagation:** a variant of the trivial-pass
     fixture with an extra input — one `correction_event` (a
     `dispute_opened` entry) is present in the private
     correction-ledger. Expected: G5 passes; the pushed aggregate's
     `corrections[]` contains the entry.
5. **Machinery-invariants report** format defined and emitted per
   publish attempt: three-path boundary write set assertion, G5
   outcome, denylist size, denylist version, homoglyph table
   version, fixture id, timestamp. Archived under
   `machinery-invariants/<publish-attempt-id>.json` in the private
   repo.
6. **Correction-ledger propagation drill.** A synthetic
   `correction_event` is appended to the private correction-ledger
   as part of one fixture's inputs; the boundary workflow includes
   the correction in the pushed aggregate's `corrections[]` array.

**Acceptance criteria (all must pass in CI or on the operator's
verified run):**

| AC | Enforcement | Description |
|---|---|---|
| AC1.1 | CI | The trivial-pass fixture produces a G5 report with `outcome: pass`, `matches: 0`, and results in three files landing in the public repo `main` via the App token. |
| AC1.2 | CI | Each of the eleven quarantine fixtures (exact-name, Cyrillic homoglyph, Greek homoglyph, mixed-script, alias, threat-actor, malware-family, URL-destination poisoning, URL unreachable, manifest-row leak, statement leak) produces a G5 report with `outcome: quarantine`, at least one match, the expected match rule, and no push to the public repo. |
| AC1.3 | CI | The boundary-write-set-violation fixture is rejected by branch protection at the GitHub API layer: the App token push returns 4xx, no commit lands, the workflow exits non-zero. |
| AC1.4 | CI | Every quarantine fixture appends exactly one correction-ledger entry with `event_type: administrative_note` whose `note` field records `authority: g5-machinery`, the failing fixture id, the match rule, and the denylist version (per docs/data-model.md `correction_event.event_type = administrative_note`). |
| AC1.5 | CI | Correction-propagation fixture (fourteenth fixture, a variant of the trivial-pass fixture with an extra input): a synthetic `correction_event` appended in the private repo's correction-ledger before the boundary run appears in the pushed aggregate's `corrections[]` array with the same fields. G5 must still pass (the correction fields are pre-vetted vocabulary; free-text `note` is name-scanned like every other value). |
| AC1.6 | CI | Every `g5-reports/<batch-id>.json` conforms to the ADR 0013 §9 schema: batch id, scan timestamp, denylist size, denylist version, homoglyph table version, scan-target counts, URL fetch outcomes, and every match record (denylist entry hash, match rule, scan target, match position). Schema-check runs on every emitted report. |
| AC1.7 | CI | The `xevents-boundary` App scopes are exactly the minimum required by ADR 0012 §Mechanics (`contents:write` on both repos, `actions:write` on `xevents`, `metadata:read`, nothing else). A test enumerates the App's declared scopes and fails if any additional scope is present. |
| AC1.8 | CI | Boundary-write-set assertion runs on every PR to either repo: a test loads ADR 0012 §Boundary write set, private AGENTS.md, and private `docs/file-layout.md`, parses the three-path list from each, and asserts all three lists are identical. Any drift fails CI on the PR and blocks merge. |
| AC1.9 | CI | Machinery-invariants report is emitted on every publish attempt (pass and quarantine both) and archived. A test asserts every run produces a report; a missing report fails CI. |
| AC1.10 | CI | Fail-closed structure: a synthetic modification to the workflow that attempts to use the App token *before* the G5 step (moving G5 later) is refused by a workflow-lint test that asserts G5 completes before the token-using step. |
| AC1.11 | CI | Denylist derivation determinism: the derivation function invoked twice on identical inputs produces byte-identical output (verified in-memory in the test). The G5 report captures `denylist_size` and `denylist_version` per ADR 0013 §9 (not the raw entries, which would leak); the test asserts both fields match across the two runs. |
| AC1.12 | CI | URL-fetch instrumentation: a fixture where the same advisory URL appears twice in one batch causes the URL to be fetched exactly once within that batch (in-batch deduplication), with the fetched-destination hash recorded once in the G5 report. Cross-run caching is deferred to post-M8; this AC establishes the per-batch instrumentation the later optimization will build on. |
| AC1.13 | CI | JSONL header-row convention (private `docs/file-layout.md`): every JSONL file the workflow reads or writes (`evidence-manifest.jsonl`, `denylist/*.jsonl`, `data/aggregates/*.jsonl`) carries the leading metadata header row; readers skip it. |
| AC1.14 | CI | Nygard immutability check runs on every PR touching `docs/adr/` and asserts no accepted ADR body is modified without a supersession declaration. |
| AC1.15 | CI | Docs QA per ADR 0010 §4: (a) cross-reference lint (every ADR and doc reference in the repo resolves to an existing file/section), (b) decision-consistency check (no `TBD` / `UNDECIDED` / "proposed" language in text that references an accepted ADR or a decided open-decisions.md entry), (c) glossary-term usage sweep. All three sub-checks run on every PR. |
| AC1.16 | [operator-verified] | The App installation on both repos is confirmed via the GitHub UI; the App's private key is present only in `xevents-internal` secrets and not in `xevents`. **Operator-verified because App installation state and secret placement are external to CI.** |

**Explicitly out of scope for M1:**

- Any public surface (M2).
- Real RansomLook ingest (M3).
- Real aggregation, sector classification, or entity resolution (M4+).
- Correction-ledger operator UI or dispute-process page (M7).

**Exit criteria:** all 16 ACs green; every adversarial fixture
produces the expected G5 outcome; branch protection rejects the
fourth-path push at the API layer; App scopes are minimum; machinery-
invariants report format is stable.

---

### M2 — Public site skeleton over the proven boundary

**Goal.** The static site builds on GitHub Pages via a public-repo
GitHub Actions workflow, consuming placeholder aggregates that were
pushed across the proven M1 boundary. The public surface exists,
deploys reproducibly, and renders the placeholder content correctly.
Still no real data.

**What ships:**

1. **Public repo build workflow**
   (`.github/workflows/build-site.yml`) that:
   - Runs on `workflow_dispatch` only (invoked by the boundary
     App after each successful push per ADR 0012 §Mechanics; also
     invocable manually by the project lead).
   - Reads `data/aggregates/*.jsonl`, `evidence-manifest.jsonl`,
     and `coverage-boundary-statement.md` (whichever exist).
   - Emits `site/` (static HTML + JSON snapshots).
   - Deploys `site/` to GitHub Pages via the official
     `deploy-pages` action.
2. **Placeholder aggregates** pushed via the M1 boundary:
   `data/aggregates/view1.jsonl` and `view2.jsonl` each contain a
   single row explicitly marked `synthetic: true`, window bounds set,
   all counts zero, sector = one placeholder value.
3. **Site skeleton pages:**
   - Landing page with naming-policy statement, methodology summary,
     and the coverage-boundary summary.
   - View 1 sector-exposure page (placeholder single row).
   - View 2 technique-detail page (placeholder single row).
   - Coverage-boundary statement page (from the pushed statement
     file).
   - Explicit "xevents is in pre-launch" banner across every page.
4. **Deterministic build.** Two builds against the same inputs
   produce byte-identical `site/` outputs.

**Acceptance criteria:**

| AC | Enforcement | Description |
|---|---|---|
| AC2.1 | CI | `build-site.yml` runs to completion on `workflow_dispatch` (invoked by the boundary App per ADR 0012 §Mechanics); `site/` is produced; Pages deploys successfully. Manual dispatch by the project lead is also permitted. Push triggers are not enabled (a push does not trigger a rebuild; only the boundary's explicit dispatch does). |
| AC2.2 | CI | Deterministic build: two runs on the same inputs produce byte-identical `site/`. |
| AC2.3 | CI | Naming-policy sweep on the rendered `site/`: zero organization, actor, or malware names. (Trivially true against placeholder content — this AC establishes the check.) |
| AC2.4 | CI | Every page contains the pre-launch banner and the naming-policy statement. |
| AC2.5 | CI | Data isolation: `build-site.yml` reads data only from the three boundary-writable paths (`data/aggregates/`, `evidence-manifest.jsonl`, `coverage-boundary-statement.md`); a test greps the workflow, its build script, and every template it invokes to assert no other `data/` path, no `evidence/` path, and no reference to `xevents-internal` is read. Templates, static assets, and docs (`docs/dashboard-spec.md`) may be read freely as they are checked-in build inputs, not data. |
| AC2.6 | [operator-verified] | The public Pages URL loads. Every page renders the placeholder content correctly and displays the pre-launch banner. **Operator-verified because Pages URL reachability is external to CI.** |
| AC2.7 | CI | End-to-end drill: run the M1 boundary workflow with a trivial-pass fixture. The boundary pushes the three files to `xevents` and then invokes `build-site.yml` via `workflow_dispatch` per ADR 0012 §Mechanics. The dispatched build produces the expected placeholder rendering. |
| AC2.8 | CI | All M1 cross-cutting invariants (AC1.8, AC1.14, AC1.15) continue to pass. |

**Explicitly out of scope for M2:** real observations; real aggregates;
per-page interactivity beyond the static rendering; correction-ledger
page; dispute-process page.

**Exit criteria:** the public site is live at its Pages URL with
placeholder content that flowed through the M1 boundary; all 8 ACs
green.

---

### M3 — First real observation crosses the machinery

**Goal.** RansomLook ingest is live in the private repo. One
observation and its evidence artifact land per poll; the
evidence-manifest gets a real hash row per observation. The public
evidence-manifest is populated with real hashes on the next boundary
publish, but the public aggregates remain the same synthetic
placeholders — aggregation itself is M4. This is the smallest slice
that proves the full ingest → evidence-manifest → public audit
commitment path is real.

**What ships:**

1. **Private repo ingest workflow**
   (`.github/workflows/ingest.yml`) that runs on the cron cadence
   from open-decisions.md #5 (2-hour trigger with a 6-hour
   effective-cadence guard). Each run:
   - Fetches the current RansomLook API window
     (docs/source-spec-ransomlook.md).
   - For each new item, computes a SHA-256 of the raw payload,
     writes the raw bytes into `evidence/<sha256>`, appends one
     `observation` row to `data/observations.jsonl`, and appends
     one row to `evidence-manifest.jsonl`.
   - Idempotency: an item already present (keyed by
     `source_item_key`) updates `listing_state.last_seen_at` only.
   - Poll-run metadata written to `data/poll_runs.jsonl`.
2. **Boundary publish updated** to include the real
   `evidence-manifest.jsonl` on each run. Aggregates remain
   synthetic; the placeholder-with-zeros pattern is preserved but
   `window_end` rolls forward each publish.
3. **Public site updated** to render an evidence-manifest browser
   (dashboard-spec.md §5) — a table of the last N manifest rows
   with `source_name`, `retrieved_at`, `payload_sha256`. Every
   `source_ref` is verified name-free before display.
4. **G5 scans real evidence-manifest rows.** Since manifest rows
   are hashes + name-free `source_ref` + sourcing metadata, G5
   must pass with zero matches on every real run. Any G5 match on
   a manifest row is a live incident — the M1 adversarial corpus
   proved the gate; here we prove it against real content.
5. **Denylist expansion.** The static denylist begins populating
   with real entries: threat-actor names from the ingested source
   window, malware families from the taxonomy. First real denylist
   entries land here.

**Acceptance criteria:**

| AC | Enforcement | Description |
|---|---|---|
| AC3.1 | CI | Ingest workflow completes end-to-end against RansomLook's live API; produces at least one observation row, one evidence artifact under `evidence/`, and one evidence-manifest row with matching SHA-256s. |
| AC3.2 | CI | Idempotency: two consecutive runs on unchanged upstream produce zero new observation rows and zero new evidence-manifest rows; `listing_state.last_seen_at` updates. |
| AC3.3 | CI | Poll-run metadata (docs/data-model.md `poll_run`) is written on every run: start, end, source name, items fetched, items new, items skipped-as-duplicate, errors. |
| AC3.4 | CI | Two-clock doctrine per row (docs/data-model.md §observation, ADR 0010 §4): every observation carries a non-null `observed_at` (when xevents recorded the observation), a `retrieved_at` (when the payload was fetched), and either a `source_claimed_at` value the source supplied or an explicit null (never synthesized). `poller_version` (registered in `model_versions.jsonl`) is present on every row. |
| AC3.5 | CI | G5 scans the real evidence-manifest before boundary publish and passes with zero matches. |
| AC3.6 | CI | A synthetic observation whose `subject_raw` is a denylist entry causes G5 to match on the pre-publish scan and quarantine the batch. (Reuses the M1 fixture rig.) |
| AC3.7 | CI | Public evidence-manifest browser page contains N real rows after M3 lands; every row has a valid SHA-256 and a name-free `source_ref`. |
| AC3.8 | CI | Cadence guard test: an ingest run inside the 6-hour effective-cadence guard is a no-op with a `poll_run` row explaining why (open-decisions.md #5). |
| AC3.9 | CI | Coverage-boundary statement G-gate counters are updated from real `g5-reports/<batch-id>.json` files, not synthetic values. |
| AC3.10 | [operator-verified] | Public Pages URL shows N real evidence-manifest rows and one placeholder aggregate row. No organization, actor, or malware name is visible. |
| AC3.11 | CI | Immutability: any pipeline run that modifies an existing `observation`, `evidence-manifest`, or `correction_event` row (rather than appending) fails CI. |

**Explicitly out of scope for M3:** entity resolution (M5); confidence
assessment (M5); sector classification (M4); real aggregation (M4);
view 2 real content (M6); dashboard beyond a single page + the manifest
browser (M7).

**Exit criteria:** N observations live in the private repo; N manifest
rows live in the public repo; the aggregate placeholder still shows
zero counts; all 11 ACs green.

---

### M4 — First real aggregate, sector-aggregated view 1

**Goal.** Real observations are grouped by sector × time window and
published as view 1 aggregates. Sector classification is deterministic
per docs/attack-class-vocabulary.md and the sector taxonomy. Small-cell
disclosure rule (open-decisions.md #13) is enforced. Zero
organization/actor/malware names leak into any aggregate row.

**What ships:**

1. **Sector classification pipeline** in the private repo. Each
   observation is mapped to zero-or-one sector by rule (initial
   rules in `docs/sector-classification-rules.md`, drafted as part
   of M4). Unmapped observations count toward an `unmapped` bucket
   and are surfaced in the coverage-boundary statement.
2. **Aggregation pipeline** in the private repo that materializes
   `data/aggregates/view1.jsonl` from observations. Every aggregate
   row contains: sector, window_start, window_end, claim_count,
   confidence_breakdown (zero-init until M5), victim_acknowledged_
   breakdown (zero-init until M5), attack_class_breakdown,
   data_classes_claimed, corrections[] (empty at M4),
   manifest_refs[], attribution[].
3. **Small-cell rule enforcement.** Any aggregate row with
   claim_count below the small-cell threshold
   (open-decisions.md #13) is either suppressed or rolled up into a
   larger window per the rule. The disposition is recorded in the
   coverage-boundary statement.
4. **Public site view 1 rendering.** The sector-exposure page
   (dashboard-spec.md §View 1) is generated from real aggregates,
   with the naming policy, the two clocks, the confidence bands,
   and the re-identification caveat prominently stated.
5. **First correction propagation drill on real data.** A synthetic
   `correction_event` (dispute_opened) is filed against one of the
   observations; boundary re-publish shows the correction appearing
   in the affected aggregate's `corrections[]` and on the rendered
   sector page.
6. **Attribution strings.** Every RansomLook-derived aggregate
   carries the CC BY 4.0 attribution string in `attribution[]`.

**Acceptance criteria:**

| AC | Enforcement | Description |
|---|---|---|
| AC4.1 | CI | Aggregation produces `data/aggregates/view1.jsonl`; every row's `claim_count` equals the underlying observation count after small-cell rule; every `manifest_refs[]` entry is present in `evidence-manifest.jsonl`. |
| AC4.2 | CI | Sector-classification fixture with known labels produces the expected assignments; unmapped observations land in `unmapped` with a coverage-boundary note. |
| AC4.3 | CI | Small-cell rule: a fixture that would produce a row below threshold is suppressed or rolled up; disposition recorded in `disclosure_action`. |
| AC4.4 | CI | G5 scans every value in every view 1 aggregate row and passes with zero matches on real data. Sector, attack_class, and data_class_* fields are pre-vetted vocabulary; no free-text organization names are possible by construction. |
| AC4.5 | CI | Aggregate immutability: recomputing an aggregate on an unchanged observation set produces byte-identical output; changes are auditable via git history. |
| AC4.6 | CI | Correction propagation on real data covers both event classes: (a) `dispute_opened` — the aggregate's `corrections[]` gains the entry, `claim_count` is unchanged, the public sector page renders the dispute; (b) `retraction` — the aggregate's `corrections[]` gains the entry, `claim_count` is decremented, the underlying observation is not deleted (append-only per ADR 0001); the public sector page shows both the pre-retraction and post-retraction `claim_count` via the correction. |
| AC4.7 | CI | Attribution: every RansomLook-derived aggregate has the CC BY 4.0 attribution string; missing attribution fails CI. |
| AC4.8 | CI | The public sector-exposure page renders all real aggregate rows; each page carries naming policy, two-clocks explanation, confidence-band methodology, coverage-boundary summary, and a correction-ledger link. |
| AC4.9 | CI | Negative test: a synthetic observation whose `subject_raw` is a real organization name from the static denylist produces an aggregate that still G5-passes (raw doesn't cross), but the test also asserts the coverage-boundary statement correctly reports the suppression. |
| AC4.10 | [operator-verified] | Blue-team-on-Friday test (docs/naming-policy.md): the operator reads three consecutive sector-exposure pages and confirms each answers "would a blue-team engineer do something different if they saw this?" affirmatively. |
| AC4.11 | CI | Naming-policy sweep on the generated `site/`: zero organization names, zero threat-actor brand names, zero malware family names anywhere in rendered HTML or JSON. |

**Explicitly out of scope for M4:** entity resolution (M5); real
confidence rationales (M5); view 2 real content (M6); named
comparison to other trackers (never — naming policy).

**Exit criteria:** view 1 aggregate on the public surface, populated
from real observations; every AC green; correction propagation drilled
on real data.

---

### M5 — Real confidence bands and entity resolution

**Goal.** The `confidence_assessment` table is populated from real
inputs: independence classes counted correctly (open-decisions.md #1),
band assigned per model_version, rationale string generated. Entity
resolution runs on real observations, populating `entity` and `alias`
tables. `victim_acknowledged` axis populated from sourced disclosures.
All of this stays in the private repo; the public surface gets
`confidence_breakdown` and `victim_acknowledged_breakdown` counts on
each aggregate row; no per-record confidence or acknowledged status
leaves the boundary.

**What ships:**

1. **Confidence-model v1** per ADR 0006 and open-decisions.md #1.
   Independence classes as defined in ADR 0006.
2. **Entity-resolution pipeline** per ADR 0005. `subject_raw` →
   `entity_id` where resolvable; `alias` rows written; unresolvable
   subjects stay null with the raw preserved (private only).
3. **Victim-acknowledged detection.** A rules-based scanner over
   sourced disclosures (public press statements, 8-K filings, state
   AG notices, HHS OCR entries) populates the `victim_acknowledged`
   axis. Defaults to `unacknowledged`; transitions to `acknowledged`
   require a cited source.
4. **Confidence-breakdown and victim-acknowledged-breakdown counts
   in aggregates.** View 1 aggregates now carry real counts per band
   and per acknowledged status.
5. **Correction ledger extended.** Every `victim_acknowledged`
   transition to `acknowledged` files a correction-ledger entry
   (ADR 0010 §review triggers).

**Acceptance criteria:**

| AC | Enforcement | Description |
|---|---|---|
| AC5.1 | CI | Independence-class counting: a fixture of two observations — one from RansomLook, one from a synthetic echo source whose content is derivative of RansomLook — collapses the echo per ADR 0006 and yields exactly one contributing independence class in `confidence_assessment.independence_classes[]`. |
| AC5.2 | CI | Every incident has a `confidence_assessment` row with `model_version`, `inputs_hash`, `independence_classes[]`, `band`, and non-empty `rationale`. |
| AC5.3 | CI | Immutable confidence: a superseded assessment retains the old row and links via `superseded_by`; the old row remains queryable. |
| AC5.4 | CI | Entity resolution: known-alias fixtures resolve to the correct `entity_id`; unknown subjects stay null with `subject_raw` preserved. |
| AC5.5 | CI | Victim-acknowledged detector: a fixture of victim disclosures triggers the correct transitions; a fixture of silence-only does not. |
| AC5.6 | CI | Aggregate breakdown counts equal per-band and per-acknowledged sums over underlying incidents. |
| AC5.7 | CI | Every `victim_acknowledged` transition produces a corresponding correction-ledger entry. |
| AC5.8 | CI | Naming-policy sweep (repeat of AC4.11) over an aggregate set with real confidence/acknowledged counts: zero names in the rendered `site/`. |
| AC5.9 | [operator-verified] | Public sector page: each band count and each acknowledged count is displayed with methodology text; no per-record confidence or acknowledged status is visible. |
| AC5.10 | CI | `supporting_weight` and `refuting_weight` fields (docs/data-model.md) never appear in any public output — verified by grepping the generated `site/` and every `data/aggregates/*.jsonl` row. |

**Explicitly out of scope for M5:** view 2 (M6); dashboard-spec §6+
(M7); dispute-response operational tooling (M7).

**Exit criteria:** view 1 aggregates carry real confidence and
acknowledged breakdowns; all 10 ACs green.

---

### M6 — View 2 (technique detail) live

**Goal.** The technique-focused view 2 (ADR 0011) is live: CVE
identifiers, KEV flags, vendor advisories, mitigation refs, appliance
classes, misconfiguration classes — per docs/exploitation-vocabulary.md.
Not cross-indexed with view 1 (open-decisions.md #14). URL destination
scanning at G5 time is already proven against adversarial URLs in M1;
here it runs against real advisory URLs.

**What ships:**

1. **Exploitation-vocabulary extraction pipeline** in the private
   repo. Regex extraction of CVE IDs from `description` and linked
   advisories; local cached KEV lookup; vendor-advisory URL
   extraction; mitigation-ref extraction.
2. **View 2 aggregate** (`data/aggregates/view2.jsonl`) built from
   private observations, keyed by technique × time window.
3. **Public view 2 page** rendered from the aggregate. No CVEs or
   vendor names in view 1; no view-1 sector labels in view 2.

**Acceptance criteria:**

| AC | Enforcement | Description |
|---|---|---|
| AC6.1 | CI | CVE extraction: fixture descriptions with known CVE mentions produce the expected `cve_ids[]`; fixtures without CVEs produce empty. |
| AC6.2 | CI | KEV lookup uses the local cached snapshot; snapshot version recorded on each observation; a stale snapshot triggers a warning surfaced in the coverage-boundary statement. |
| AC6.3 | CI | Vendor-advisory extraction: URLs in known formats (Microsoft KB, Cisco PSIRT, Fortinet FSA, Ivanti) are captured; unknown-vendor URLs are captured with a note. |
| AC6.4 | CI | G5 URL-destination scan on real advisory URLs: every URL is fetched, the destination hashed and scanned, the outcome recorded in `g5-reports/<batch-id>.json`. (The M1 adversarial URL fixtures already proved the failure paths; this AC proves the pass path on real URLs.) |
| AC6.5 | CI | View 2 contains no `sector` field; view 1 contains no `cve_ids`, `vendor_advisories`, or `appliance_class`. Cross-indexing test: no row in view 1 shares an `incident_id` with a row in view 2. |
| AC6.6 | CI | Naming-policy sweep on view 2 rendered output: zero organization, actor, or malware names. |
| AC6.7 | CI | View 2 aggregate carries `mitigation_refs[]` for every incident where a mitigation URL was extracted; a defender clicking a rendered link reaches a mitigation page, not a victim disclosure. |
| AC6.8 | [operator-verified] | Blue-team-on-Friday test on view 2: three consecutive pages, each answers the test affirmatively per rendered incident. |
| AC6.9 | CI | Every advisory URL in the batch is fetched during G5; the fetch outcome (200/quarantine/unreachable) is recorded in `g5-reports/<batch-id>.json`. |

**Explicitly out of scope for M6:** any view-1/view-2 cross-index UI;
correlation across views; a unified search bar (open-decisions.md #14
forbids cross-index).

**Exit criteria:** view 2 aggregates live; URL scanning green on real
URLs; ACs green; naming-policy sweep clean across both views.

---

### M7 — Public accountability surfaces live

**Goal.** The four dashboard-spec sections that are not per-view
(dashboard-spec.md §3 methodology, §4 correction ledger, §5 evidence
manifest browser, §6+ coverage-boundary and dispute surfaces) render
from real data. The dispute-process page is live with the
docs/dispute-process.md SLA (open-decisions.md #4). The correction
ledger becomes a queryable page.

**What ships:**

1. **Correction-ledger page** — queryable by sector, technique,
   window, event_type. Rendered from all corrections[] arrays
   across both views' aggregates.
2. **Methodology page** — the full docs/naming-policy.md,
   confidence-band criteria, two-clock doctrine, independence
   classes, coverage-boundary link.
3. **Coverage-boundary statement** — rendered from
   `coverage-boundary-statement.md` on every publish; week-over-week
   diff publicly visible.
4. **Dispute-process page** with docs/dispute-process.md content and
   a public contact route (GitHub issue template).
5. **Attribution and license page** — CC BY 4.0 for the aggregates;
   attribution strings surfaced.

**Acceptance criteria:**

| AC | Enforcement | Description |
|---|---|---|
| AC7.1 | CI | Correction-ledger page renders every correction across both views' aggregates; filters by sector/window/event_type produce the correct subset. |
| AC7.2 | CI | Methodology page contains, verbatim, the six mandatory sections listed in docs/dashboard-spec.md §3. |
| AC7.3 | CI | Coverage-boundary statement page carries per-gate counters (G2/G3/G5/G6/G7) and the boundary-write-set file counts (private `docs/file-layout.md` §Boundary write verification). |
| AC7.4 | CI | Dispute-process page states the acknowledgement SLA (two business days; one for wrongful-listing claims) and the initial-assessment SLA (ten business days), per open-decisions.md #4. |
| AC7.5 | CI | Every RansomLook-derived aggregate row has an attribution string; the attribution page renders the union of unique attribution strings across the site. |
| AC7.6 | CI | Naming-policy sweep on the full generated `site/`: zero names. |
| AC7.7 | [operator-verified] | Operator walks the full public site end-to-end and confirms every dashboard-spec.md-required section is present, correctly named, and internally consistent. |
| AC7.8 | CI | Dispute-process page's public contact route (GitHub issue template) exists and is linked from every dashboard page. |

**Exit criteria:** every dashboard-spec required surface renders from
real data; every AC green; the public site is the surface described
in docs/dashboard-spec.md.

---

### M8 — First public publish (burn-in start)

**Goal.** Everything M1–M7 has established runs on a real weekly
cadence (open-decisions.md #12) against real observations for a
burn-in window (open-decisions.md #17). This is where xevents becomes
a live public research service.

**What ships:**

1. **Weekly publish cadence** enabled: the boundary workflow runs
   on `schedule` per open-decisions.md #12 (weekly public, daily
   internal), not on manual `workflow_dispatch`.
2. **Burn-in window declared** in the coverage-boundary statement:
   "xevents is in a burn-in window; findings are forward-going only;
   no historical claims are made about periods prior to
   ingest-start-date."
3. **Publish-freeze on structural drift.** If the boundary
   write-set assertion test (AC1.8) fails during a scheduled
   publish, the publish is aborted, a correction-ledger entry is
   filed, and the operator is notified.
4. **Machinery invariants continuously checked.** Every publish
   emits a machinery-invariants report (M1 format): three-path
   boundary write set, G5 pass, naming-policy sweep clean, aggregate
   immutability, coverage-boundary reconciles with private counters.

**Acceptance criteria:**

| AC | Enforcement | Description |
|---|---|---|
| AC8.1 | CI (scheduled) | The weekly boundary workflow runs on schedule and completes end-to-end with green G5 and zero manual intervention. |
| AC8.2 | CI | Machinery-invariants report is emitted on every publish and archived under `machinery-invariants/<publish-date>.json` in the private repo. |
| AC8.3 | CI | Publish-freeze test: a synthetic branch that breaks the boundary-write-set invariant (e.g., adds a fourth path to private AGENTS.md without an ADR amendment) fails the pre-publish check and prevents the workflow from pushing. |
| AC8.4 | [operator-verified] | Neil reads the burn-in-window declaration on the public coverage-boundary page and confirms it reads correctly. |
| AC8.5 | CI | Post-publish audit: naming-policy sweep on the just-published `site/`; boundary-write-set assertion; G5 report present and valid. Failure files a correction-ledger entry and blocks the next publish until resolved. |
| AC8.6 | CI | Correction-ledger propagation drill (M1 AC1.5) re-run in the M8 configuration against real data and passes. |

**Exit criteria:** first weekly publish landed; burn-in declared;
machinery-invariants report format holds up under real cadence;
correction-ledger receives no unresolved entries during the first
publish cycle.

## Cross-cutting invariants (checked at every milestone)

Properties of the system that must hold from M1 forward. Each is a CI
check that runs on every PR and every scheduled publish. A regression
blocks merge and blocks publish.

| Invariant | Check |
|---|---|
| Nygard immutability | No accepted ADR body is modified in a PR that doesn't declare supersession. Diff-scanning check compares each PR against the accepted-ADR set. |
| Boundary write set = 3 paths | List stated in three places (ADR 0012, private AGENTS.md, private `docs/file-layout.md`) and asserted identical by AC1.8. Extending the set requires an ADR amendment that updates all three. |
| Naming policy | Every publish scans generated `site/` for organization/actor/malware names. Zero tolerance. |
| G5 fail-closed | Boundary workflow never uses its App token unless G5 passes on the exact batch being published. Enforced by workflow structure (AC1.10), not by convention. |
| Correction propagation | Every correction filed in the private ledger propagates to the affected aggregate's `corrections[]` within one publish cycle. Enforced by an end-to-end test on every PR that touches aggregation. |
| Append-only | Immutability checks on observations, evidence-manifest, correction_event, confidence_assessment. Any pipeline run that rewrites a line fails CI. |
| Machinery-first | Any new gate, review, or human step must be automatable or explicitly justified in an open-decisions.md entry as machinery-first-inappropriate. |

## Sequencing rationale

- **M1 first, no data, no public surface.** The boundary is the
  trust boundary of the whole design. Standing it up against a
  designed adversarial corpus is the strongest first proof — G5 is
  tested against every failure mode ADR 0013 §5 describes before
  any real name-bearing content ever crosses. Real data never
  touches an unproven boundary.
- **M2 second, public site over the proven boundary.** With the
  boundary hardened, the public surface can be built with
  confidence that anything it renders came through a working gate.
  Placeholder aggregates flow through the M1 machinery; the site
  build proves its own reproducibility.
- **M3 before aggregation.** One real observation crossing to
  evidence-manifest is a stronger proof than an aggregate over
  no-data. It also exercises the G5 gate against real
  source-derived content (source names, source_refs) before we
  add the derived-aggregate surface.
- **M4 before confidence.** Structural correctness (aggregation,
  small-cell, sector classification) first; explainability
  (confidence bands with rationales) second. If the aggregation is
  wrong, richer per-row explanation just makes the wrong number
  legible.
- **M5 before view 2.** View 1 is the higher-value surface (sector
  exposure for CISOs); view 2 is the more mechanically complex
  surface (URL scanning against real advisories). Getting view 1
  fully right before adding view 2's complexity is the correct
  order.
- **M6 before dashboard.** Both views must exist before the
  dashboard around them can be verified. Building dashboard
  scaffolding earlier would be visible progress without substance.
- **M7 before M8.** The burn-in window is only meaningful if every
  accountability surface (correction ledger, coverage boundary,
  dispute process) is live. Burn-in without those surfaces would
  be publishing without the credibility assets, which contradicts
  ADR 0004.

## Post-M8 backlog (deferred, not committed)

Not part of this plan; recorded here so the plan doesn't imply they
are out of consideration:

- Sector-classification rules v2 (broader ontology; open-decisions.md
  will need to be updated before this ships).
- Historical baseline import (open-decisions.md #6 already sets the
  policy — accept the frozen ransomwatch baseline; the mechanics of
  landing it are post-M8).
- Additional sources beyond RansomLook (post-burn-in; each new source
  needs its own source-spec and independence-class evaluation).
- Dashboard sections beyond docs/dashboard-spec.md v1.
- A subsequent ADR on manifest retention (currently draft in
  `docs/retention-policy.md`).
- URL-fetch caching optimization (M1 AC1.12 provides the ground
  truth for what caching would preserve).

## Cross-references

- ADR 0009 (static-first architecture)
- ADR 0010 (quality assurance; G-gate machinery)
- ADR 0011 (two-view public surface)
- ADR 0012 (aggregation-boundary transport)
- ADR 0013 (G5 name-scan gate)
- docs/mvp-scope.md — the scope this plan implements
- docs/dashboard-spec.md — the surfaces M2–M7 render
- docs/data-model.md — the tables M3–M5 populate
- docs/open-decisions.md — the doctrine the plan sequences under
- xevents-internal/docs/implementation-plan-private.md — companion
  plan for private-repo-only work (denylist maintenance, App key
  handling, evidence-storage internals)

## M1 mechanism revision (post-audit, 2026-09-22)

During M1 execution, a platform audit against GitHub's actual
capabilities on `neilweitzel/xevents` (public repo, personal Free
account) and `neilweitzel/xevents-internal` (private repo, personal
Free account) established that two mechanisms this plan and ADR 0012
depend on are not available on this infrastructure:

- **File-path-restricted push enforcement on public repos.** GitHub
  push rulesets are not available on public repositories on any plan,
  and there is no roadmap to add support. Any AC that expects the
  GitHub API to refuse a push to `xevents` based on the changed file
  paths cannot be implemented as written.
- **Actor-bypass lists in branch protection on personal-account
  repos.** "Restrict who can push" and per-actor bypass are available
  only on organization-owned repos. Any AC that expects branch
  protection to distinguish App pushes from operator pushes at the
  API layer cannot be implemented as written on this account.

ADR 0014 supersedes ADR 0012 §Mechanics and §Identity and audit with
an App-opened-PR transport that preserves the plan's load-bearing
properties (machinery-first, boundary write set as tight rule,
distinct-principal audit signal, G5 as sole gate) using mechanisms
that do exist on this infrastructure (branch protection with required
status checks). The following M1 acceptance criteria are revised in
light of that supersession. Original AC text is preserved above; the
revised interpretation below is what M1 execution actually satisfies.

### AC1.3 revised

**Original wording:** "The boundary-write-set-violation fixture is
rejected by branch protection at the GitHub API layer: the App token
push returns 4xx, no commit lands, the workflow exits non-zero."

**Revised wording under ADR 0014:** The boundary-write-set-violation
fixture is rejected by GitHub-side merge protection: the boundary
workflow runs the fixture, opens a PR against `xevents` `main` whose
diff includes a fourth path outside the boundary write set, the
`boundary-write-set-in-diff` required status check fails, the merge
API returns 4xx when the workflow attempts to merge, no commit lands
on `main`, and the workflow exits non-zero. Enforcement is at the
merge boundary rather than the push boundary; the net effect (no
bytes cross the boundary on a defective batch) is identical.

Alternative wording accepted: if the workflow's local
boundary-write-set-in-diff step fires first and refuses to open the
PR at all, the assertion is also satisfied — no PR, no merge, no
commit. Both paths are proven by fixture 13; the M1 corpus run
records which path fired.

### AC1.8 revised

**Original wording:** "Boundary-write-set assertion runs on every PR
to either repo: a test loads ADR 0012 §Boundary write set, private
AGENTS.md, and private `docs/file-layout.md`, parses the three-path
list from each, and asserts all three lists are identical. Any drift
fails CI on the PR and blocks merge."

**Revised wording under ADR 0014:** unchanged. The tri-declaration
invariant remains the source of truth. The required status check
`boundary-write-set-in-diff` reads the write set from private
`AGENTS.md` (the operational copy that CI ships with the run) and
enforces it against every PR's changed file list.

### Cross-cutting note on private-repo branch protection

Any private-repo AC that references branch protection on
`xevents-internal` (see the private plan) is satisfied by workflow-
internal CI gating rather than GitHub-side branch protection, because
Free-plan private repos do not support branch protection. The private
plan carries the equivalent revision block.

### Cascade effects on later milestones

- **M2–M8:** the App's transport pattern is one PR per batch, not one
  direct push per batch. Boundary-write-set expansions (which the
  plan explicitly anticipates) are still small ADR amendments to the
  boundary write set declaration, and the required status check reads
  from that declaration.
- **AC1.16 operator attestation** (branch protection screenshot) now
  captures branch-protection settings on `main` plus the three
  required status checks, per ADR 0014 §Mechanics.

