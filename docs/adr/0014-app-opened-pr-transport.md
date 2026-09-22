# ADR 0014: App-opened PR transport

- Status: accepted
- Date: 2026-09-22
- Deciders: project lead
- Supersedes: 0012 §Mechanics, 0012 §Identity and audit

## Context

ADR 0012 specified the aggregation-boundary transport as a GitHub App
that pushes aggregates directly to `xevents`'s `main` branch, with
GitHub branch protection refusing any commit that touches a path
outside the boundary write set. During M1 execution, an audit of every
mechanism claim against GitHub's actual behavior on the target
infrastructure revealed that direct-push path enforcement is not
available:

- `neilweitzel/xevents` is a public repository on a personal Free
  account. GitHub push rulesets — the only mechanism that restricts a
  push by file path — are not available on public repositories on any
  plan. GitHub product statements confirm "push rules are not
  applicable to any public repos" and there is no roadmap to add
  support (community discussion
  `https://github.com/orgs/community/discussions/118843`).
- Classic branch protection's "Restrict who can push" feature —
  the only mechanism that restricts pushes by actor — requires the
  repository to belong to an organization. On personal-account repos
  it is not available, per GitHub docs on About protected branches:
  "Actors may only be added to bypass lists when the repository
  belongs to an organization."

The two missing features are both load-bearing for ADR 0012 §Identity
and audit's claim that "Boundary-authored commits allowed only when
signed by the app installation and only against paths in the boundary
write set." Neither the path constraint nor the actor constraint can
be enforced at the GitHub API layer for direct pushes to `xevents`.

`neilweitzel/xevents-internal` is a private repository on the same
Free plan. Branch protection and rulesets are not available on
Free-plan private repos at all (community discussion
`https://github.com/orgs/community/discussions/174419`). This affects
private-repo enforcement claims but is orthogonal to the transport;
the private repo does not host the public output.

The load-bearing properties of ADR 0012 remain valid — machinery-first
enforcement, boundary write set as the tight rule, distinct-principal
audit signal, G5 as the sole gate that authorizes credential use.
Only the transport mechanism has to change to fit the platform.

## Decision

The aggregation boundary uses a **GitHub App that opens pull requests
against `xevents`'s `main`**, rather than pushing directly. Merges are
gated by required status checks that enforce the boundary write set
and the G5 result. The App auto-merges its own PRs once the required
checks pass.

### Mechanics (supersedes ADR 0012 §Mechanics)

- The GitHub App `xevents-boundary` remains registered under the
  project lead's account and installed on both `xevents` and
  `xevents-internal`.
- App scopes (revised from ADR 0012):
  - `contents: write` on both repos (unchanged; needed to create the
    bot branch and commit aggregates to it).
  - `pull_requests: write` on `xevents` (added; needed to open and
    merge the PRs that are now the transport surface).
  - `actions: write` on `xevents` (unchanged; the App still dispatches
    the public build workflow after a merge lands).
  - `metadata: read` (unchanged).
  - Nothing else. In particular: no `issues`, no `packages`, no
    `workflows`. The `pull_requests: write` addition is a scope
    widening; the boundary write set (see ADR 0012 §Boundary write
    set) still constrains what the App can land through those PRs.
- The App's private key is stored as a GitHub Actions secret in
  `xevents-internal` only. Unchanged from ADR 0012.
- The boundary workflow (`xevents-internal/.github/workflows/publish-boundary.yml`)
  runs on `workflow_dispatch`, and:
  1. Loads a batch, derives the denylist, runs G5. On G5 failure the
     workflow exits non-zero, no PR is opened, no bytes cross.
  2. On G5 pass, generates an installation access token, creates a bot
     branch `boundary/<batch-id>` on `xevents`, commits the three
     boundary write set files with `xevents-boundary[bot]` as author,
     pushes the branch.
  3. Opens a PR from `boundary/<batch-id>` to `main` on `xevents` with
     a PR body that includes the G5 report summary and the batch id.
  4. Waits for required status checks on the PR to go green
     (`boundary-write-set-in-diff`, `g5-report-present-and-valid`,
     plus the cross-cutting invariant checks).
  5. Merges the PR via the merge API using the same installation
     token. Merge method: squash-merge. Deletes the bot branch after
     merge.
  6. Dispatches the public build workflow via `workflow_dispatch`.
- If any required check fails, the merge API returns 4xx and the
  workflow exits non-zero. No bytes reach `main`.

### Identity and audit (supersedes ADR 0012 §Identity and audit)

- PR authorship and commit authorship on the bot branch are both
  `xevents-boundary[bot]`. This preserves the distinct-principal audit
  signal from ADR 0012: every boundary-mediated change on `main`
  arrives via a merged PR authored by the App, distinct in `git log`
  from the project lead's manually authored commits.
- `xevents` branch protection on `main` enforces:
  - `Require a pull request before merging`.
  - `Require signed commits`.
  - `Require status checks to pass before merging`. Required checks:
    - `boundary-write-set-in-diff` — inspects the PR's changed file
      list, fails if any changed path is outside the boundary write
      set declared in `xevents-internal`'s `AGENTS.md`.
    - `g5-report-present-and-valid` — inspects the PR body (or a
      linked commit) for a G5 report that conforms to ADR 0013 §9 and
      reports `outcome: pass`.
    - The cross-cutting invariant checks from ADR 0010 §4 (Nygard
      immutability, docs QA, JSONL header rows), scoped to what
      applies to a boundary PR.
  - `Do not allow bypassing the above settings` — on. Neither the
    project lead nor the App can merge a PR with a failing required
    check. In particular, admin cannot bypass. This is what makes the
    write set mechanically enforced.
- Required-review-approval count on `main` is set to 0. The App
  auto-merges its own PRs. Human PRs from the project lead's account
  merge without review as well; the mechanical gate is the required
  status checks, not human review. This is consistent with the
  solo-operator context and preserves machinery-first execution.

### Boundary write set enforcement (references ADR 0012 §Boundary write set)

The boundary write set list is unchanged from ADR 0012 (`data/aggregates/`,
`evidence-manifest.jsonl`, `coverage-boundary-statement.md`). What
changes is the enforcement mechanism: instead of a push-time
GitHub-side path check on direct pushes, enforcement lives in the
`boundary-write-set-in-diff` required status check that runs on every
PR to `main`. A PR (from the App or a human) with a changed path
outside the write set fails the check and cannot be merged.

The tri-declaration invariant from AC1.8 (write set stated in ADR
0012, private `AGENTS.md`, and private `docs/file-layout.md`, all
three asserted identical by CI) remains the source of truth. The
required status check reads from `AGENTS.md`.

### Manual commits (revises ADR 0012 §Identity and audit's manual-commit clause)

The original ADR 0012 clause "Manual commits to protected branches
allowed only from the project lead's account" was implementable on an
organization repo but is not on a personal-account repo. In this
environment the equivalent guarantee is:

- The `xevents` repository has the project lead as its only
  collaborator with push access. Push access is a repository-level
  setting, not a branch-protection setting; it does not require
  org-owned repos.
- Every direct push and every PR merge must pass required status
  checks (no bypass). Both the project lead and the App face the same
  gate.
- Manual commits from the project lead's account that would touch a
  boundary write set path fail the `boundary-write-set-in-diff` check
  on their PR, just like a defective App PR would. The mechanical
  effect is symmetric.

### App auto-merge safety

- The App merges only PRs that:
  1. Were opened from a branch named `boundary/<batch-id>`.
  2. Have all required checks green.
  3. Have as their commit author `xevents-boundary[bot]`.
- The merge step is the last thing the boundary workflow does before
  dispatching the build. If any of the three preconditions fails, the
  workflow exits non-zero without calling merge.
- The App has no scope to merge PRs not opened by itself. A human PR
  to `xevents` merges through the project lead's normal Git flow, not
  the App's merge path.

### G5 interaction (unchanged from ADR 0012 §G5 interaction)

G5 runs inside the boundary workflow, before the PR is opened. G5
failure means no PR, no commit on the bot branch, no merge. G5 is
still the only gate that decides whether the App's credential is used
at all. The G5 result also lands in the PR body so the
`g5-report-present-and-valid` required status check can inspect it.

### Private-repo workflow isolation (unchanged from ADR 0012)

The private repo cannot host branch protection on Free plan. The
boundary workflow's own exit code is the private-side gate: a defective
batch is caught by G5, by the boundary-write-set-in-diff step run
locally in the workflow before the PR is opened, or by both. CI on the
private repo runs the corpus and asserts the workflow's decisions on
every fixture. This mirrors the guarantee GitHub-side branch
protection would give and is what M1 verifies against the adversarial
corpus.

### Rotation (unchanged from ADR 0012)

Twelve-month cadence, one-action rotation, `xevents-internal` secret
update. The added `pull_requests: write` scope is set at App
registration and does not affect rotation.

## Consequences

- The App's scope widens by one (`pull_requests: write`). This is a
  strictly larger blast radius than ADR 0012 anticipated, but
  restricted to `xevents` only, and constrained by the same boundary
  write set — the App cannot use its PR permission to land content
  outside the write set, because the required status checks refuse to
  merge such a PR.
- Each batch produces one PR, one merge commit, one bot-branch delete,
  and one build dispatch. `git log --author=xevents-boundary[bot]` on
  `main` shows one merge commit per batch instead of one push per
  batch. Squash-merges keep the log clean.
- Setup requires configuring branch protection on `main` with three
  required checks. Documented in `docs/branch-protection.md` (added
  during M1 execution).
- If GitHub adds push rulesets for public repos, migration back to a
  direct-push model is straightforward: add the push ruleset, remove
  `pull_requests: write` from the App, replace the PR-opening steps
  in the workflow with a direct push. The App itself does not need to
  be re-registered.
- If `xevents` is later moved into a GitHub organization on a paid
  plan, this design remains optimal. Push rulesets on public repos
  still would not be available; the PR-based flow is the same on org
  repos as on personal repos. The only change would be that org repos
  gain `Restrict who can push` and bypass actor lists as additional
  hardening; those become supplementary, not replacements for the
  status-check enforcement.

## Alternatives considered

### Alternative A — Weaken AC1.3 to workflow-internal enforcement only

- The boundary workflow inspects the diff before pushing directly to
  `main`, refuses to push on a fourth path, exits non-zero.
- **Rejected because:** the guarantee is "the App promises not to push
  a fourth path" rather than "GitHub refuses to merge a fourth path."
  The M1 doctrine — mechanically enforced boundary — is weakened. A
  buggy workflow could push anyway. The App-opened-PR path preserves
  the mechanical guarantee via GitHub-side status checks.

### Alternative B — Move `xevents` into an organization on GitHub Team

- Team plan grants `Restrict who can push` on org-owned repos, which
  gives back part of the original ADR 0012 design.
- **Rejected because:** push rulesets on public repos remain
  unavailable on Team, so the path-based enforcement still requires
  the required-status-check flow. Moving to an org buys nothing that
  the PR-based flow does not already provide, and adds recurring cost
  plus a migration step.

### Alternative C — Make `xevents` a private repo, upgrade to Pro

- Push rulesets become available on private repos on Team+; on Pro
  they still are not.
- **Rejected because:** `xevents` is the public-consumption face of
  the project (GitHub Pages hosts the site). Making it private
  defeats the goal.

## Non-goals

- Signing commits with the App's own GPG key. Optional hardening,
  same status as under ADR 0012.
- Human review approval on boundary PRs. The design is
  machinery-first; the required checks are the merge gate, not
  human review. A future amendment could add required reviews on
  human-authored PRs while keeping the App's auto-merge path, but
  that is not part of M1.
- Direct-push transport if GitHub adds public-repo push rulesets.
  Documented in Consequences as a migration path, not committed.

## Research basis

- GitHub push ruleset availability
  (`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/managing-rulesets-for-a-repository`).
- GitHub branch protection actor bypass limits, org-only
  (`https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-protected-branches/about-protected-branches`).
- GitHub Free-plan private repo branch protection unavailability
  (`https://github.com/orgs/community/discussions/174419`).
- Public-repo push rules not planned
  (`https://github.com/orgs/community/discussions/118843`).
- GitHub App PR-open and PR-merge semantics
  (`https://docs.github.com/en/rest/pulls/pulls`).

## Related

- Supersedes: ADR 0012 §Mechanics, §Identity and audit. ADR 0012's
  §Boundary write set, §Rotation, §G5 interaction, §Private-repo
  workflow isolation, and §Non-goals remain in force and are cited
  by this ADR.
- Depends on ADR 0013 (G5 name-scan gate). G5 is unchanged; its
  output is now consumed by the `g5-report-present-and-valid`
  required status check.
- Depends on ADR 0010 §4 (docs QA / cross-cutting invariants). The
  three required checks include the cross-cutting invariant checks
  from that ADR.
- Blocks the M1 execution checklist rewrite of work stream 7 (branch
  protection) and additions to work stream 6 (boundary workflow).
