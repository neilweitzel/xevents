# xevents — M1 execution checklist

**Status:** accepted, 2026-09-22. Supersedes the closed PR #20 draft
(which encoded a three-ruleset design later found infeasible on
personal-account public repos). Sub-task-level execution checklist
for M1 (boundary contract proven against an adversarial corpus).
Execution mechanism follows ADR 0014 (App-opened-PR transport).
Organized by dependency-ordered work streams: each stream lists
sub-tasks in build order, and each stream ends with the ACs it
satisfies from `docs/implementation-plan.md`.

**Doctrine:** every check-off must be evidence-backed. A task is done
when the artifact it produces is committed, the test asserting it is
passing in CI, or (for `[operator-verified]` items) the operator has
confirmed it and left a signed note in the private repo's
`machinery-invariants/` archive. No self-attestation without evidence.

Progress is tracked by editing this file — replace `- [ ]` with
`- [x]` and append a commit SHA or evidence path in the same line
when checking off. This file is machinery: it is committed, its diff
is auditable, and its final state becomes M1's exit record.

## Work stream table of contents

1. [Repo scaffolding and shared configuration](#ws1)
2. [GitHub App registration](#ws2)
3. [Private repo boundary substrate](#ws3)
4. [Adversarial corpus assembly](#ws4)
5. [G5 gate implementation](#ws5)
6. [Boundary workflow implementation](#ws6)
7. [Public repo branch protection](#ws7)
8. [Machinery-invariants report](#ws8)
9. [Cross-cutting invariant CI checks](#ws9)
10. [CI wiring on both repos](#ws10)
11. [End-to-end execution and evidence archival](#ws11)
12. [Operator-verified attestations](#ws12)
13. [M1 exit gate](#ws13)

## Prerequisites (should already be true; verify before starting)

- [ ] Both repos scaffolded per `xevents-internal/docs/file-layout.md`
      and public repo file layout. **Verify:** `ls docs/adr/` shows
      fourteen ADRs; `ls docs/` shows the accepted-decision docs.
- [ ] All ADRs 0001–0014 present. **Verify:** `ls docs/adr/*.md`
      lists fourteen files. Twelve of them carry `- Status: accepted`
      (0001–0007, 0009–0011, 0013, 0014). Two carry supersession
      status: 0008 (`superseded by ADR 0009`) and 0012
      (`superseded-in-part` by ADR 0014, §Mechanics and §Identity and
      audit only).
- [ ] `open-decisions.md` items 1–18 marked DECIDED. **Verify:**
      `grep -c 'DECIDED' docs/open-decisions.md` matches item count.
- [ ] Git identity configured as `Neil Weitzel
      <weitzel.neil@gmail.com>`.

---

<a id="ws1"></a>

## 1. Repo scaffolding and shared configuration

Purpose: baseline directory structure and shared machinery-first
config that the rest of M1 will populate.

- [ ] Create `xevents-internal/tests/boundary/` directory with a
      `README.md` explaining the fixture-directory contract from
      the plan (four files per fixture: `observations.jsonl`,
      `denylist-state.json`, `expected-outcome.json`, fixture
      `README.md`).
- [ ] Create `xevents-internal/g5-reports/` directory with a
      `.gitkeep` and a `README.md` noting the ADR 0013 §9 schema.
- [ ] Create `xevents-internal/machinery-invariants/` directory with
      a `.gitkeep` and a `README.md` noting the M1 report format
      (see work stream 8).
- [ ] Create `xevents-internal/tests/g5/` directory with a `.gitkeep`
      and a `README.md` explaining that G5 unit tests live here.
- [ ] Create `xevents/data/aggregates/` directory with a `.gitkeep`.
- [ ] Create `xevents/evidence-manifest.jsonl` as an empty file with
      the JSONL header row per `xevents-internal/docs/file-layout.md`
      §JSONL header-row convention.
- [ ] Create `xevents/coverage-boundary-statement.md` as a
      placeholder page stating "xevents is pre-launch; no coverage
      claims are made yet." (Real content lands in M2.)
- [ ] Add `.github/CODEOWNERS` to both repos with `neilweitzel` as
      the sole owner. **Note:** an org-level review requirement is
      not applicable to a solo operator; CODEOWNERS is here as
      evidence, not policy.
- [ ] Add a `.gitignore` block to `xevents-internal` excluding
      `secrets/*` and `.env*` (defense in depth; the App key lives
      only in Actions secrets and never in a file, but the
      `.gitignore` provides a second line of defense).

**AC coverage:** none directly; enables ws3–ws8.

---

<a id="ws2"></a>

## 2. GitHub App registration

Purpose: register `xevents-boundary` GitHub App with the minimum
scope set from ADR 0014 §Mechanics (which supersedes ADR 0012's
scope list by adding `pull_requests: write` for App-opened-PR
transport).

- [ ] Open GitHub → Settings → Developer settings → GitHub Apps →
      New GitHub App.
- [ ] Set App name: `xevents-boundary`.
- [ ] Set Homepage URL: the public repo URL.
- [ ] Set Webhook: disabled (no runtime callbacks needed).
- [ ] Set repository permissions:
  - [ ] `Contents: Read and write`
  - [ ] `Pull requests: Read and write` (per ADR 0014 §Mechanics;
        needed for the App to open and merge boundary PRs on
        `xevents`)
  - [ ] `Actions: Read and write`
  - [ ] `Metadata: Read-only` (auto-added, mandatory)
  - [ ] Every other repository permission: **No access**. In
        particular: `Issues: No access`, `Packages: No access`,
        `Workflows: No access`, `Secrets: No access`, `Deployments:
        No access`.
- [ ] Set organization permissions: **No access** for every entry.
- [ ] Set account permissions: **No access** for every entry.
- [ ] Set "Where can this GitHub App be installed?" to "Only on
      this account".
- [ ] Click "Create GitHub App".
- [ ] Screenshot the created App's permissions page and save it
      to `xevents-internal/machinery-invariants/2026-09-22-app-scopes.png`
      (evidence for AC1.16 later).
- [ ] Generate a private key: App settings → Generate a private key
      → download the `.pem` file to a secure location on the
      operator's local machine only.
- [ ] Install the App on `xevents`: App settings → Install App →
      select `neilweitzel/xevents` → grant. Do not select other
      repos.
- [ ] Install the App on `xevents-internal`: same flow, this repo
      only.
- [ ] Screenshot both install pages and save to
      `xevents-internal/machinery-invariants/2026-09-22-app-installations.png`.
- [ ] Store the `.pem` file's contents as a repository secret in
      `xevents-internal`: repo Settings → Secrets and variables →
      Actions → New repository secret → name
      `XEVENTS_BOUNDARY_APP_KEY` → paste `.pem` contents.
- [ ] Note the App's numeric ID and installation IDs for both repos.
      Store them as repository variables (not secrets — they are
      not sensitive on their own) in `xevents-internal`: repo
      Settings → Secrets and variables → Actions → Variables →
      New repository variable:
  - [ ] `XEVENTS_BOUNDARY_APP_ID`
  - [ ] `XEVENTS_BOUNDARY_INSTALL_ID_PUBLIC`
  - [ ] `XEVENTS_BOUNDARY_INSTALL_ID_PRIVATE`
- [ ] Delete the `.pem` file from the operator's local machine
      after storing it in Actions secrets. Evidence: shred or
      secure-delete; note the deletion timestamp in the
      operator-verified attestation later (ws12).
- [ ] Write `xevents-internal/docs/app-key-rotation.md` (per
      ACP1.7): rotation trigger conditions (compromise suspicion,
      operator departure, annual routine), rotation procedure
      (generate new key, add as `XEVENTS_BOUNDARY_APP_KEY_NEW`,
      switch workflow reference, delete old key), verification
      steps, and correction-ledger entry template (event_type:
      administrative_note; note: authority: operator; reason: key
      rotation).

**AC coverage:** AC1.7 (scope minimum, per ADR 0014 §Mechanics),
AC1.16 (operator-verified installation and key placement), ACP1.4
(secret placement), ACP1.7 (rotation runbook).

---

<a id="ws3"></a>

## 3. Private repo boundary substrate

Purpose: static denylist v0, homoglyph table v1.0.0, derivation
procedure. The M1 corpus reads these; G5 uses them at run time.

- [ ] Create `xevents-internal/denylist/static.jsonl` with the JSONL
      header row per `xevents-internal/docs/file-layout.md` §JSONL
      header-row convention.
- [ ] Populate `static.jsonl` with **synthetic-only** entries for
      the M1 corpus. Real entries land in M3; M1 is corpus-only.
      Entries needed:
  - [ ] `syn-org-001` — a synthetic organization name (something
        deliberately absurd like "Placeholder Corp of Fictitious
        Sector") with 2–3 aliases.
  - [ ] `syn-actor-001` — a synthetic threat-actor brand name.
  - [ ] `syn-malware-001` — a synthetic malware-family name.
  - [ ] Every row: `entity_id`, `canonical_name`, `aliases[]`,
        `sources[]` (empty allowed for synthetic;
        `real_source_required: false` field distinguishes from
        M3+ entries), `first_seen` = 2026-09-22.
- [ ] Commit `static.jsonl`; verify JSONL header row present and
      every row parses as JSON.
- [ ] Create `xevents-internal/denylist/homoglyphs.jsonl` v1.0.0
      with header row.
- [ ] Populate `homoglyphs.jsonl` with substitution rows covering
      the fixtures needed:
  - [ ] Cyrillic confusables for every Latin letter in the M1
        synthetic entity's canonical name (at minimum: а/a, е/e,
        о/o, р/p, с/c, у/y, х/x, etc.).
  - [ ] Greek confusables (α/a, ε/e, ο/o, ρ/p, ν/v, etc.).
  - [ ] Explicit version pin in the header row: `version: 1.0.0`.
- [ ] Commit `homoglyphs.jsonl`; verify version parses.
- [ ] Write `xevents-internal/docs/denylist-derivation.md` (per
      plan §M1 "Denylist derivation procedure documented"):
  - [ ] Header (title, status, date).
  - [ ] "Purpose" section: derives the effective denylist at
        publish time; not stored per ADR 0013 §2.
  - [ ] "Inputs" section: `denylist/static.jsonl`, entity+alias
        state at run time (M1: empty; M3+: populated).
  - [ ] "Derivation steps" section: union canonical + aliases;
        deduplicate; sort deterministically; return byte string.
  - [ ] "Determinism guarantees" section: same inputs produce
        byte-identical output (this is what ACP1.3 tests).
  - [ ] "Nygard immutability" section: procedure is accepted;
        changes require a superseding version and version bump
        of the derivation function.
- [ ] Write `xevents-internal/docs/evidence-storage-layout.md`
      (per ACP1.6): content-addressed `evidence/<sha256>` scheme;
      hash-verified read path; no filename metadata; retention
      pointer to draft `docs/retention-policy.md` (deferred to
      post-M8 per plan post-M8 backlog).

**AC coverage:** ACP1.1 (static denylist), ACP1.2 (homoglyph
table), ACP1.3 (derivation determinism doc), ACP1.6 (evidence
storage layout doc). Enables ws4, ws5, ws6.

---

<a id="ws4"></a>

## 4. Adversarial corpus assembly

Purpose: fourteen fixtures under
`xevents-internal/tests/boundary/fixtures/` covering every G5
failure mode from ADR 0013 §5 plus branch-protection refusal plus
correction propagation.

### Fixture contract (applies to every fixture below)

Each fixture is a directory under
`xevents-internal/tests/boundary/fixtures/<NN-slug>/` containing:

- `observations.jsonl` — synthetic private-side inputs.
- `denylist-state.json` — which ws3 denylist entries this fixture
  references (canonical, aliases, homoglyph table version).
- `expected-outcome.json` — the expected G5 outcome fields.
- `README.md` — which failure mode this fixture targets and which
  ADR section it maps to.

Creating a fixture means: create the directory, populate all four
files, and commit them together. The corpus completeness test (end
of this work stream) fails on any incomplete fixture.

### Fixture list

- [ ] **Fixture 01 — Trivial pass:** aggregates with vocabulary-only
      free-text fields. Expected `outcome: pass, matches: 0,
      pushes_to_public: true, files_pushed: 3`.
- [ ] **Fixture 02 — Exact-name match:** aggregate row with
      `syn-org-001`'s canonical name verbatim. Expected `outcome:
      quarantine, match_rule: exact_substring, scan_target:
      aggregate_row`.
- [ ] **Fixture 03 — Cyrillic homoglyph:** `syn-org-001`'s
      canonical name with every Latin letter replaced by its
      Cyrillic confusable per `homoglyphs.jsonl` v1.0.0. Expected
      `outcome: quarantine, match_rule: normalized_substring,
      normalization: cyrillic`.
- [ ] **Fixture 04 — Greek homoglyph:** analogous with Greek
      confusables. Expected `normalization: greek`.
- [ ] **Fixture 05 — Mixed-script:** one Latin letter swapped to
      Cyrillic in an otherwise Latin canonical name. Expected
      `normalization: mixed_script`.
- [ ] **Fixture 06 — Alias match:** aggregate row contains one of
      `syn-org-001`'s aliases (not the canonical form). Expected
      `match_rule: alias_substring, matched_entity: syn-org-001`.
- [ ] **Fixture 07 — Threat-actor brand:** aggregate row contains
      `syn-actor-001`'s canonical name. Expected `entity_class:
      threat_actor`.
- [ ] **Fixture 08 — Malware-family name:** aggregate row contains
      `syn-malware-001`'s canonical name. Expected `entity_class:
      malware_family`.
- [ ] **Fixture 09 — URL destination poisoning:** requires the
      mock HTTP harness (see task below) serving a body containing
      `syn-org-001`'s canonical name; aggregate row's
      `vendor_advisories` references the mock URL. Expected
      `match_rule: url_destination, scan_target: url_body,
      fetch_outcome: 200`.
- [ ] **Fixture 10 — URL unreachable:** aggregate row references a
      URL the mock harness deliberately 404s or times out.
      Expected `outcome: quarantine, url_fetch_outcome:
      unreachable`.
- [ ] **Fixture 11 — Manifest-row name leak:** aggregates clean;
      one `evidence-manifest.jsonl` row's `source_ref` contains
      `syn-org-001`'s canonical name. Expected `scan_target:
      manifest_row`.
- [ ] **Fixture 12 — Coverage-boundary statement name leak:**
      aggregates clean; synthetic
      `coverage-boundary-statement.md` payload contains
      `syn-actor-001`'s canonical name. Expected `scan_target:
      coverage_boundary_statement`.
- [ ] **Fixture 13 — Boundary write-set violation:** aggregates
      clean (G5 would pass); synthetic write set targets `docs/` (a
      fourth path outside the boundary write set). Expected one of
      two outcomes (per ADR 0014 §Mechanics):
      `outcome: refused_pre_flight` (private-side pre-flight check
      exits before opening a PR, `pr_opened: false`,
      `merge_attempted: false`), OR
      `outcome: refused_by_required_check` (PR opened,
      `boundary-write-set-in-diff` status check red,
      `merge_api_response_code: 4xx`, `commit_landed_on_main: false`).
      Both satisfy AC1.3. `g5_ran: true` in both paths (G5 runs
      before either refusal fires).
- [ ] **Fixture 14 — Correction propagation:** fixture 01
      aggregates plus one `correction_event` row (`event_type:
      dispute_opened`, pre-vetted-vocabulary `note` only). Expected
      `outcome: pass, corrections_in_aggregate: 1,
      correction_event_type: dispute_opened`.

### Mock URL harness

- [ ] Implement a mock HTTP server harness at
      `xevents-internal/tests/boundary/mock_url_server.py` (or
      equivalent) that: serves controlled bodies at controlled
      URLs; supports 404 and timeout responses; is invocable from
      the CI job that runs the corpus. Fixtures 09 and 10 depend
      on this harness.

### Fixture corpus verification

- [ ] Write `xevents-internal/tests/boundary/test_corpus.py` (or
      equivalent) that:
  - [ ] Enumerates the fixture directory set.
  - [ ] Asserts exactly fourteen directories exist.
  - [ ] Asserts each has the four required files.
  - [ ] Asserts each `expected-outcome.json` parses.
  - [ ] Cross-references the fixture list against the public
        plan's M1 corpus enumeration (matches ACP1.5).

**AC coverage:** ACP1.5 (corpus completeness). Enables ws5, ws11.

---

<a id="ws5"></a>

## 5. G5 gate implementation

Purpose: the name-scan gate itself, per ADR 0013. Lives in the
private repo (it reads the derived denylist and homoglyph table).

- [ ] Create `xevents-internal/g5/` package directory with
      `__init__.py`.
- [ ] Implement `g5/normalize.py` per ADR 0013 §3: Unicode NFKC,
      case fold, homoglyph substitution using the table version
      pinned in `denylist-state.json`.
- [ ] Implement `g5/denylist.py` per ADR 0013 §2 and the derivation
      procedure from ws3: derive at run time from
      `denylist/static.jsonl` + entity+alias state; return
      byte-deterministic output; capture size and version.
- [ ] Implement `g5/match_rules.py` per ADR 0013 §4:
  - [ ] `exact_substring`
  - [ ] `normalized_substring` (after normalize.py)
  - [ ] `alias_substring` (matches any alias, records the entity)
  - [ ] `token_match` if ADR 0013 §4 defines it (verify)
- [ ] Implement `g5/url_fetch.py` per ADR 0013 §5:
  - [ ] Fetch URL with timeout (say, 15s) and max response size
        (say, 5 MB).
  - [ ] In-batch dedup: same URL appearing twice in one batch is
        fetched once (AC1.12).
  - [ ] Hash the fetched destination.
  - [ ] Return `{status, hash, body_or_null}`.
  - [ ] On timeout/error: return `{status: unreachable}`; the
        caller quarantines (fail-closed).
- [ ] Implement `g5/scan.py` — the main entry point:
  - [ ] Loads the batch (aggregates + manifest + statement).
  - [ ] Derives the denylist (calls `denylist.py`).
  - [ ] Scans every value in every scan target using match_rules.
  - [ ] For URL fields (`vendor_advisories`, `mitigation_refs`):
        fetches destinations, scans fetched bodies.
  - [ ] Returns a G5 report object.
- [ ] Implement `g5/report.py` — writes the G5 report to
      `g5-reports/<batch-id>.json` per ADR 0013 §9:
  - [ ] `batch_id`, `scan_timestamp`, `denylist_size`,
        `denylist_version`, `homoglyph_table_version`.
  - [ ] `scan_targets: {aggregate_rows: N, manifest_rows: N, urls: N}`.
  - [ ] `url_fetch: {fetched: N, failed: N, matched: N}`.
  - [ ] `matches: []` — each match has denylist-entry-hash,
        match_rule, scan_target, match_position.
  - [ ] `outcome`: `pass` | `quarantine` | `refused_pre_flight` |
        `refused_by_required_check`.
- [ ] Implement `g5/schema.py` — JSON Schema for the report.
- [ ] Write unit tests under `tests/g5/`:
  - [ ] `test_normalize.py`: NFKC, case fold, Cyrillic/Greek/mixed
        substitution.
  - [ ] `test_denylist.py`: determinism (two calls, same bytes);
        derived from static + entity state.
  - [ ] `test_match_rules.py`: every match rule with positive and
        negative fixtures.
  - [ ] `test_url_fetch.py`: dedup within batch; unreachable path;
        timeout path.
  - [ ] `test_scan.py`: end-to-end against every corpus fixture.
  - [ ] `test_report.py`: report conforms to schema for both
        `pass` and `quarantine` outcomes.
- [ ] Achieve 100% coverage on `g5/*.py` files (this is
      load-bearing security code; coverage below 100% is a defect).
- [ ] Write `g5/README.md` explaining the module structure and how
      to add a new match rule (with the ADR-supersession
      requirement noted).

**AC coverage:** AC1.6 (report schema), AC1.11 (derivation
determinism), AC1.12 (URL-fetch instrumentation), ACP1.3
(derivation reproducibility). Enables ws6, ws11.

---

<a id="ws6"></a>

## 6. Boundary workflow implementation

Purpose: `.github/workflows/publish-boundary.yml` in
`xevents-internal` — the workflow the App key authenticates for
and that G5 gates.

- [ ] Create `xevents-internal/.github/workflows/publish-boundary.yml`.
- [ ] Set trigger: `workflow_dispatch` with a required `batch_id`
      input.
- [ ] Set `permissions`: minimum — the workflow does not use the
      workflow-native `GITHUB_TOKEN`; it uses the App installation
      token instead. Set `contents: read` for the checkout only,
      revoke everything else.
- [ ] Add the checkout step (public checkout only).
- [ ] Add a step that loads the batch from
      `tests/boundary/fixtures/${{ inputs.batch_id }}/` (in M1;
      M3+ this will load from live ingest state instead).
- [ ] Add a step that runs G5:
  - [ ] Invoke `python -m g5.scan --batch-id ${{ inputs.batch_id }}
        --output g5-reports/${{ inputs.batch_id }}.json`.
  - [ ] Capture the exit code and outcome from the report.
- [ ] Add a step that writes the machinery-invariants report (see
      ws8) regardless of G5 outcome.
- [ ] Add a step that computes the boundary-write-set-in-diff
      locally, before touching the App token: read the three-path
      write set from `AGENTS.md`, list the files the workflow is
      about to write, and exit non-zero if any file lies outside
      the write set. This is the private-side pre-flight of the
      GitHub-side required status check.
- [ ] Add a conditional step (only when G5 outcome is `pass` AND
      the local diff-check passed) that:
  - [ ] Generates an App installation token by signing a JWT with
        `XEVENTS_BOUNDARY_APP_KEY`.
  - [ ] Exchanges the JWT for a public-repo installation token
        scoped to `XEVENTS_BOUNDARY_INSTALL_ID_PUBLIC`.
  - [ ] Uses the token to create branch `boundary/${{ inputs.batch_id }}`
        on `xevents` from the current tip of `main`.
  - [ ] Uses the token to commit the three boundary-writable files
        (`data/aggregates/*.jsonl`, `evidence-manifest.jsonl`,
        `coverage-boundary-statement.md`) to that bot branch, with
        author `xevents-boundary[bot]`.
  - [ ] Uses the token's `pull_requests: write` scope to open a PR
        from `boundary/${{ inputs.batch_id }}` to `main` on
        `xevents`. PR body includes the G5 report JSON (or a
        commit-scoped link to it) so the required status check
        `g5-report-present-and-valid` can inspect it.
  - [ ] Polls the PR's status-check state (bounded wait, hard
        timeout). On all-green, calls the merge API with
        `merge_method: squash`. Deletes the bot branch after merge.
  - [ ] On any required check failing or the merge API returning
        4xx, exits the workflow non-zero without merging. The
        failed PR is left open with its checks red for the operator
        to inspect (per ADR 0014 §App auto-merge safety).
  - [ ] After successful merge, uses the token's `actions: write`
        scope to dispatch `build-site.yml` on `xevents` (per ADR
        0014 §Mechanics step 6).
- [ ] Add a conditional step (only when G5 outcome is `quarantine`)
      that:
  - [ ] Writes a correction-ledger entry to `correction-ledger/`
        (or the file path per file-layout.md) with `event_type:
        administrative_note`, `note` field containing
        `authority: g5-machinery`, `fixture_id`, `match_rule`,
        `denylist_version`.
  - [ ] Exits the workflow with a non-zero status.
- [ ] Add a step that archives the G5 report under
      `g5-reports/<batch-id>.json` (already written by the G5
      step; this ensures it's committed to the private repo,
      possibly via a second commit-back-to-private-repo step).
- [ ] Write `xevents-internal/docs/publish-boundary-workflow.md`
      documenting the workflow's step ordering and the fail-closed
      structure (the App token generation MUST come after G5, and
      MUST NOT run when G5 outcome is not `pass`).
- [ ] Write a workflow-lint test at
      `tests/boundary/test_workflow_lint.py` that:
  - [ ] Parses `.github/workflows/publish-boundary.yml`.
  - [ ] Asserts G5 step precedes any step that references
        `XEVENTS_BOUNDARY_APP_KEY`.
  - [ ] Asserts the local boundary-write-set-in-diff step
        precedes any step that references `XEVENTS_BOUNDARY_APP_KEY`.
  - [ ] Asserts App-token-using steps have `if: <g5 outcome ==
        pass AND diff-check passed>` conditions.
  - [ ] Asserts the merge API call is guarded on the poll step's
        success (no merge attempt if any required check is red).
  - [ ] Asserts the workflow does not use the workflow-native
        `GITHUB_TOKEN` for any write operation.
- [ ] Verify no `GITHUB_TOKEN` writes and no App-token step lacks
      the outcome-conditional (the lint test enforces this).

**AC coverage:** AC1.10 (fail-closed structure). Enables AC1.1
(trivial-pass merged onto `main`), AC1.2 (quarantine — no PR ever
opened, no bytes on `main`), AC1.9 (machinery-invariants report on
every run). AC1.3 is exercised end-to-end by fixture 13 in ws11.

---

<a id="ws7"></a>

## 7. Public repo branch protection

Purpose: branch protection on `xevents` `main` that enforces the
boundary write set and the G5 result at merge time, per ADR 0014.
This is the GitHub-side layer of the two-layer enforcement (private-
side workflow diff-check in ws6 is the first layer). Because this is
a personal-account public repo, push-time path enforcement and
actor-bypass lists are unavailable on GitHub; required status checks
on a required-PR gate provide the equivalent guarantee at merge
time.

### Branch protection rule on `main`

- [ ] Confirm signed commits are configured on the operator's local
      machine (`git config commit.gpgsign true` or SSH-key signing).
- [ ] `xevents` repo Settings → Rules → Rulesets → New branch
      ruleset. Target: `refs/heads/main`. Enforcement: `Active`.
      Bypass list: empty. Enable the following rules:
  - [ ] `Require signed commits`.
  - [ ] `Require a pull request before merging`. Required approvals:
        0 (solo-operator, machinery-first — required checks are the
        merge gate, not human review). Dismiss stale approvals: off.
        Require review from code owners: off.
  - [ ] `Require status checks to pass before merging`. Require
        branches to be up to date before merging: on. Required
        checks (added after ws9/ws10 wire them into CI):
    - [ ] `boundary-write-set-in-diff`
    - [ ] `g5-report-present-and-valid`
    - [ ] `nygard-immutability`
    - [ ] `docs-qa`
    - [ ] `jsonl-headers`
  - [ ] `Restrict deletions`.
  - [ ] `Block force pushes`.
  - [ ] `Do not allow bypassing the above settings`. Rationale:
        neither the App nor the operator can merge a PR with a red
        required check. This is what makes the boundary write set
        mechanically enforced on `main` (per ADR 0014 §Identity and
        audit).

### Required-check implementations (referenced from CI)

The status checks themselves are implemented by CI jobs in ws9 and
wired to run on PRs to `main` in ws10. For each required check, the
task below verifies the check is reachable from a PR before we mark
it `Required` in the ruleset. If a check name is `Required` before it
can actually run, PRs stall.

- [ ] `boundary-write-set-in-diff`: verify a hand-crafted PR touching
      only `data/aggregates/view1.jsonl` gets a green check; verify a
      hand-crafted PR touching `docs/foo.md` in addition to a
      boundary path gets a red check.
- [ ] `g5-report-present-and-valid`: verify a PR opened by the App
      whose body contains a well-formed G5 report with `outcome:
      pass` gets a green check; verify a PR whose body lacks a G5
      report gets a red check.
- [ ] `nygard-immutability`, `docs-qa`, `jsonl-headers`: verify each
      runs on a PR touching the relevant file class and produces a
      green result when the file is well-formed.

### Test operator-side enforcement

- [ ] From a local branch, open a PR that touches
      `data/aggregates/view1.jsonl` manually. The
      `boundary-write-set-in-diff` check is designed to green-light
      any subset of the three boundary paths, so this PR should pass
      the write-set check. The `g5-report-present-and-valid` check
      should red-light it (no G5 report in the PR body). Confirm the
      PR cannot be merged. Screenshot the merge button in its
      disabled state and save to
      `xevents-internal/machinery-invariants/2026-09-22-manual-boundary-write-blocked.png`.
      This is the mechanical equivalent of the old "operator cannot
      manually touch boundary paths" invariant: they can open the PR,
      but the G5 required check refuses the merge.
- [ ] From a local branch, open a PR that touches `docs/foo.md` (a
      non-boundary path). The write-set check should green-light it.
      The G5 check does not apply to non-boundary PRs (its scope
      guards its own no-op path); operator documentation PRs merge
      normally.

### Test App-side enforcement (deferred to ws11 fixture 13)

Fixture 13 in ws11 exercises the App-side end-to-end: the App opens a
PR whose diff includes `docs/foo.md`, `boundary-write-set-in-diff`
fails, the workflow's merge call returns 4xx, no commit lands on
`main`, workflow exits non-zero. This is the AC1.3 test as revised
under ADR 0014.

### Document the configuration

- [ ] Write `xevents/docs/branch-protection.md` documenting the
      ruleset, the five required status checks, and the AC1.3
      revised interpretation. Cite ADR 0014 §Mechanics and §Identity
      and audit. Include the operator-side screenshot and the
      fixture-13 CI run URL as evidence.

**AC coverage:** AC1.3 revised (merge refused on write-set violation,
via required status check). Enables AC1.1 (trivial-pass fixture PR
merged), AC1.2 (quarantine fixtures — workflow exits before opening
any PR, no bytes on `main`). Cross-supports AC1.16 (operator-verified
attestation captures this ruleset).

---

<a id="ws8"></a>

## 8. Machinery-invariants report

Purpose: a report emitted on every publish attempt capturing the
invariants that are meant to hold. Distinct from the G5 report;
this one records the meta-state.

- [ ] Design the machinery-invariants report schema in
      `xevents-internal/docs/machinery-invariants-report-format.md`:
  - [ ] `publish_attempt_id` — UUID for this attempt.
  - [ ] `timestamp` — ISO 8601.
  - [ ] `fixture_id` (M1 only; empty in M3+ real-data runs).
  - [ ] `boundary_write_set_assertion` — three paths, must equal
        the ADR 0012 §Boundary write set exactly.
  - [ ] `g5_outcome` — mirror of the G5 report outcome.
  - [ ] `g5_report_path` — path to the G5 report for this attempt.
  - [ ] `denylist_size`.
  - [ ] `denylist_version`.
  - [ ] `homoglyph_table_version`.
  - [ ] `naming_policy_sweep_result` (M2+ only; skipped in M1).
  - [ ] `correction_ledger_propagation_result` (from fixture 14
        for M1; a real check in M4+).
  - [ ] `workflow_run_id` — GitHub Actions run reference.
  - [ ] `outcome` — `pass` | `blocked` | `error`.
- [ ] Implement the emitter in `xevents-internal/scripts/emit_machinery_invariants.py`
      that takes the G5 report, adds boundary-write-set state, and
      writes to `machinery-invariants/<publish-attempt-id>.json`.
- [ ] Wire the emitter into `publish-boundary.yml` (as a step that
      runs regardless of G5 outcome — ws6 already added the step
      reference; this task implements the script it calls).
- [ ] Write a schema-validation test at
      `tests/boundary/test_machinery_invariants_schema.py` that
      asserts every emitted report conforms.
- [ ] Write a completeness test at
      `tests/boundary/test_machinery_invariants_completeness.py`
      that asserts: every publish attempt (identified by
      `workflow_run_id`) has a matching report in
      `machinery-invariants/`.

**AC coverage:** AC1.9 (report emitted on every publish).

---

<a id="ws9"></a>

## 9. Cross-cutting invariant CI checks

Purpose: the invariants from the plan's cross-cutting table that
run on every PR to either repo. Some of these were AC1.8, AC1.13,
AC1.14, AC1.15 in the plan.

### Boundary-write-set tri-declaration assertion (AC1.8)

- [ ] Create `tests/invariants/test_boundary_write_set.py` in
      **both** repos.
- [ ] The test:
  - [ ] Fetches the current ADR 0012 body from the public repo
        (in the private-repo test, this means a fetch step).
  - [ ] Parses the three-path list from ADR 0012 §Boundary write
        set.
  - [ ] Parses the same list from private `AGENTS.md`.
  - [ ] Parses the same list from private `docs/file-layout.md`
        §Boundary write verification.
  - [ ] Asserts all three lists are set-equal.
- [ ] Wire the test to run on every PR (see ws10).

### `boundary-write-set-in-diff` required check (AC1.3, per ADR 0014)

- [ ] Create `tests/invariants/test_pr_diff_write_set.py` in the
      public repo. This is the required status check enforced at
      merge on `xevents` `main` (ws7).
- [ ] The test:
  - [ ] Reads the three-path write set from ADR 0012 §Boundary
        write set.
  - [ ] Uses `gh api` (or GitHub Actions event context) to list the
        files the PR changes.
  - [ ] Classifies the PR as boundary-touching if any changed file
        matches a boundary path.
  - [ ] For a boundary-touching PR, asserts every changed file lies
        inside the write set. Fails the check otherwise.
  - [ ] For a non-boundary PR (operator documentation, ADR
        amendment, etc.), the check is a no-op green.
- [ ] Register the CI job under the status name
      `boundary-write-set-in-diff` (this is the exact name marked
      Required in the ws7 ruleset).
- [ ] Add unit tests that construct synthetic PR diffs and assert
      the check classifies and refuses correctly.

### `g5-report-present-and-valid` required check (per ADR 0014)

- [ ] Create `tests/invariants/test_pr_g5_report.py` in the public
      repo. Also a required status check on `main`.
- [ ] The test:
  - [ ] Applies to PRs whose head branch matches `boundary/*`
        (App-opened PRs). Non-boundary PRs are a no-op green.
  - [ ] Reads the PR body via `gh api`.
  - [ ] Extracts the G5 report (a fenced JSON block or a link to a
        commit-scoped file in the PR head).
  - [ ] Validates the report against the G5 schema (ADR 0013 §9).
  - [ ] Asserts `outcome: pass`.
  - [ ] Asserts the report's `batch_id` matches the branch name
        pattern.
  - [ ] Asserts the report's `denylist_version` matches what the
        current private-repo state pins (fetch via `gh api`).
  - [ ] Fails the check on any mismatch.
- [ ] Register the CI job under the status name
      `g5-report-present-and-valid`.
- [ ] Add unit tests: report missing, wrong outcome, malformed
      JSON, mismatched batch_id, stale denylist_version — all should
      red the check.

### JSONL header-row convention (AC1.13)

- [ ] Create `tests/invariants/test_jsonl_headers.py` in the
      private repo.
- [ ] The test:
  - [ ] Enumerates every `.jsonl` file the boundary workflow
        reads or writes: `evidence-manifest.jsonl`,
        `denylist/*.jsonl`, `data/aggregates/*.jsonl`.
  - [ ] Asserts each has a leading metadata header row.
  - [ ] Asserts every reader (`g5/*.py`, aggregation, boundary
        workflow) uses a header-aware parser.
- [ ] Wire it into the private repo's CI on every PR.

### Nygard immutability (AC1.14)

- [ ] Create `tests/invariants/test_nygard_immutability.py` in the
      public repo.
- [ ] The test:
  - [ ] Uses `git diff` against the merge base to detect changes
        to `docs/adr/*.md`.
  - [ ] For each changed ADR whose current body has `Status:
        accepted`, asserts either the change is only in fenced
        comments/metadata OR the diff introduces a
        `superseded by ADR NNNN` line at the top of that ADR.
  - [ ] Adding a new ADR is always allowed.
- [ ] Wire it into the public repo's CI on every PR to `main`.
- [ ] Add a mirror version in the private repo for the two
      accepted-status docs in this repo (`AGENTS.md`,
      `docs/file-layout.md`) — a lighter check that these files
      declare status and never lose the declaration.

### Docs QA per ADR 0010 §4 (AC1.15)

- [ ] Create `tests/invariants/test_docs_qa.py` in both repos.
- [ ] Cross-reference lint sub-check:
  - [ ] Walks every markdown file.
  - [ ] Finds every reference to ADRs (`ADR NNNN`, `docs/adr/*`),
        docs (`docs/*.md`), and file paths.
  - [ ] Asserts each reference resolves to an existing file.
- [ ] Decision-consistency sub-check:
  - [ ] Walks every markdown file.
  - [ ] Finds every occurrence of `TBD`, `UNDECIDED`, `proposed`,
        or `to be decided`.
  - [ ] For each, checks whether it appears in a paragraph or
        sentence that references an ADR whose status is accepted
        or an open-decisions.md entry marked DECIDED.
  - [ ] Fails if any such reference is found.
- [ ] Glossary-term-usage sub-check:
  - [ ] Load the glossary from wherever it lives (per ADR 0010
        §4; verify whether a glossary file exists; if not, this
        sub-check is deferred until one lands and this test is
        updated).
- [ ] Wire the test into both repos' CI on every PR.

### Machinery-first invariant

- [ ] Document in `xevents/docs/machinery-first-audit-procedure.md`:
      any new gate, review, or human step introduced in a PR must
      either be automatable in CI or justified with an
      open-decisions.md entry marked machinery-first-inappropriate.
- [ ] Add a manual reminder in `.github/pull_request_template.md`
      asking the operator to confirm the machinery-first invariant
      is not violated. (This one is a soft check; the plan's
      machinery-first invariant is doctrinal, not fully CI-testable.)

**AC coverage:** AC1.8, AC1.13, AC1.14, AC1.15 (and their
private-side mirrors ACP1.8).

---

<a id="ws10"></a>

## 10. CI wiring on both repos

Purpose: connect the tests written in ws5, ws6, ws8, ws9 to
GitHub Actions so they actually run on every PR and every
scheduled event.

### Public repo CI

- [ ] Create `xevents/.github/workflows/ci.yml`.
- [ ] Trigger: pull_request (all branches), push to main.
- [ ] Jobs:
  - [ ] `docs-qa` — runs `tests/invariants/test_docs_qa.py`.
  - [ ] `nygard-immutability` — runs
        `tests/invariants/test_nygard_immutability.py`.
  - [ ] `boundary-write-set` — runs
        `tests/invariants/test_boundary_write_set.py` (fetches
        the private-repo files it needs via a read-only PAT or
        via GITHUB_TOKEN if the private repo grants read access;
        confirm mechanism at implementation time).
- [ ] Configure branch protection to require these checks to pass
      before merge.

### Private repo CI

- [ ] Create `xevents-internal/.github/workflows/ci.yml`.
- [ ] Trigger: pull_request (all branches), push to main.
- [ ] Jobs:
  - [ ] `docs-qa` — as above.
  - [ ] `nygard-immutability-mirror` — light check on private
        accepted-status files.
  - [ ] `boundary-write-set-mirror` — same test as public.
  - [ ] `jsonl-headers` — runs `tests/invariants/test_jsonl_headers.py`.
  - [ ] `g5-unit` — runs `pytest tests/g5/`.
  - [ ] `g5-corpus` — runs G5 against every fixture in
        `tests/boundary/fixtures/` and asserts each fixture's
        outcome matches its `expected-outcome.json`.
  - [ ] `workflow-lint` — runs
        `tests/boundary/test_workflow_lint.py`.
  - [ ] `machinery-invariants-schema` — runs
        `tests/boundary/test_machinery_invariants_schema.py`.
  - [ ] `corpus-completeness` — runs
        `tests/boundary/test_corpus.py`.
- [ ] Configure branch protection to require these checks to pass
      before merge.
- [ ] Add coverage reporting for `g5/*.py` files; fail CI if
      coverage below 100%.

### Determinism check

- [ ] Add a CI job on the private repo that runs the denylist
      derivation twice, in-memory, and asserts byte-identical
      output (ACP1.3, AC1.11).

**AC coverage:** AC1.11 (derivation determinism in CI), enables all
prior ACs to run on every PR.

---

<a id="ws11"></a>

## 11. End-to-end execution and evidence archival

Purpose: run the boundary workflow against every fixture and archive
the outcomes as evidence.

- [ ] Dispatch `publish-boundary.yml` with `batch_id:
      01-trivial-pass`. Confirm:
  - [ ] G5 report emitted with `outcome: pass, matches: 0`.
  - [ ] Three files pushed to `xevents` `main` by the App.
  - [ ] `build-site.yml` dispatched.
  - [ ] Machinery-invariants report emitted.
  - [ ] Archive the run URL in
        `xevents-internal/machinery-invariants/`.
- [ ] Dispatch with `batch_id: 02-exact-name-match`. Confirm:
  - [ ] G5 report emitted with `outcome: quarantine, matches: >=1`.
  - [ ] No push to `xevents`.
  - [ ] Correction-ledger entry appended.
  - [ ] Machinery-invariants report emitted.
- [ ] Repeat the above dispatch-and-verify for fixtures 03 through
      12. Each run produces:
  - [ ] G5 report with the expected outcome and match rule.
  - [ ] No push (or the correct push for fixture 14).
  - [ ] Correction-ledger entry (for quarantines).
  - [ ] Machinery-invariants report.
- [ ] Dispatch fixture 13 (write-set violation). Under ADR 0014 the
      fixture may be refused at either of two points; either
      satisfies AC1.3 and the fixture assertion records which one
      fired. Confirm one of:
  - [ ] **Path A (private-side pre-flight fires first):** the
        workflow's local `boundary-write-set-in-diff` step (ws6)
        exits non-zero before opening any PR. No branch created on
        `xevents`, no PR opened, no bytes on `main`. Workflow exit
        code non-zero.
  - [ ] **Path B (GitHub-side required check fires):** the workflow
        opens the PR, the `boundary-write-set-in-diff` required
        status check on the PR reports red, the workflow's merge
        API call returns 4xx (captured in workflow log), no commit
        lands on `main`, the failed PR is left open with red checks
        for operator inspection, workflow exit code non-zero.
  - [ ] In either path, correction-ledger entry appended.
  - [ ] In either path, machinery-invariants report emitted with
        `outcome: refused_pre_flight` (Path A) or
        `outcome: refused_by_required_check` (Path B).
- [ ] Dispatch fixture 14 (correction propagation). Confirm:
  - [ ] G5 passes.
  - [ ] Push to `xevents` includes the pre-existing
        `correction_event` in the aggregate's `corrections[]`.
  - [ ] Machinery-invariants report emitted.
- [ ] Compile an evidence table at
      `xevents-internal/machinery-invariants/M1-fixture-run-summary.md`
      with one row per fixture: fixture id, workflow run URL,
      outcome, G5 report path, machinery-invariants report path.
- [ ] Commit the run summary and every emitted report to the
      private repo.

**AC coverage:** AC1.1, AC1.2, AC1.3 (revised, per ADR 0014), AC1.4,
AC1.5 (via fixtures 01, 02–12, 13, quarantine ledger entries, 14
respectively).

---

<a id="ws12"></a>

## 12. Operator-verified attestations

Purpose: the two `[operator-verified]` ACs (AC1.16, ACP1.4) —
things CI cannot reach, so the operator has to leave signed
evidence.

- [ ] Open GitHub UI, navigate to the `xevents-boundary` App page,
      screenshot the "installed on 2 repositories" state.
- [ ] Save the screenshot as
      `xevents-internal/machinery-invariants/2026-09-22-app-installation-confirmation.png`.
- [ ] Confirm `XEVENTS_BOUNDARY_APP_KEY` is set in `xevents-internal`
      Actions secrets. Screenshot the secrets page (the value is
      hidden; only the name is visible). Save as
      `xevents-internal/machinery-invariants/2026-09-22-secret-placement-confirmation.png`.
- [ ] Confirm `XEVENTS_BOUNDARY_APP_KEY` is NOT set in `xevents`
      Actions secrets. Screenshot the empty secrets page (or the
      page without this secret listed). Save as
      `xevents-internal/machinery-invariants/2026-09-22-secret-absence-public-repo.png`.
- [ ] Screenshot the `xevents` branch protection ruleset on `main`
      showing: `Require signed commits`, `Require a pull request
      before merging`, `Require status checks to pass before merging`
      with the five required checks listed by name, `Restrict
      deletions`, `Block force pushes`, `Do not allow bypassing`, and
      empty bypass list. Save as
      `xevents-internal/machinery-invariants/2026-09-22-branch-protection-configuration.png`.
- [ ] Write an attestation note at
      `xevents-internal/machinery-invariants/2026-09-22-M1-operator-attestation.md`:
  - [ ] Date, operator identity, and a signed statement per AC1.16
        and ACP1.4.
  - [ ] Reference to the three screenshots above.
  - [ ] Confirmation that the `.pem` file was deleted from local
        machine after upload to Actions secrets; deletion
        timestamp.
- [ ] Commit the attestation to the private repo.

**AC coverage:** AC1.16, ACP1.4.

---

<a id="ws13"></a>

## 13. M1 exit gate

Purpose: final verification that every M1 AC is satisfied before
declaring M1 done and starting M2.

- [ ] All sixteen public M1 ACs (AC1.1–AC1.16) checked off.
- [ ] All eight private M1 ACs (ACP1.1–ACP1.8) checked off.
- [ ] `xevents-internal/machinery-invariants/M1-fixture-run-summary.md`
      lists all fourteen fixtures with green outcomes.
- [ ] `xevents-internal/machinery-invariants/2026-*-M1-operator-attestation.md`
      committed with all three screenshots.
- [ ] Every cross-cutting invariant CI check (boundary-write-set,
      JSONL headers, Nygard immutability, docs QA) green on the
      current `main` of both repos.
- [ ] `xevents` `main` branch protection ruleset is Active with the
      configuration attested in ws12 (ADR 0014 §Mechanics).
- [ ] G5 unit-test coverage at 100% on `g5/*.py`.
- [ ] Corpus completeness test asserts fourteen fixtures.
- [ ] Machinery-invariants report emitted for every one of the
      fourteen fixture dispatches, archived, and schema-valid.
- [ ] Zero uncommitted changes on either repo's `main`.
- [ ] Zero open PRs blocking M1.
- [ ] Update this checklist file: replace every `- [ ]` with
      `- [x]` and add the commit SHA that closed each work stream
      in a table at the bottom of this document (add the table
      when reaching exit).
- [ ] Open a final "M1 complete" PR that updates `docs/implementation-plan.md`
      with an M1 exit-timestamp annotation (append a small `## M1
      exit record` section at the end of the plan noting the date
      and the summary path).
- [ ] Merge the exit-record PR (independent inspection first per
      standing preference).
- [ ] Begin M2.

**AC coverage:** completeness gate for all of M1.

## Cross-references

- `docs/implementation-plan.md` — the plan this checklist executes.
- `xevents-internal/docs/implementation-plan-private.md` — the
  private-side companion plan.
- `docs/adr/0012-aggregation-boundary-transport.md` — boundary write
  set, rotation, G5 interaction, non-goals (§Mechanics and §Identity
  and audit are superseded by ADR 0014).
- `docs/adr/0014-app-opened-pr-transport.md` — App-opened-PR
  transport, App scopes, branch-protection contract for AC1.3.
- `docs/adr/0013-g5-name-scan-gate.md` — G5 specification.
- `docs/adr/0010-quality-assurance.md` — CI-enforced quality bars.
- `xevents-internal/docs/file-layout.md` — private-repo physical
  layout including the JSONL header-row convention and boundary
  write verification.
