# Publication-proof verifier and read-only GitHub adapter

## GitHub snapshot connection

The inherited `data/aggregates/.gitkeep` is inert repository scaffolding only
when it is an unchanged, zero-byte, regular `100644` file in both authenticated
trees. It is not an allowed release write, not part of the candidate digest,
and not packaged into Pages. Every other unexpected aggregate-directory file
remains a refusal.

`github_snapshot.py` connects the existing verifier to authenticated, read-only
GitHub metadata and actual Git objects for the fixed public repository. It serves
ADR 0019's admission adapter and PP-22/23 plus mutable-state checkpoint cases.
It adds no signing key, public workflow, required check, status write, merge or
deployment permission. Production publication remains blocked.

The adapter verifies repository identity and public visibility, same-repository
open/non-draft PR state, one-commit parentage and current main. A fresh bare
object database fetches only from the fixed HTTPS repository, without a working
tree, templates, hooks or submodule recursion. Every commit, tree and blob is
checked against its Git object identity. Complete base/head trees determine the
diff; patch snippets and paginated file-list completeness claims are not trusted.
Unchanged files participate in reconstruction. Symlinks, submodules, deletions,
mixed code/data changes, unsafe paths, unsupported modes and incomplete counts
fail. Candidate content is never executed or imported.

`read_admission` rereads PR body, refs, state and metadata after reconstruction.
`check_admission` additionally calls a runner-supplied, independently selected
current-policy reader twice, rechecks PR state again and repeats signature,
expiry and key-validity verification with the final clock. Changed policy or
state and a backwards clock fail. This is checkpoint validation, not an atomic
GitHub transaction or protection against an ABA change between observations.

The runner and its authenticated `gh`/`git` environment remain trusted. The
runner's configured `gh` host/authentication route is respected, including an
approved connector proxy; neither comes from candidate content. A caller
who substitutes a dishonest API/object/policy provider is outside this adapter's
trust model. Use code selected independently of the PR. Safe production key
provisioning, registry selection, the private signed producer, all release gates,
controlled merge and deployment verification are still required. The returned
verdict retains `publication_authorized=False`.

Resource bounds match the core's 5,000 files, 5 MiB per non-boundary blob and
50 MiB per tree. Additional adapter bounds are 10,000 entries, 64 directory
levels, 1 MiB per tree object/API response, 256 KiB per commit and 120 seconds
per transport command. These are refusal limits, never truncation. They bound
processed objects, not the downloaded Git pack's total disk size.

The diagnostic below checks a proposed boundary PR's snapshot only. It does not
load a production policy or claim a valid signature, and must not be used as the
publication success check:

```sh
uv run --directory tools/publication_proof --locked python github_snapshot.py --pr NUMBER
```

The remaining sections describe the unchanged pure core and its earlier
implementation evidence. Its no-I/O restriction applies to `proof.py`, not the
separate authenticated adapter.

### Adapter validation

Local validation on 2026-09-23: 304 tests passed (238 existing core tests and
66 adapter tests), with lint, formatting and strict type checks passing. The
core retains 100% measured statement/branch coverage; the adapter measures 99%
(its executable entry line runs in a separate subprocess test). Coverage is not
a security-completeness claim.

The adapter tests cover real bare Git object reads, byte-identity mismatches,
unsafe tree structure/modes, incomplete diffs, fork and identity rejection,
mixed code changes, stale/mutating PR state, policy changes, late expiry,
interrupted reads, transport failures and fixed CLI diagnostics. An authenticated
read-only live probe reconstructed and verified all 102 files at public main
`37c973df003745436c087299f70b893c43ffaf56`. That probe did not approve a boundary
PR, sign data, change repository settings or publish anything.

## Pure verifier core

The core was the first implementation increment, not an active publication gate.
It verifies a synthetic or caller-supplied attestation against explicitly supplied
policy, snapshot and clock inputs. Success means **valid at check time**;
the result always has `publication_authorized=False`.

It is a separate, reviewable implementation of part of the
[proposed contract](../../docs/adr/0019-public-safe-g5-proof-contract.md).
The contract and its companion plan retain their proposal-era status; this
README records the narrower implementation status. No production key, live
registry, workflow, required check, merge/deploy path or public data is added.
The existing public G5 block remains unchanged.

## What works

- Strict, closed UTF-8 JSON parsing with size/depth bounds, duplicate detection,
  safe integers, exact string grammars and canonical unpadded base64url.
- Domain-separated Ed25519 verification using pinned `cryptography==50.0.1`.
  The library verifies 64-byte signatures against 32-byte public keys and raises
  on invalid signatures ([versioned API documentation](https://cryptography.io/en/50.0.1/hazmat/primitives/asymmetric/ed25519/)).
- Full supplied boundary-surface hashing, including unchanged files, raw bytes,
  modes, paths and sizes. The computed diff must match the supplied complete
  addition/modification summary, with no mixed code changes.
- Exact repository/PR/base/head binding and sole-parent admission shape,
  checked against the supplied snapshot.
- Policy/key/profile matching, key validity/revocation and unchanged D4 limits:
  900-second scan lifetime, 300-second signing delay, 60-second future tolerance,
  8,192-byte body, 1 MiB per boundary file and 4 MiB per boundary candidate.
- Fixed refusal codes rather than attacker-controlled exception messages.
  There is no signing, I/O, network client or execution of candidate content
  in the core.

## Trust boundary and non-goals

`verify_offline(raw, policy_bytes, snapshot, now)` is a pure admission-mode
function, not a trusted GitHub adapter. The caller supplies all four inputs.
The module cannot establish that the supplied policy is the currently approved
policy, the clock is trusted, the Git SHAs identify the supplied bytes, or the
snapshot is complete and current. Setting `complete=True` is an adapter assertion,
not independent evidence. A deliberate test demonstrates that internally
consistent but fabricated Git identifiers can pass this core.

The separate adapter described above authenticates repository/PR/Git-object
metadata, reconstructs complete trees and diffs, detects incomplete reads, and
rereads changing state. Its trusted runner must still select verifier/policy
revisions independently of the candidate; production selection is not
implemented here. Neither layer trusts a patch snippet or declared blob identity.

A valid signature authenticates the key holder's assertion; it cannot prove
that the private scan happened or that an authorized signer is honest. This
core does not validate aggregate schemas, scan names or URL destinations,
validate sealed receipts, assess proof-ID entropy, or check export eligibility.
URL-looking content stays inert bytes. No continuous URL-safety claim is made.

There is no replay database, producer, signing service, command-line success
gate, credential handling, deployment mode, merge controller or hosted protection
test in the core. The adapter adds final point-in-time state rereads, not a
controlled merge. Rechecking the same still-valid proof is idempotent;
issuing a newer proof does not automatically revoke an older valid proof.
Merged PRs remain invalid for this admission-only function.

Catch `Refused` at a future adapter boundary and emit only its fixed `code`.
Do not print input values, exception locals or debug dumps. Missing dependency
imports fail rather than fall back; a future runner must sanitize bootstrap
failures too. Unexpected runtime failures must never become a success verdict.

## Production-key registration prerequisite

**Production key registration remains blocked pending a reviewed provisioning
design and its acceptance tests.** The current policy loader checks public-key
encoding and 32-byte length, not whether that encoding establishes a safe
signing identity. Signature verification alone does not supply this guarantee.

A synthetic review probe registered the identity-point encoding (`01` followed
by 31 zero bytes) in the supplied trusted policy. A constructed signature of
that value followed by 32 zero bytes then passed the current offline verifier
without a private signing operation. The same signature failed under the normal
RFC test public key. This depends on an unsafe key being placed in trusted
policy; it is not evidence of a bypass of a properly provisioned approved key.
The verdict still had `publication_authorized=False`.

Before any production key can enter an approved registry, the separately
reviewed provisioning implementation must:

- Establish and record the key's approved origin, authorized signer and custody;
  never import candidate-supplied keys or the deliberately public RFC test key.
- Define and enforce safe Ed25519 key-acceptance rules using a maintained,
  reviewed validation mechanism, not handwritten curve arithmetic. Explicitly
  reject identity/low-order keys and invalid encodings; length alone is not
  validation.
- Include the identity-key/constructed-signature regression, rejection cases
  for the other prohibited key classes, and a positive control for a properly
  generated key. Demonstrate failure before an unsafe key is registered.
- Review the provisioning evidence and the independently selected registry
  before authorizing production use. Existing validity and revocation fields
  do not replace this prerequisite.

These are future acceptance requirements, not implemented guarantees of this
offline component. No key, credential, production registry or live workflow
is introduced here.

## Canonicalization and provisional policy schema

The core supports only ASCII strings and nonnegative safe integers, plus
schema-controlled objects/arrays/Booleans in policy and descriptors. Its
canonical encoder is compatible with that restricted domain, **not a general
JCS implementation**. Full JCS additionally specifies general Unicode/UTF-16
ordering and ECMAScript floating-point serialization
([RFC 8785](https://www.rfc-editor.org/rfc/rfc8785)).

The provisional offline policy is a closed object with exactly `version`,
`contract`, `algorithm`, `repository_id`, `repository_name`, `base_branch`,
`limits`, `aggregate_files`, `profiles` and `keys`. Its complete synthetic
example is in [the independent vector](./tests/vector.json). Key records contain
only `key_id`, `public_key`, `profiles`, `not_before`, `not_after` and `revoked`.
Validity intervals are half-open, and apply at issuance and verification time.

This schema is an implementation proposal, not a deployed trust root.
Policy arrays preserve order when hashing. Limits and aggregate filenames
must exactly match this version; changes require explicit code/policy review,
not a permissive runtime override.

Additional offline input guards bound policy to 64 KiB and four container
levels, the registry to 16 keys and 32 profile labels per list, each supplied
tree to 5,000 files/50 MiB, a non-boundary blob to 5 MiB, and paths to 4,096
ASCII characters. All supplied files must be regular files; boundary files
must be non-executable. Duplicate, unsafe and file/directory-prefix-colliding
paths fail. These defensive fixture/adapter-input limits are not measurements
of production needs or authorization to widen D4.

## Reproduce locally

Run from the repository root using Python 3.14.3 and uv. Dependency resolution
is pinned in [the lockfile](uv.lock); installation may access public PyPI,
but executing the proof suite uses no production credentials or network reads.

```sh
uv sync --project tools/publication_proof --locked
uv run --directory tools/publication_proof --locked pytest \
  --cov=proof --cov-branch --cov-report=term-missing --cov-fail-under=100
uv run --directory tools/publication_proof --locked ruff check .
uv run --directory tools/publication_proof --locked ruff format --check .
uv run --directory tools/publication_proof --locked mypy --strict proof.py github_snapshot.py
```

The independently generated project vector uses Node's crypto implementation
and a separate ASCII canonical serializer. It includes canonical policy,
descriptor and payload bytes, domain-message bytes, digests and signature.
The seed is the deliberately public TEST 1 seed from
[RFC 8032 section 7.1](https://www.rfc-editor.org/rfc/rfc8032).
The suite also checks that RFC's published empty-message known answer.
This seed and policy must NEVER enter a production trust registry.

To regenerate with Node 20.20.1 and check reproducibility:

```sh
node tools/publication_proof/tests/generate_vectors.mjs
git diff --exit-code -- tools/publication_proof/tests/vector.json
```

Node is a vector-regeneration dependency only. Ordinary tests consume the
committed vector and do not shell out to Node.

## Test evidence and remaining acceptance work

Local validation on 2026-09-23: 238 proof tests passed with zero skips, strict
type checking and lint/format checks passed, and the core had 100% measured
statement/branch coverage. This metric describes exercised code, not security
completeness, hosted behavior or completion of the full adversarial plan.

Two isolated regressions now use otherwise-valid signed envelopes: a boundary
file at 1 MiB passes while 1 MiB + 1 byte fails with the candidate total below
4 MiB, and scan-time `0` passes while the wire spelling `-0` fails. The size
fixture constructs its descriptor hash independently of `candidate_digest`.
In disposable copies, removing only the per-file size guard or allowing only
the negative-zero token each caused its corresponding new test to fail
(1 failed, 237 passed per mutation). These targeted checks are not an exhaustive
mutation-testing score.

The [62-case plan](../../docs/publication-proof-adversarial-plan.md) remains
the acceptance backlog. The table below maps local evidence to topics; it
does not mark entire multi-part plan cases complete.

| Local test groups | Plan topics exercised | Not established here |
|---|---|---|
| Independent vector, parser/closure/base64 tests, signature tampering and malformed scalar/point tests | PP-01 through PP-12 component logic | All cryptographic edge cases, every unsupported runtime, runner bootstrap sanitization |
| Target binding, raw bytes, unchanged surface, path/mode/size/diff tests | PP-13 through PP-21 and PP-24 component logic | Authentic GitHub metadata, Git-object identity, API completeness or private/public adapter equivalence |
| Policy schema, current-policy controls, key intervals, fixed refusal codes | PP-25 through PP-27 and PP-34 component logic | Independent live policy selection/revocation reads, public runner diagnostics |
| Unknown-profile, no-I/O inspection, inert URL and fabricated snapshot tests | Limited PP-28, PP-33, PP-35 and PP-44 trust-boundary evidence | Private mappings, truthful scans, public job isolation, changing external URLs |
| Time boundaries, clock rejection, repeat verification and proof refresh tests | PP-36 through PP-41 and PP-43 admission components | Deployment behavior or mutable-state re-reads in PP-42 |

The new adapter exercises PP-22/23 and mutable-state checkpoint topics with
synthetic authenticated-metadata substitutes and real local Git object tests.
This does not complete the hosted acceptance plan. Private-producer PP-28
through PP-32 and PP-45 through PP-52, and hosted checkpoint/deployment PP-53
through PP-62 remain incomplete.

The next production prerequisite is reviewed safe-key provisioning and an
independently selected current registry, followed by the private signed producer
and controlled merge/deployment connection. Keep the production block until
those components and the release gates pass separately reviewed acceptance
tests. No successful diagnostic here authorizes publishing data.
