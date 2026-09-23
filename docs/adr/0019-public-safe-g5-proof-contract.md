# ADR 0019: Public-safe G5 publication attestation

- Status: proposed (pending user redline)
- Date: 2026-09-22
- Revision: 2026-09-23; revised D6 approved as design direction only
- Deciders: project lead; D6 design approval recorded, no merge or implementation authorization
- Scope: M1 boundary proof contract and adversarial test design
- Related: [privacy-preserving verification](0015-private-invariant-verification.md),
  [App transport](0014-app-opened-pr-transport.md),
  [G5 specification](0013-g5-name-scan-gate.md)

## Purpose and authority

The operator requested a narrowly scoped proof contract and adversarial test
plan. This proposal serves M1 AC1.1, AC1.2, revised AC1.3, and the required
G5 check in [the implementation plan](../implementation-plan.md).
It does not authorize implementation, key creation, workflow dispatch, public
data writes, required-check activation or live publication.

The current boundary-related public G5 gate must continue returning
`public-proof-contract-not-implemented`. Preparation or merge of these documents
does not replace that failure with success. The companion
[adversarial plan](../publication-proof-adversarial-plan.md) specifies future
tests; none are represented as newly implemented or passing here.

If explicitly accepted, this contract would replace the full-report-in-PR
interpretation of the G5-check clauses in ADR 0014 with a minimal attestation.
It also proposes replacing private batch identifiers in public PR bodies and
branch suffixes with independent public randomness; that change is not yet
approved or implemented.
It would not change the three-location write set, loosen the naming policy,
approve correction export, or rewrite accepted historical documents.

## Focused revision and changed guarantee

This revision replaces the earlier requirement for atomic custom authorization
at the instant of GitHub merge with explicit validation checkpoints. It is a
weaker timing guarantee, not an equivalent implementation of that requirement.
The operator endorsed the initial D4 limits and evidence-based tuning, then
explicitly approved revised D6 as the design direction on 2026-09-23.
That D6 approval includes the checkpoint model and residual risks stated here;
it does not authorize merge, implementation, key setup or activation.
The full ADR remains proposed; this approval is not blanket acceptance of the
remaining contract decisions.

| Earlier proposal | Revised D6, approved as design direction only |
|---|---|
| Expiry, proof-body changes and revocation prevent every merge at the exact instant it occurs. | Each controlled operation checks fresh evidence immediately before its request; native branch rules govern merges, but no atomic custom expiry/revocation guarantee is claimed. |
| A green required proof check must remain current until merge. | A green check records validity at check time only; controlled merge and website deployment repeat validation. A manual merge may still use a previously valid green check. |
| The 15-minute limit is a maximum age at completed publication. | The unchanged 900-second limit is enforced at the defined validation checkpoints, not a deadline guaranteed for GitHub's later completion or CDN propagation. |

Public branch creation is already public disclosure. Public main is also
public, even if Pages has not deployed. A later website check cannot prevent
or undo either exposure. Every initial boundary write therefore still requires
successful private G5/export validation of the exact bytes before transport.
This revision does not authorize publishing unscanned data as public staging.

## Meaning of a proof

A valid attestation would mean: a separately trusted private producer states
that the exact public candidate identified by this proof passed G5 under an
approved scanner profile, and the public verifier has authenticated that
statement and recomputed its public-content binding.

It would NOT mean the public job inspected private evidence, independently
reran G5, proved the private producer uncompromised, established incident
truth, or authorized release. A signature authenticates a producer's claim;
it does not make an incorrect producer truthful. Required protections,
all other gates, export contracts and checkpoint freshness remain independent.

The claim is point-in-time. In particular, a scanned external URL can change
after the scan. A short proof lifetime reduces this interval; it does not
promise that an external destination will remain safe indefinitely.

## Recommended authentication design

Use a dedicated Ed25519 attestation key, separate from the GitHub App key.
The private key would exist only in a future trusted private signing job.
The public verifier needs only a reviewed public key and public data.
No private checkout, report download, private-read credential or private API
lookup is permitted in a public job.

Ed25519 has 32-byte public keys and 64-byte signatures; implementers must use
a maintained, pinned library and published known-answer vectors, not a custom
signature implementation ([RFC 8032](https://www.rfc-editor.org/rfc/rfc8032)).
No RSA App-key reuse, HMAC shared secret, unsigned JSON, author-name inference,
or fallback algorithm is allowed by this proposal.

This is a new credential dependency requiring separate approval. No key or
secret is generated by this increment. Before implementation, a reviewed
lifecycle must cover provisioning, restricted job access, rotation, emergency
revocation, recovery and compromise response. A missing key or policy blocks.

Alternatives considered:

- App authorship or a verified commit alone: identifies a GitHub actor/commit,
  not the specific private scan and candidate the claim concerns.
- Full private reports or identity-bearing provenance tokens: violate this
  contract's public disclosure budget unless separately redesigned and approved.
- Dedicated signature: chosen as the proposal because public verification can
  be offline and need not expose private provenance. Its additional secret and
  trust-root management are real costs, not assumed solved.

## Public disclosure budget

Only the exact envelope below may cross through the proof channel. It contains
public repository/PR identity, public Git revisions, digests of public content
and policy, public profile/key labels, an independent random proof identifier,
three timestamps and a signature.

Forbidden in the envelope, public logs, branch names, check output and error
messages: private repository identity/revisions/run URLs, private workflow or
fixture identifiers, internal batch/observation/correction IDs, names, matched
strings, evidence paths, raw reports, raw URL-fetch results, denylist entries,
denylist size/version/digest and hashes of private artifacts. Hashing a private
value is not permission to publish it.

The profile label must be from a finite public policy registry, not a private
commit hash in disguise. Key labels come from that same reviewed registry.
The proof identifier must be independent random data, never an encoded private
identifier. Timing, public profile/key versions and public-data digests are
explicit metadata disclosures that the operator must approve.

The schema and output discipline constrain an honest producer; they cannot
eliminate covert channels under a compromised authorized signer. That signer,
the private job, the public policy authority, the verifier and GitHub integrity
are explicit trust assumptions.

## Proposed v1 envelope

The entire PR body is one UTF-8 JSON object with exactly `payload` and
`signature`. No Markdown fences, report links, arbitrary notes, extra fields,
embedded URLs or multiple proof blocks. The v1 byte limit is 8,192.

`signature` is unpadded base64url of exactly 64 signature bytes. `payload` is
an object with exactly the following fields; null values and extensions fail:

| Field | Exact v1 constraint |
|---|---|
| `version` | Integer `1`, not Boolean. |
| `repository_id` | Positive GitHub numeric ID equal to the trusted target policy and live PR metadata. |
| `pr_number` | Positive integer equal to the same-repository PR; open for admission/merge, merged for the separate deployment mode. |
| `base_sha` | Exactly 40 lowercase hex characters; direct parent of the candidate and current public main at admission/merge validation; historical first parent of the verified merge commit at deployment. |
| `head_sha` | Exactly 40 lowercase hex characters; exact same-repository PR head, preserved as the second parent of the merge commit for deployment validation. |
| `candidate_sha256` | Exactly 64 lowercase hex characters; digest defined below. |
| `policy_sha256` | Exactly 64 lowercase hex characters; SHA-256 of the canonical, independently trusted public verification policy. |
| `profile_id` | Exact member of the policy's approved scanner-profile set; ASCII grammar `[a-z0-9][a-z0-9._-]{0,63}`. |
| `key_id` | Exact member of the policy's approved, currently valid non-revoked key set; same ASCII grammar as `profile_id`. |
| `proof_id` | 32 lowercase hex characters from 128 fresh cryptographically random bits. |
| `scan_completed_at` | Integer Unix seconds, from the sealed private successful scan. |
| `issued_at` | Integer Unix seconds, after scan completion. |
| `expires_at` | Integer Unix seconds; see freshness limits. |

All integers are in `0..9007199254740991`, further restricted as above, with
JSON number tokens matching `0|[1-9][0-9]*` (no exponent, fraction or minus).
Only the stated ASCII string grammars are permitted. Reject duplicate keys,
unknown keys, invalid UTF-8, a BOM, lone surrogates, floating-point values,
nonfinite values, trailing documents, arrays and noncanonical
base64url encodings. Reject rather than normalize an invalid candidate.
The envelope has exactly two object levels: the root and its payload.
No deeper container is permitted. Apply the byte and depth bounds while parsing,
before unbounded allocation; reject any extra object member immediately.

The signature message is the exact ASCII bytes
`xevents-publication-proof/v1`, then one NUL byte, then UTF-8 JCS(payload).
There is no implicit newline and no caller-selected algorithm.
Use RFC 8785 canonicalization; JSON property order on the wire is immaterial,
but duplicate properties are forbidden and array order is preserved
([RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)).
Both sides must publish matching canonical-byte/hash test vectors before use.

There is no separate outcome field: only a complete successful G5 scan can
produce a v1 proof. A quarantine, exception, partial scan or skipped prerequisite
must produce no public proof or new boundary branch/PR. If a later revalidation
fails after a successful initial scan and partial transport, the existing
controlled operation stops; an existing branch/PR is not authorization. A
previously emitted green status has the residual timing limitations below.

## Exact public-candidate binding

Reconstruct the full resulting boundary surface at `head_sha`, not just the
changed lines, API patch text, changed files or the scanner's existing private
envelope hash. Hash raw Git blob bytes, without newline or Unicode normalization.

The v1 candidate descriptor is a closed object containing only `files`.
`files` is an array sorted by ASCII path bytes. Each member has exactly:
`path`, `mode` (literal `"100644"`), `size` (raw byte length integer), and
`sha256` (raw-byte SHA-256). The candidate digest is SHA-256(JCS(descriptor)).
Git object IDs are not substitutes for these SHA-256 content digests.

Require the manifest and coverage statement and at least one aggregate file.
For this v1 proposal, aggregate filenames are limited to `view1.jsonl` and
`view2.jsonl` beneath the existing aggregate directory. Require exact agreement
between the descriptor and every file under that directory plus the two other
boundary locations. No fourth output location is introduced. Any additional
filename needs a separately reviewed profile/contract revision.

Reject symlinks, executable modes, submodules, missing mandatory files, duplicate
or unsafe paths and unexpected aggregate members. Initial limits are 1 MiB per
file and 4 MiB across the boundary candidate. These are proposed safety caps;
oversize fails, never truncates. Larger production needs require review.

At admission/merge validation, the v1 candidate is exactly one commit whose
sole parent is current public main. The complete parent-to-head diff contains
only regular-file additions
or modifications inside the permitted locations. Deletions, renames, copies,
multiple parents, extra commits and mixed code/data changes are refused even
where the existing path-only check is broader. These proposed restrictions
serve the thin first transport, not new permissions.

For boundary data, the proposed controlled transport requests a merge commit,
not squash or rebase. At deployment, verify that merge commit has exactly the
ordered parents `[base_sha, head_sha]` and its full Git tree equals the signed
candidate head's tree. A different merge shape, conflict resolution or altered
tree is ineligible; never silently reinterpret an old proof for a new tree.
This is a future boundary-transport requirement, not a repository setting change
or a restriction newly applied to documentation PRs.

The private producer must scan exactly this complete candidate and privately
bind the scan to these same bytes. An adapter from the existing scanner envelope
to this descriptor needs reviewed equivalence tests; equality is not assumed.
Public verification re-reads Git objects by immutable SHA and recomputes the
descriptor. Candidate files remain inert data throughout.

## Public trust policy and private profile mapping

The future trusted public policy must have a closed, versioned schema containing
the target repository ID/name/base branch, contract/algorithm identifiers,
candidate limits and filenames, timing limits, approved public profiles, and
key records with public key bytes, permitted profiles, validity intervals and
revocation state. Unknown policy fields fail. No public policy file or key
record is created or activated by this preparation.

A separately selected trusted verifier revision loads that policy from a
reviewed public policy revision, never the candidate, PR body, attached key or
artifact. The payload's policy digest must equal the current approved policy.
Policy or revocation changes invalidate prior proofs at the next validation;
no instantaneous cancellation of an in-flight GitHub operation is promised.
A proof cannot select an older registry to revive a revoked key.
Policy changes and candidate data cannot
approve each other in one boundary PR.

For each public profile, a private reviewed mapping must bind the exact scanner
code, dependencies/runtime, normalization rules, public-export validation,
candidate adapter and producer code. Dynamic denylist state, its derivation
inputs, private code revisions, private receipt and URL outcomes stay in the
private evidence chain. The producer must verify this mapping and the current
required input state before signing. Missing, stale or candidate-edited mappings
refuse signing; an unchanged public label must never silently select new code.

The public verifier trusts the signer's profile assertion. It cannot verify the
private mapping itself; no independent private-code verification is claimed.
Changing the mapping requires reviewed profile versioning and public policy
coordination, not a private-only reinterpretation of an old label.

## Proposed freshness and replay semantics

Initial values for review: maximum scan-to-expiry interval 900 seconds;
maximum scan-to-issuance delay 300 seconds; maximum future-clock tolerance
60 seconds. Require `scan_completed_at <= issued_at < expires_at`,
`expires_at - scan_completed_at <= 900`, and
`issued_at - scan_completed_at <= 300`.

At verification, require `scan_completed_at <= now + 60`,
`issued_at <= now + 60`, and `now < expires_at`; there is no expiry grace.
The key must be valid and unrevoked both at issuance and at current validation,
and authorized for the profile. Key validity intervals are half-open:
`not_before <= issued_at < not_after` and `not_before <= now < not_after`.
Current revocation overrides a formerly valid interval. Missing/untrusted time
fails.

Repository, PR, base, head, candidate digest, current policy and signature
prevent reuse for a different target. The nonce is not a replay database.
Repeated verification of the same proof for the same open PR and unchanged
head is intentionally idempotent while valid. This contract does not claim
global one-time consumption. A merged/closed PR is not eligible for admission
or merge mode. Deployment mode separately
requires an already merged PR with the exact merge provenance defined below;
a merely closed, unmerged PR is never eligible.

A changed head, advanced base at admission, policy change, expiry or relevant
private-input change requires a newly validated candidate and fresh proof.
Deployment uses the historical parent tuple and current-main selection rules
below, rather than applying admission's current-base rule to a merged PR.
Issuing a new proof
does not itself revoke an otherwise valid old one: urgent invalidation requires
a current policy/key revocation record checked at each checkpoint. Revocation
does not erase public Git history, retract a completed deployment or cancel an
already accepted provider request.

The initial limits remain 900/300/60 seconds and 1 MiB per file, 4 MiB total.
Record scan duration, scan-to-sign delay, queue wait, validation-to-request
delay and provider completion duration during authorized runs. Review measured
results before changing limits; never auto-widen, truncate, extend an old scan
or treat a slow run as an implicit exception. Public telemetry still requires
the disclosure review above.

## Producer and consumer sequence

Future producer, only after separate implementation approval:

1. Run trusted private code on an approved main revision, with no candidate
   code execution, PR-provided commands or untrusted dependency installation.
2. Resolve the approved profile and current private inputs. Build and scan the
   candidate, validate export schemas and all prerequisite gates, seal and
   validate the private receipt, and complete required private archival.
3. Only then permit App credential access. Construct a signed public commit
   from an exact public base using the scanned bytes. Verify remote blob bytes,
   the complete diff and the commit identity. A transport failure produces no
   authorization and stops the controlled operation.
   Before the first public write, recheck the private receipt's exact candidate,
   current profile/input state and scan age below 900 seconds. There is no
   public PR number or signed PR envelope yet; this private preflight is not
   misrepresented as a public proof. Queue waits require a new preflight.
4. Obtain the public PR number using a fixed pending body, with a random public
   branch identifier, never a private batch/fixture identifier. Revalidate the
   complete candidate and fresh scan before proof signing.
5. The isolated signing job independently validates the sealed evidence,
   approved producer/profile revision and public target. Only after those
   checks does it receive the dedicated signing key and emit the minimal proof.
   Arbitrary uploaded `pass` JSON or a caller-supplied digest is insufficient.
6. Replace the PR body with the envelope. Errors, cancellations or proof-attach
   failure must stop controlled publication; no unsigned fallback. Required
   checks must not report success without a valid proof, but stale green
   statuses have the expressly documented limitations below.

Future public admission consumer:

1. Use trusted verifier code and independently approved current policy.
2. Read the exact open same-repository PR and its actual base/head, enforce
   complete pagination and immutable blob reads, and reject API uncertainty.
3. Parse the one envelope within limits; authenticate it, its key/profile/policy,
   exact target binding and time window; recompute the complete candidate.
4. Re-read PR state, raw proof body, base/head and policy immediately before
   emitting the result. Any race/change fails rather than verifies stale data.
5. Emit only a fixed result code, public PR/head and fixed contract label.
   Never echo untrusted body text, parse errors, private receipt or matched data.

Passing this consumer means only `attestation-valid-at-check-time`.
It must not be called a complete publication authorization.

## Checkpoint model and native controls

A green status is not a continuously refreshed authorization. Proof expiry,
key revocation, PR-body replacement and base changes can occur after a check.
Public metadata edits may also leave the same head SHA. Event-triggered reruns
and a last-minute read improve detection but are not an atomic merge condition.

GitHub's documented merge endpoint offers a `sha` condition on the PR head;
its parameter list does not provide an equivalent base-SHA condition
([GitHub REST documentation](https://docs.github.com/en/rest/pulls/pulls)).
Strict required status checks require a branch to be up to date with its base;
they do not provide a custom proof-expiry condition
([protected branches](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/defining-the-mergeability-of-pull-requests/about-protected-branches)).
GitHub can treat neutral/skipped checks as successful, so requiring a check name
alone does not establish a fail-closed verifier
([status checks](https://docs.github.com/en/pull-requests/reference/status-checks)).

The proposed checkpoints are:

1. **First public write:** private preflight above, before any branch/blob/commit
   write. Failed or stale input means no new public write by the producer.
2. **PR admission and controlled merge:** admission runs the public verifier.
   The controlled publisher repeats the entire verification immediately before
   requesting merge with `sha=head_sha` and `merge_method=merge`. The final
   validation and request occur consecutively in the same trusted job, with no
   approval wait, queued downstream job or unrelated work between them. A
   retry starts validation again; never reuse an earlier green result.
3. **Website deployment:** a trusted public-only workflow verifies the actual
   merged result, current policy/key, full candidate bytes and fresh proof.
   It builds only that immutable revision, runs the other site gates, then
   repeats validation after all build/queue/approval waits and immediately
   before submitting the exact checked artifact for deployment. No job may
   substitute a newer branch tip or an unbound artifact after validation.

Deployment mode is a separate verifier entry point, not a permissive flag on
admission. It requires the actual PR state `merged`, its recorded merge commit
equal to the selected deployment revision, ordered parents and full-tree
equality above, and that revision still being public main at the final read.
It reuses the exact signed public tuple and recomputes the candidate digest.
It does not require historical `base_sha` still to be current main.

If a proof expires after merge, stop deployment. The private producer may issue
a replacement only after a new complete scan of those same immutable public
bytes under current inputs/profile and a new sealed receipt. It may replace the
same merged PR's body after verifying the exact merge provenance; no new data
write is implied. The original base/head tuple stays fixed, but timestamps and
proof ID are new. Never re-sign the old scan with a later expiry. If the tuple,
public main or candidate changed, do not refresh it as a shortcut: use a new
reviewed candidate path. This recovery needs explicit private-producer tests.

Before activation, demonstrate native required checks with strict up-to-date
enforcement, authenticated expected check producers, required PRs/signatures,
and no configured bypass. The trusted final verdict must execute regardless of
child-job outcomes and emit success only for explicit complete validation;
skipped, neutral, missing or failed prerequisites cannot become success.
Candidate-controlled code must not produce that verdict. A discovered bypass
or untrusted producer blocks activation rather than becoming an exception.

Every deploy-capable path, including manual workflow dispatch and retries, must
enter the deployment checkpoint. Inventory and test those paths and credential
holders before activation; no separate unchecked Pages workflow is permitted.
Workflow concurrency can serialize cooperating jobs, but is not a lock against
manual GitHub merges or administrators. Administrators who change protections,
trusted code or deployment permissions remain outside this control's guarantee.

### Residual risks accepted as design limits

- A manual merge can occur after a proof expires or changes if an earlier green
  check still satisfies native rules. This proposal does not claim to prohibit
  it mechanically. The deployment workflow must evaluate fresh evidence rather
  than trust that green check; repository disclosure has already happened.
- Expiry, revocation, body edits or a new main revision after the final read but
  before provider completion may escape that operation's last check. There is
  no claimed numerical upper bound on provider delay or universal atomic
  cancellation. Record the outcome; subsequent operations must validate anew.
- Timeout or lost responses can leave an already submitted merge/deployment
  completed despite an unknown local result. Reconcile provider state read-only;
  do not blindly retry, report "no write", or claim a rollback.
- Do not automatically delete public history or revert a deployment after such
  a race. Detection triggers the existing incident/correction process; rollback
  and takedown remain separately authorized actions.

This model needs no new server, organization transfer or merge queue. GitHub
documents queue availability for organization-owned repositories, and queue
checks still do not document custom atomic expiry/revocation evaluation
([merge queues](https://docs.github.com/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/managing-a-merge-queue)).
Those alternatives are not dependencies of this proposed revision.

### Readiness remains blocked

The existing hard-failing public G5 gate remains unchanged. D6 design approval
satisfies only that decision: the remaining contract review, trusted
implementations, native protections and revised adversarial tests still need
completion, and activation must be separately authorized. A docs merge or
offline parser pass is not activation. A future change to the accepted risk
model requires explicit review; do not quietly widen it.

## Required decisions and exit criteria

Decision register; approval of one item does not approve the others:

- D1: attestation trust model and dedicated Ed25519 credential dependency.
- D2: the exact public disclosure budget, including timing and public labels.
- D3: body-only transport, signed envelope and complete-candidate descriptor.
- D4: initial time/size limits and evidence-based tuning endorsed; filename
  restrictions remain part of the overall contract review.
- D5: profile versioning and key/policy rotation and revocation requirements.
- D6 (revised): approved as design direction on 2026-09-23, including
  checkpoint-time freshness, manual-merge/in-flight residual risks and the
  independent deployment gate. Merge, implementation and activation remain
  separately authorized; the existing hard block remains in place.

Preparation is complete when these decisions are reviewable, test cases and
expected outcomes are traceable, and the two documents add no runtime behavior.
Acceptance of a design is not acceptance of its implementation.

Later stages, each separately authorized: offline verifier and synthetic vectors;
private producer/profile/key lifecycle; trusted public consumer and checkpoint
integration with native protections; adversarial hosted tests; only then required-check and
transport activation. Correction export, documentation enforcement, site build,
and all other M1/M2 dependencies remain separate gates, not waived by a proof.
