# ADR 0012: Aggregation-boundary transport

- Status: accepted
- Date: 2026-09-21
- Deciders: project lead

## Context

The whole xevents design rests on one control: the public build never
reads the private repo. Raw name-bearing observations live in
`xevents-internal`; only sector-aggregated and technique-aggregated outputs
cross to public `xevents`, after the name-scan gate (G5, ADR 0013 TBD)
asserts zero name matches in the outgoing batch.

Prior ADRs (0009 static-first, 0010 quality assurance, 0011 two-view
surface) reference "the aggregation boundary" without specifying how bytes
actually cross it. This ADR specifies the transport.

The choice of transport is load-bearing for two reasons:

1. **Blast radius on credential compromise.** Whatever credential
   authorizes the private-to-public write is a bypass for G5 if it
   leaks. The tighter the credential's scope, the smaller the bypass.
2. **Auditability.** Every public-repo commit must be distinguishable
   between "the operator pushed this manually" and "the boundary pipeline
   pushed this." Manual commits should not run through the boundary
   machinery; boundary commits should not look like manual commits.

## Decision

The aggregation boundary uses a **GitHub App** with a scoped installation
on both `xevents` and `xevents-internal`.

### Mechanics

- A GitHub App named **xevents-boundary** is registered under the project
  lead's account.
- The app is installed on exactly two repositories: `xevents` and
  `xevents-internal`. Installation is scoped, not org-wide.
- The app has the minimum permission set required:
  - `contents: write` on both repos (write the aggregate JSONL and the
    evidence manifest; read source docs during builds)
  - `actions: write` on `xevents` (dispatch the public build workflow
    after pushing aggregates)
  - `metadata: read` (baseline)
  - No other scopes. No `pull_requests`, no `issues`, no `packages`,
    no `workflows`.
- The app's private key is stored as a GitHub Actions secret in
  `xevents-internal` only. The public repo never holds the key.
- Boundary workflow runs inside `xevents-internal`. It generates an
  installation access token at run time (JWT signed with the app's private
  key, exchanged for an installation token scoped to the two-repo
  installation), pushes aggregates to `xevents`, then dispatches the
  public build workflow via `workflow_dispatch`.

### Identity and audit

- Commits authored by the boundary appear in `xevents`'s log as
  **`xevents-boundary[bot]`**, a distinct principal from the project
  lead's personal commits. This is the mechanical distinction that
  separates boundary-mediated changes from manual commits.
- The public repo's branch protection rules require:
  - Manual commits to protected branches allowed only from the project
    lead's account.
  - Boundary-authored commits allowed only when signed by the app
    installation and only against paths in the **boundary write set**
    (below). Any path outside that set fails the branch-protection check.

### Boundary write set

The initial tight rule. Boundary-authored commits may write to:

- `data/aggregates/` — the JSONL aggregate files (view 1 and view 2)
- `evidence-manifest.jsonl` — the append-only manifest of source hashes
- The coverage-boundary statement file (path pinned in
  `docs/dashboard-spec.md`)

Nothing else. The boundary cannot touch docs, ADRs, workflow files,
`AGENTS.md`, or any other path. A boundary commit that attempts to write
outside this set fails the branch-protection check; the workflow logs the
attempted paths and quarantines the batch as a severity-1 incident
(ADR 0010 §3).

**The write set is expected to be amended as the workflow is built.**
When the workflow legitimately needs a new path (e.g. a build timestamp
file, a search index shard directory), the addition is a small amendment
to this ADR — not a new ADR, and not a suspension of the rule. The
discipline is: the write set stays as narrow as the workflow's actual
needs, and every widening is explicit.

### Private-repo workflow isolation

The private repo's boundary workflow is the only workflow with access to
the app's private key. Other private-repo workflows (ingest, review,
internal aggregation) run under `GITHUB_TOKEN` scoped to the private repo
alone.

### Rotation

- The app's private key is rotated on a 12-month calendar cadence,
  recorded in an operations log entry. Emergency rotation follows the
  incident-response ADR (0010 §3).
- Key rotation is one action: regenerate the key in the app settings,
  update the `xevents-internal` secret. No code changes, no ADR
  amendments, no coordination with the public repo.

### G5 interaction

- G5 runs inside the boundary workflow, *before* the aggregate is pushed
  to the public repo. A G5 failure quarantines the batch and prevents
  the push; the app installation token is never used for a batch that has
  not passed G5.
- G5 specification is ADR 0013 (TBD). This ADR does not specify G5; it
  specifies that G5 is the only gate that decides whether the boundary
  workflow uses its credential.

## Alternatives considered

### Alternative A — Fine-grained personal access token (PAT)

- The private-repo boundary workflow uses a fine-grained PAT scoped to
  `xevents` with contents:write.
- **Rejected because:** the PAT is tied to the project lead's account.
  Its blast radius on compromise is everything that account can touch on
  GitHub, not two repos. Audit logs show boundary commits as
  authored by the lead — indistinguishable from manual commits.
- **Fallback path:** if the GitHub App proves to be more setup friction
  than value, a fine-grained PAT is an accepted migration-back option,
  documented here so it does not require a new ADR to authorize.
  Migration back requires a new operations-log entry and an amendment
  to this ADR's status section.

### Alternative B — Cross-repo `workflow_run` artifact hand-off

- Private workflow uploads the aggregate as a GitHub Actions artifact;
  a workflow in the public repo, triggered by cross-repo `workflow_run`,
  downloads and commits it.
- **Rejected because:** cross-repo `workflow_run` triggering is
  awkward in practice — the trigger permission model is repository-
  scoped in ways that don't match a two-repo boundary. Adds a moving
  part (the artifact API) without corresponding audit gain over the
  App path.

### Alternative C — Deploy key or SSH key

- SSH deploy key on `xevents` with write access, private half held by
  `xevents-internal`.
- **Rejected because:** deploy keys are per-repo but not per-app;
  they don't provide the distinct-principal audit signal a GitHub App
  gives, and they carry the same "commit looks like the operator did it
  manually" problem as a PAT.

## Consequences

- Setup requires registering the GitHub App and installing it on both
  repos before the boundary workflow can be built. A one-time ~30-minute
  task, done once before any code lands.
- Two secrets management surfaces to remember: the app's private key
  (in `xevents-internal`), and the branch protection rules (in `xevents`
  settings). Both are documented in a `docs/boundary-operations.md` file
  (added in a subsequent PR when the workflow is built).
- The boundary workflow becomes the *only* mechanism by which aggregates
  reach the public repo. Manual commits touching aggregate paths on the
  public repo are blocked by branch protection, which is intentional —
  a manual commit that bypasses the boundary bypasses G5.
- The project lead's personal account can still push documentation and
  ADR changes to the public repo manually; those commits are visible in
  the log as the lead's own, distinct from boundary commits.

## Non-goals

- Cross-organization installation. The app is installed on the project
  lead's two personal repos. Extending to organization ownership is a
  future migration, not this ADR.
- Signing commits with a GPG key held by the app. Optional; the app's
  bot identity is sufficient audit signal for MVP. Signed commits from
  the app are a hardening to revisit post-launch.
- Multi-writer boundaries. Only one workflow (the private repo's
  boundary workflow) is authorized to use the app's credential. Additional
  writers require an ADR amendment.

## Research basis

- GitHub App scoping and installation-token semantics
  (`https://docs.github.com/en/apps`).
- Branch protection path-based checks
  (`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`).

## Related

- Depends on ADR 0011 (defines what crosses the boundary: view 1 and
  view 2 aggregates plus the evidence manifest).
- Blocks ADR 0013 (G5 name-scan gate) — G5 is the gate the boundary
  workflow honors; ADR 0013 says what G5 does; this ADR says what
  happens when G5 passes.
- Blocks `docs/boundary-operations.md` — the runbook for standing up
  the app, rotating the key, and revoking on incident.
- Superseded-note target: this ADR is where the fine-grained PAT
  fallback would be recorded if migration back is ever authorized.
