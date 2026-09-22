# Public main branch protection

Status: proposed (pending user redline).

Authority: [M1 execution checklist, WS7](m1-execution-checklist.md#ws7)
and [ADR 0014, Mechanics and Identity and audit](adr/0014-app-opened-pr-transport.md).
This is an implementation record, not an amendment to an accepted ADR.

## Baseline configuration

The versioned [bootstrap payload](branch-protection-bootstrap.json) describes
one repository branch ruleset, `xevents-main`, targeting exactly
`refs/heads/main` in `neilweitzel/xevents`. Its intended enforcement is active.
It contains no exclusions and an empty bypass list. Activation is a separate
operator-approved API operation; a JSON file in Git is not evidence that
GitHub is enforcing its contents.

| Control | Baseline |
| --- | --- |
| Verified commit signatures | Required |
| Pull request before merge | Required |
| Human review approvals | Zero |
| Stale-review dismissal | Off |
| Code-owner review | Off |
| Last-push approval | Off |
| Review-thread resolution | Off |
| Main deletion | Blocked |
| Main force pushes | Blocked |
| Bypass actors | None, including no operator or App exemption |
| Allowed merge methods | Existing merge, squash, and rebase options retained |
| Required status checks | Not configured until WS9/WS10 verification |

The App's eventual transport still uses squash merge as specified in ADR 0014;
retaining repository merge options does not change that transport contract.
The rule set uses the field names and parameters in GitHub's
[repository rules REST API](https://docs.github.com/en/rest/repos/rules).

## Deliberately incomplete boundary enforcement

This baseline is NOT the publication boundary's completed GitHub-side gate.
Signatures and PRs do not prove that a change is name-free, came through G5,
or touches only authorized data paths. Until the checks below exist, boundary
changes are not mechanically blocked by those checks.

WS7 explicitly requires proving each check can run on a PR before marking it
required. Requiring a nonexistent check would stall every PR, including the
PR that introduces its implementation. No dummy success statuses or bypass
actors may be used to work around that dependency.

The five pending required contexts are:

- `boundary-write-set-in-diff`
- `g5-report-present-and-valid`
- `nygard-immutability`
- `docs-qa`
- `jsonl-headers`

After WS9/WS10 validation, add a `required_status_checks` rule with
`strict_required_status_checks_policy: true`, all five contexts, and an
explicit verified producing integration where supported. Do not treat any
writer's same-named status as equivalent to the trusted check. GitHub documents
check-source selection and strict up-to-date behavior under
[available rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).
GitHub's API states that strict mode has no effect without an enabled check;
the bootstrap does not claim up-to-date enforcement.

The boundary publisher stays unavailable under the approved
[WS6 separation](ws6-boundary-separation.md). No public data publication is
authorized by installing this baseline.

## Commit signing and operator access

Protection applies to commits introduced by a PR, not merely a hoped-for
signed squash result. Unsigned PR-head commits can block a squash merge.
Do not disable signature enforcement or add a bypass to merge such a PR;
recreate its changes as verified signed commits, as described in
[GitHub's signed-commit rule](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets).

Two distinct signing paths must not be conflated:

- **GitHub-hosted authoring:** `createCommitOnBranch` creates a commit using
  the authenticated principal. GitHub signs it when supported; verify
  `commit.verification.verified` from the commit API before treating it as a
  usable signing path. This does not require creating or exporting a local key.
  GitHub describes the behavior in its
  [mutation reference](https://docs.github.com/en/graphql/reference/mutations#createcommitonbranch)
  and [signed-commit API announcement](https://github.blog/changelog/2021-09-13-a-simpler-api-for-authoring-commits/).
- **Local operator Git:** separately configure and verify the operator's
  signing key and relevant repository settings before using local commits for
  protected-branch PRs. A global-config check is not proof of every local
  checkout's configuration. This checklist item remains open until an actual
  locally signed commit is verified by GitHub; no local signing setup is
  silently created as part of ruleset activation.

An empty bypass list does not remove the repository owner's administrative
ability to edit rules. The intended guarantee is no configured merge bypass
while this ruleset remains active, not protection against an owner deliberately
changing the policy. Drift checks must read the actual API configuration.

## Verification and activation procedure

1. Read repository rulesets, effective rules for `main`, current main SHA,
   and the five checks' actual availability. Do not overwrite an existing
   ruleset without inspecting and reconciling it.
2. Validate the versioned payload with the offline tests. Prepare a
   documentation-only PR using a verified signed commit.
3. Obtain approval for activation. Create the exact versioned ruleset through
   the API, keeping the bypass list empty. A permission or plan error is a
   blocker, not a reason to weaken settings or broaden the App's permissions.
4. Read back the ruleset by ID and effective `main` rules. Compare all four
   rule types, PR parameters, active enforcement, target, exclusions, and
   bypass list against the payload. Record its GitHub URL and ID in the
   implementation PR's verification record.
5. With merge approval, merge the signed documentation-only PR through the
   ordinary PR path. Verify the merged tree and commit signature. Do not use
   an admin-bypass merge. This is a positive signed-PR test, not a negative
   direct-push, force-push, deletion, or unsigned-commit test.
6. Do not attempt destructive probes against `main`. Any additional test
   branch, negative merge test, or screenshot capture requires a defined
   non-destructive test plan and authorization.

Repository inspection on 2026-09-22, before this increment's activation,
found no rulesets, no effective main rules, and no Actions workflows.
The preceding main commit was verified signed. These observations are a
pre-activation snapshot, not a current-state guarantee.

## Remaining evidence and acceptance criteria

- **Local signing:** still requires an independently verified local signed
  commit; hosted signing is an available alternative, not proof of this item.
- **Five required checks:** implement, run positive and negative PR tests,
  then require them with strict up-to-date policy.
- **Operator boundary-write rejection:** deferred until G5 and write-set
  checks exist. A manual boundary-only PR should fail the G5-report check.
  A documentation-only PR should exercise the scoped no-op behavior.
- **AC1.3 / App fixture 13:** deferred to WS11. The required write-set check
  must fail and GitHub must refuse the App's merge; local refusal alone does
  not prove GitHub-side enforcement.
- **Screenshot and run evidence:** not yet captured. Retain detailed private
  evidence in the private audit location prescribed by the checklist. Do not
  embed private artifacts or internal identifiers in this public document.
- **Full WS7 completion:** not claimed by this bootstrap. Readback and a
  signed documentation merge prove only their specific controls.
