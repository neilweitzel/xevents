# Public-safe publication proof: adversarial test plan

Status: proposed (pending user redline)

## Scope and execution status

This is the test-design companion to
[ADR 0019](adr/0019-public-safe-g5-proof-contract.md).
All case IDs below are PLANNED, NOT EXECUTED. Existing regression tests remain
separate; their passing results do not establish implementation of these cases.
There is no new proof verifier, signing key, producer or workflow in this change.

Revision 2026-09-23 changes the expected enforcement model, not execution status.
PP-53 through PP-62 now distinguish native merge controls, workflow checkpoints
and explicitly accepted residual races. A stale manual merge may be possible;
a test must report it truthfully, not count it as mechanically prevented.
The operator approved revised D6 as the design direction on 2026-09-23.
This records acceptance of its timing limits, not executed tests, full-contract
acceptance, merge permission or implementation/activation authorization.

The plan serves the M1 G5/transport acceptance criteria and public required proof
check described in [the implementation plan](implementation-plan.md).
It keeps private report material private and never treats a syntactically valid
`pass` claim, signature alone, or green unit suite as release authorization.

## Harness contract

Use only synthetic, explicitly non-production keys and inert public-shaped data.
No connected credential, real private record, real URL fetch, App permission,
production signing operation, workflow dispatch or public boundary write is
needed for offline stages.

The future harness supplies a fake clock, bounded public API/Git-object reader,
trusted policy snapshot, private-producer fixture receipt and a spy for every
credential/sign/write/merge/build/deploy operation. Candidate content is data,
never code. Admission and deployment are separate entry points; mock provider
acceptance and completion separately so in-flight race limits can be tested.
Generate a minimal valid proof from a known-good fixture, mutate one condition
per negative test, and recompute/re-sign only when the case requires testing
semantic validation rather than signature failure.

Golden data must include explicit expected canonical bytes, domain-separated
message bytes, candidate digest, public key and signature. Expected values must
be independently generated or externally validated, not derived solely by the
implementation under test. Public synthetic keys must never enter the trusted
production registry. Include RFC 8032 known-answer verification and RFC 8785
canonicalization cases from the references in ADR 0019.

Result vocabulary for the future harness:

- VALID: attestation valid at check time only, not publication authorized.
- REJECT: malformed/unauthorized/stale/mismatched evidence, nonzero result.
- BLOCKED: dependency, trusted time, API completeness or platform guarantee is
  unavailable, nonzero result.
- NO-SIGN/NO-WRITE/NO-MERGE/NO-DEPLOY: assertions that the controlled component
  submitted no corresponding operation; never infer provider-side nonexecution
  merely from a timeout or cancellation after submission.
- RESIDUAL-OBSERVED: a deliberately exercised, explicitly documented window,
  not VALID or a prevented incident. Record any actual merge/deployment.

Every case requires a zero-skip assertion. Public diagnostic output must contain
only fixed codes and allowed public identifiers. Fixture canaries must be absent
from logs, exceptions, generated body, branch metadata and API writes.

## Parser, canonicalization and cryptography

| ID | Mutation or scenario | Required outcome |
|---|---|---|
| PP-01 | Complete known-good synthetic proof, trusted policy, exact candidate and fake time inside validity. | VALID; no write or merge side effects. |
| PP-02 | Reorder JSON object properties and legal whitespace without changing values. | Same canonical message and signature validation; candidate array order is not silently changed. |
| PP-03 | Duplicate top-level or nested keys, including conflicting head/profile values. | REJECT before signature evaluation; no last-key-wins parser. |
| PP-04 | Unknown fields, missing fields, nulls, Boolean-as-integer, float/exponent integers, invalid version. | REJECT for each independent mutation. |
| PP-05 | BOM, invalid UTF-8, lone surrogate, multiple JSON documents, Markdown wrapper, report URL or two envelopes. | REJECT; no secondary interpretation or network fetch. |
| PP-06 | Body at 8,192-byte limit and one byte over; third object level, array or extra object member. | Valid bounded input can proceed; oversize/deep/extra-container input REJECT, no truncation or unbounded allocation. |
| PP-07 | Uppercase/short/long hex, unsafe identifier text, integer above safe range, padded/noncanonical base64url. | REJECT before use. |
| PP-08 | Published Ed25519 known-answer vectors and independent domain-separated project vector. | Correct vectors verify; bit flips in payload/signature/key fail. |
| PP-09 | Wrong key, unregistered key, revoked key, wrong algorithm, RSA/HMAC substitution or caller-provided key. | REJECT; no fallback or key download. |
| PP-10 | Valid signature over raw JSON instead of canonical/domain-separated message, wrong domain or extra newline. | REJECT. |
| PP-11 | Malformed/noncanonical signature encoding or scalar/point cases rejected by the selected library's strict profile. | REJECT; no alternate decoder/library retry. |
| PP-12 | Missing library, unsupported runtime or failure to load pinned implementation. | BLOCKED; no permissive parser/signature fallback. |

## Candidate and namespace binding

| ID | Mutation or scenario | Required outcome |
|---|---|---|
| PP-13 | Correct proof copied to another repository, PR, fork, base branch, base SHA or head SHA. | REJECT every variant. |
| PP-14 | Candidate changes one byte, trailing newline, Unicode encoding or file size after scan. | REJECT despite unchanged logical JSON values. |
| PP-15 | Head adds, omits or changes an unchanged-from-base boundary file outside the changed-file subset used by a faulty scanner. | REJECT through full-surface reconstruction. |
| PP-16 | Missing manifest, missing statement, no aggregate, extra aggregate filename or duplicate descriptor member. | REJECT each case. |
| PP-17 | Traversal, absolute/backslash/control-character path, case-confusable path, prefix collision or non-ASCII member. | REJECT, no filesystem escape. |
| PP-18 | Symlink, executable blob, submodule, directory-as-file or nested unapproved aggregate member. | REJECT before content evaluation. |
| PP-19 | Per-file and total candidate limits at boundary and one byte over. | Valid boundary proceeds; oversize REJECT, no partial hashing. |
| PP-20 | Fourth output location, workflow/code change mixed with data, rename, copy or deletion. | REJECT regardless of author or branch label. |
| PP-21 | Admission candidate not a sole-parent one-commit child of current public main; main advances. | REJECT at admission/controlled merge; rebuild/re-scan/re-prove, not silent rebase. Deployment uses its distinct historical-parent checks. |
| PP-22 | Metadata claims an expected blob but fetched bytes differ, API patch is truncated or file-list pagination incomplete. | BLOCKED/REJECT; no trust in patch snippets or reported counts alone. |
| PP-23 | Existing scanner envelope digest incorrectly substituted for the public candidate digest. | REJECT; adapter equivalence must be demonstrated, not assumed. |
| PP-24 | Candidate includes executable-looking content, malicious filenames or a policy/verifier replacement. | Treat as inert data; REJECT forbidden change; zero candidate-code execution. |

## Trust roots, profiles and privacy

| ID | Mutation or scenario | Required outcome |
|---|---|---|
| PP-25 | Candidate changes its own key/profile/policy registry or requests a floating revision. | REJECT; trusted independent code/policy remains authoritative. |
| PP-26 | Previously valid policy replaced or key revoked while old proof still has time remaining, before a checkpoint reads policy. | REJECT at that checkpoint; no caller-selected old registry. In-flight changes after the final read are tested as residual risks, not atomic cancellation. |
| PP-27 | Key before/after validity interval, valid at issuance but expired now, or unauthorized for profile. | REJECT each variant. |
| PP-28 | Unknown profile, changed private mapping behind same public label, unpinned runtime/dependency, stale private input state. | Producer NO-SIGN; public verifier rejects unknown labels but must not claim to inspect private mapping. |
| PP-29 | Fake receipt says pass but omits scan targets, failed URL scan, skipped stage, archive confirmation or exact content binding. | Producer NO-SIGN/NO-WRITE; no trust in a top-level Boolean. |
| PP-30 | Receipt is validly shaped but from wrong private workflow/revision/run/attempt or untrusted artifact. | Producer NO-SIGN; private provenance mismatch stays private. |
| PP-31 | Public envelope/log/branch/check contains private canary, private URL/ID/hash, denylist state or matched text. | REJECT/export refusal; canary absent from all captured public sinks. |
| PP-32 | Profile/key/proof labels encode private data instead of using approved labels and independent randomness. | Producer refuses invalid labels; test generation path and entropy source. Document compromised-signer covert-channel limit rather than claim universal detection. |
| PP-33 | Public verifier attempts a private checkout/API call, private credential read or network request from envelope URL. | Test fails immediately; no such dependency is permitted. |
| PP-34 | Syntax/crypto/API error contains attacker-controlled text or private producer exception. | Fixed sanitized public code only, no echo or traceback leakage. |
| PP-35 | Authenticated compromised signer makes a false scan assertion over matching public bytes. | Document trust limitation: signature can validate; do not claim public cryptography detects private dishonesty. Producer isolation remains a separate control. |

## Freshness, replay and state changes

| ID | Mutation or scenario | Required outcome |
|---|---|---|
| PP-36 | Time immediately before expiry, exactly at expiry and after expiry. | Before can be VALID; at/after REJECT with no grace. |
| PP-37 | Scan-to-expiry interval 900/901 seconds; scan-to-issue delay 300/301 seconds. | At limits can be VALID; over REJECT. |
| PP-38 | Future issue/scan at 60/61-second tolerance; reversed times; issue equals expiry; unavailable trusted clock. | At tolerance can proceed; invalid ordering/over tolerance REJECT; unknown clock BLOCKED. |
| PP-39 | Same proof checked again for same open unchanged PR within lifetime. | VALID idempotent verification; no global one-use claim and no duplicate side effect. |
| PP-40 | Proof reused across PRs/heads/bases; closed/merged PR supplied to admission; closed-unmerged PR supplied to deployment. | REJECT each case. Deployment accepts merged state only with the exact provenance in PP-62, never by relaxing admission. |
| PP-41 | Fresh proof issued; earlier proof replayed for identical still-valid tuple. | Follow documented semantics: not automatically revoked. Test enforceable policy/key revocation separately. |
| PP-42 | Raw PR body, head/base, repository state or policy changes between initial and final consumer reads. | REJECT/BLOCKED, no success for the prior snapshot. |
| PP-43 | Re-sign old scan with fresh issue time to extend its original maximum lifetime. | REJECT; the 900-second limit is measured from scan completion. |
| PP-44 | External URL content changes after scan. | Point-in-time claim only; do not assert continuous safety. Rescan rules and later rendered-output checks remain separate. |

## Producer ordering and side-effect isolation

| ID | Mutation or scenario | Required outcome |
|---|---|---|
| PP-45 | Initial G5 quarantine, malformed candidate, scan exception, incomplete target coverage, failed prerequisite or 900-second scan age at preflight. | NO-SIGN/NO-WRITE; no App credential access or new public data. Recheck after queue waits. Later failure stops the controlled operation but does not guarantee invalidation of an earlier green status. |
| PP-46 | Public-schema export fails, internal correction identifier remains, or required correction contract is absent. | NO-SIGN/NO-WRITE; G5 pass alone cannot override the block. |
| PP-47 | Private sealed-receipt validation or required archival fails/cancels. | NO-SIGN/NO-WRITE, no fabricated archive success. |
| PP-48 | Caller uploads a fabricated receipt or instructs a signing job to sign arbitrary bytes. | NO-SIGN; independent trusted producer checks mandatory. |
| PP-49 | App branch/commit/PR operation fails after a successful scan, or remote bytes differ. | Stop proof issuance and controlled merge; partial public branch/PR is already disclosure, not authorization. Reconcile unknown provider outcomes without blind retry. |
| PP-50 | Proof attachment fails, signature key unavailable, retry occurs after expiry or run cancels. | Controlled publisher submits no new merge/deploy; no unsigned/cached fallback. An already submitted operation has an unknown outcome until reconciled. |
| PP-51 | App key used to sign proof, proof key offered to GitHub API, or either credential appears in logs/artifacts. | Test fails; credential separation and zero disclosure required. |
| PP-52 | Correct synthetic scan, sealed receipt, archive, exact public reconstruction, independent signer checks and attachment. | Future integration produces only minimal valid envelope; still NO-MERGE until all release gates exist. |

## Native controls, checkpoints and residual-race tests

These are later-stage acceptance tests, NOT authorized live experiments.
They require an approved mechanism and a separate safe test environment before
any attempt against protected main. No present GitHub capability is presumed
to satisfy them. Simulations can exercise the logic offline; they are not proof
that hosted protections, permissions or all deploy paths are configured.

| ID | Scenario | Required outcome before activation |
|---|---|---|
| PP-53 | Required verdict missing/pending/failed/cancelled, wrong producer/head; separately skip or neutralize a prerequisite or finalizer. | Native protections block unsupported verdicts. The trusted unconditional finalizer must fail for every non-success prerequisite; demonstrate that neutral/skipped GitHub conclusions are not relied on as rejection. Any path producing an accepted green verdict without validation blocks activation. |
| PP-54 | Check passes, proof expires before controlled merge, manual merge, or final deployment checkpoint. | Controlled merge/deployment refuse at their fresh checks. A native manual merge using stale green may occur: record RESIDUAL-OBSERVED and require NO-DEPLOY at the expired deployment checkpoint. Do not report the repository exposure as prevented. |
| PP-55 | Base advances before admission, during controlled merge validation, or after validation but before GitHub merge. | Validator rejects observed drift; demonstrate native strict up-to-date enforcement for the later race. Unexpected merge provenance/tree fails deployment and the native-control acceptance test; head-SHA guard alone is insufficient. |
| PP-56 | Body changes, key revokes or policy changes before a checkpoint versus after its final read and before provider completion. | Pre-checkpoint change refuses. Later change is RESIDUAL-OBSERVED, not guaranteed cancellation; next checkpoint rejects. No retroactive deletion or rollback is implied. |
| PP-57 | Head changes during checks or merge request; squash/rebase/manual merge changes the expected merge shape or tree. | API head guard rejects head mismatch; deployment rejects any merge other than exact ordered parents and full candidate-tree equality. Never bind a different result using only matching file counts. |
| PP-58 | Concurrent workflow jobs, operator merge, long approval wait, expiry during build, or main advance during deployment. | Every controlled retry and post-wait operation revalidates. No claim that workflow concurrency locks manual actions. A post-final-read change is a recorded residual window; do not promise provider completion before expiry. |
| PP-59 | Candidate replaces trusted code/policy, forged verdict source, direct push/rules bypass, unchecked manual dispatch or alternative Pages credential/workflow. | Native-control and deployment-path inventory/tests expose the bypass; activation BLOCKED until closed. No automatic migration, bypass grant or new infrastructure. Admin changes to trust controls are an explicit assumption, not defeated by this test. |
| PP-60 | API uncertainty before submission versus timeout/cancellation after merge/deploy request is accepted. | Before submission: BLOCKED and no new operation. After submission: outcome unknown, read-only reconciliation required; no blind retry, "no write" claim or automatic rollback. |
| PP-61 | Missing checkpoint, stale evidence reuse, swapped built artifact, skipped final validation, or revised residual risks not explicitly accepted. | Activation BLOCKED. Require final validation after all waits/builds, immediately adjacent to submission, with immutable candidate/artifact binding. |
| PP-62 | Exact synthetic merge/deployment success; expired post-merge proof; fresh re-scan recovery; wrong merge parents/tree, moved main, reused old receipt or changed candidate during refresh. | Valid exact result can deploy only after independent deployment validation and other gates. Refresh requires a new complete private scan/receipt, same immutable tuple and new proof/timestamps; invalid variants refuse. Test admission still rejects the merged PR. |

## Traceability and evidence

| Contract obligation | Planned cases |
|---|---|
| Strict minimal format, canonical bytes and authenticated signature | PP-01 through PP-12 |
| Exact public target, full-content binding and constrained diff | PP-13 through PP-24 |
| Independent trust roots, honest profile claims and disclosure limits | PP-25 through PP-35 |
| Bounded time, replay semantics and stable reads | PP-36 through PP-44 |
| G5-before-credential ordering and trusted private issuance | PP-45 through PP-52 |
| Native controls, explicit checkpoints, deployment provenance and residual timing limits | PP-53 through PP-62 |

For every future executed case record: case ID, exact verifier/producer/policy
revisions, synthetic fixture digest, expected and observed result, zero-skip
count, fake-clock input and side-effect spy results. For checkpoint cases include
validation time, submission time, provider acceptance/completion and actual
outcome; label post-read races instead of treating them as prevented.
Private producer receipts
stay private. Any later public test summary needs its own disclosure review;
this plan does not authorize publishing private run links or hashes.

## Staged acceptance and stop conditions

- Design review: D1 through revised D6 in ADR 0019 explicitly accepted/redlined;
  each test has an owner role and expected result. Project lead owns acceptance;
  implementer owns offline tests; a separate review pass checks evidence.
- Offline implementation: deterministic vectors and PP-01 through PP-44 run
  without production credentials; applicable public invariants still pass.
  PP-35 and PP-44 must report limits truthfully, not be converted to fake refusal
  guarantees. Production gate remains hard-failing.
- Private producer: PP-28 through PP-32 and PP-45 through PP-52 run against an
  approved isolated implementation with private evidence retained privately.
- Hosted enforcement: PP-53 through PP-62 demonstrated against the actual
  approved checkpoint model, including native protection, operator paths,
  all deployment paths, refresh recovery and deliberately observed races.
- Activation: separate authorization only after every applicable case is
  evidenced, no skips or unknown results remain, and other boundary dependencies
  are complete. A passing proof suite does not complete M1 by itself.

The initial time/size limits stay unchanged. Tune only through a reviewed
change justified by authorized-run measurements, not automatic widening or
an unexplained test waiver. No numerical provider-delay bound is claimed.

No percentage-coverage number, new key, active public proof, passing production
check, or completed test result is claimed by this preparation.
