# ADR 0022: Unattended, counts-only research RC

- Status: proposed for activation approval
- Date: 2026-09-23
- Authority: the operator requested one unattended collection-to-Pages cycle
  and explicitly authorized necessary documentation changes.
- Scope: MVP items 1–7, limited to the existing single-source View 1 RC.

## Decision

Run the existing private schedule through collection, deterministic derivation,
automated eligibility, exact-byte export checks, G5, private archival, signed
App-opened PR, fresh merge verification, and fresh deployment verification.
The public build never reads the private repository. Ordinary observations
do not need an operator click. No new source, scheduler or server is added.

This amendment replaces the blanket pending-review behavior of ADR 0021.
For this counts-only RC it supersedes ADR 0010's universal burn-in/first-seen
human approval requirement, not its hard privacy gates. Operator review is
for exceptions, disputes, calibration and RC graduation, not routine release.
Uncertain or conflicting sectors remain **unclassified** and can still
contribute to that bucket. Only a single explicit description-term match is
classified automatically; it is a source-description heuristic, not an
independently verified company classification.

## RC eligibility and evidence

The immutable intake chain and its byte-addressed evidence are verified before
derivation. Intake's original pending flags are not rewritten; the new,
versioned derivative records eligibility and the reason for each exclusion.
Exact normalized actor/subject grouping is provisional claim grouping, not
proof of victim identity or independent corroboration.

The automated metadata screen covers every raw text field. Credentials,
personal-contact/identifier indicators, non-ASCII or control-bearing subject
and actor strings, impossible future source dates, historical reprocessing,
and explicitly suppressed candidates are withheld. Exceptions do not block
unrelated eligible candidates. Missing images do not block metadata-derived
counts. Images remain private, are not classification inputs, are not
published, and are not claimed to have passed OCR or image-PII review.
This is an explicit bounded metadata-screen profile, not a claim of complete
international PII detection or full production G2/G3 coverage.

Private corrections are append-only suppression events with fixed reason
codes. Suppressed candidates are excluded on every re-derivation. This RC
does not automatically resolve disputes, restore suppressed records, or
silently infer removals from a recent-only source window.

The public display remains the closed `xevents-view1-display/v1` contract:
21 fixed sectors, first-retrieval Monday UTC weeks, counts at least five,
otherwise null including zero. A cycle with no eligible records can release
an honestly empty dataset. No invented values, synthetic fallback, incident
names, source URLs, private record identifiers or raw evidence digests.

For this RC, G7 uses a private per-cell binding to original observations and
verified evidence. The public manifest binds only the already-public
aggregate bytes. This deliberately supersedes per-observation public evidence
hash linkage: public users can check export integrity but cannot independently
reconstruct the private evidence chain. That limitation is disclosed.
G6 is fixed claim-framing, not user-supplied text. G5 scans the exact candidate
bytes after serialization, using every subject and actor in the source
window, including excluded observations. Failure blocks the whole release.
G5 is not bypassed for common words or false positives.

## Release and deployment

Only the existing boundary App writes the three approved public locations.
It cannot write app code, policy, workflows or trust roots through this
publisher. A separate Ed25519 key signs proofs; the App RSA key is not reused.
An empty/revoked/expired key registry blocks activation.

All public writes follow a successful archived private preflight. A separately
credentialed job recomputes the candidate from the verified store, checks the
reviewed profile, rereads live state and signs only the exact App PR head.
The existing 900/300/60-second proof limits remain unchanged.

Public admission uses trusted main code, never PR executable code. Boundary
PRs must be same-repository, single-commit, verified App commits and data-only.
Code PRs cannot mix in boundary data. A required Actions check independently
verifies the proof and explicitly attaches its check to the PR head SHA;
`pull_request_target`'s base-bound job result is not used as a head attestation.
The private controller then rechecks the proof, policy,
native protections, PR/base/head, and check result immediately before asking
GitHub for a normal merge with an expected head SHA. No admin bypass,
squash fallback or auto-widened timeout exists.

Deployment checks the resulting two-parent merge, exact head/merge tree
equality, signed proof, current trust policy and current main. Only a successful
fresh release is deployed. Code-only merges wait for the next scheduled
release, which packages the then-current reviewed app. A deploy request is
preceded by another fresh check. GitHub provides no atomic multi-condition
merge/deploy transaction; the small last-check-to-request race remains the
ADR 0019 limitation. A refusal retains the prior deployed site.
The controller verifies successful completion of the exact release's Pages
deployment step and current main before reporting deployment. A separate
private-only audit job archives the fixed-schema outcome; a missing outcome
is not a successful burn-in cycle.

## Burn-in and operations

RC burn-in begins with the first verified real automated release, not a
synthetic run, replay, documentation merge or private-only capture. Record
private cycle receipts, exclusions, gate outcomes, timing and release results.
The existing 30-day/500-forward-observation target is retained as a graduation
review target, not a requirement to keep the RC dark or manually approve each
record. Neither threshold alone declares production readiness.

Every run must visibly fail on corrupt evidence, unknown schema/profile,
G5 failure, invalid proof, stale state, missing controls or deployment error.
Source failures preserve evidence and leave the last release available.
The reader labels old data stale. Small samples are not zero incidents.

Activation requires: approved memo and private dispute contact, separately
approved key provisioning, passing tests, reviewed merges, required public
boundary check, Actions-based Pages, and an explicit private enable flag.
Turning off that flag stops new releases without disabling evidence intake.
Revoking the public key blocks all subsequent proof verification. Existing
public Git history and a completed deployment are not erased by revocation.
