# Offline publication-proof verifier

This is the first implementation increment, not an active publication gate.
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

The future adapter must select trusted verifier/policy revisions independently
of the candidate, authenticate repository/PR/Git-object metadata, reconstruct
complete trees and diffs, detect incomplete reads, and re-read changing state at
the defined checkpoints. It must not trust a caller's completeness flag, patch
snippet, declared blob identity, file count or old policy selection.

A valid signature authenticates the key holder's assertion; it cannot prove
that the private scan happened or that an authorized signer is honest. This
core does not validate aggregate schemas, scan names or URL destinations,
validate sealed receipts, assess proof-ID entropy, or check export eligibility.
URL-looking content stays inert bytes. No continuous URL-safety claim is made.

There is no replay database, producer, signing service, command-line success
gate, credential handling, deployment mode, merge controller, final state re-read
or hosted protection test. Rechecking the same still-valid proof is idempotent;
issuing a newer proof does not automatically revoke an older valid proof.
Merged PRs remain invalid for this admission-only function.

Catch `Refused` at a future adapter boundary and emit only its fixed `code`.
Do not print input values, exception locals or debug dumps. Missing dependency
imports fail rather than fall back; a future runner must sanitize bootstrap
failures too. Unexpected runtime failures must never become a success verdict.

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
uv run --directory tools/publication_proof --locked mypy --strict proof.py
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

Local validation on 2026-09-23: 236 proof tests passed with zero skips, strict
type checking and lint/format checks passed, and the core had 100% measured
statement/branch coverage. This metric describes exercised code, not security
completeness, hosted behavior or completion of the full adversarial plan.

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

PP-22/23 adapters, private-producer PP-28 through PP-32 and PP-45 through PP-52,
and hosted checkpoint/deployment PP-53 through PP-62 are not implemented.
The offline acceptance stage as a whole is therefore still incomplete.

Next bounded increment: review this core and its provisional policy schema,
then design/implement the authenticated read-only snapshot adapter and its
incomplete-read/state-change tests. Keep the production block in place until
the remaining producer, deployment and hosted acceptance work is separately
reviewed and authorized.
