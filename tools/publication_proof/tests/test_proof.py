"""Synthetic offline tests. Signing uses only the deliberately public RFC test seed."""

import ast
import base64
import json
import subprocess
import sys
from copy import deepcopy
from dataclasses import replace
from pathlib import Path

import pytest
from cryptography.exceptions import UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

import proof as p

VECTOR = json.loads(Path(__file__).with_name("vector.json").read_text())
SEED = bytes.fromhex("9d61b19deffd5a60ba844af492ec2cc44449c5697b326919703bac031cae7f60")
NOW = 1000060
CANARY = "PRIVATE_CANARY_DO_NOT_ECHO"


def wire(obj):
    return json.dumps(obj, separators=(",", ":")).encode()


def signing(payload, domain=p.DOMAIN):
    # Test-only signer, not shipped in or imported by the core.
    signature = Ed25519PrivateKey.from_private_bytes(SEED).sign(domain + p.canonical(payload))
    return wire(
        {"payload": payload, "signature": base64.urlsafe_b64encode(signature).rstrip(b"=").decode()}
    )


def snapshot():
    files = tuple(p.Blob(f["path"], "100644", f["data"].encode()) for f in VECTOR["files"])
    code = p.Blob("README.md", "100644", b"Inert unchanged repository content.\n")
    return p.Snapshot(
        123,
        "example/synthetic",
        123,
        7,
        "open",
        "main",
        "a" * 40,
        "a" * 40,
        "b" * 40,
        ("a" * 40,),
        (code,),
        (*files, code),
        tuple(p.Change(f.path, "added") for f in files),
        True,
    )


def run(raw=None, policy=None, snap=None, now=NOW):
    return p.verify_offline(
        wire(VECTOR["envelope"]) if raw is None else raw,
        wire(VECTOR["policy"]) if policy is None else policy,
        snapshot() if snap is None else snap,
        now,
    )


def refuses(fn, code=None):
    with pytest.raises(p.Refused) as exc:
        fn()
    assert str(exc.value) in {c.value for c in p.Code}
    assert CANARY not in str(exc.value)
    assert exc.value.__cause__ is None
    if code:
        assert exc.value.code == code


def resigned_policy(policy):
    payload = deepcopy(VECTOR["payload"])
    payload["policy_sha256"] = p.digest(p.canonical(policy))
    return signing(payload), wire(policy)


def changed(snap, path, data=None, mode=None):
    """Rebuild the complete addition/modification summary for a synthetic tree."""
    files = tuple(
        replace(f, data=f.data if data is None else data, mode=f.mode if mode is None else mode)
        if f.path == path
        else f
        for f in snap.head_files
    )
    return refreshed(replace(snap, head_files=files))


def refreshed(snap):
    before = {f.path: f for f in snap.base_files}
    changes = tuple(
        p.Change(f.path, "modified" if f.path in before else "added")
        for f in snap.head_files
        if before.get(f.path) != f
    )
    return replace(snap, changes=changes)


def test_independent_node_vector_and_rfc_known_answer():
    assert (
        VECTOR["public_key_hex"]
        == "d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"
    )
    assert VECTOR["empty_message_signature_hex"] == (
        "e5564300c360ac729086e2cc806e828a84877f1eb8e5d974d873e065224901555fb88"
        "21590a33bacc61e39701cf9b46bd25bf5f0595bbe24655141438e7a100b"
    )
    p.verify_signature(
        bytes.fromhex(VECTOR["public_key_hex"]),
        bytes.fromhex(VECTOR["empty_message_signature_hex"]),
        b"",
    )
    for key in ("policy", "descriptor", "payload"):
        assert p.canonical(VECTOR[key]) == VECTOR["canonical_" + key].encode()
    assert p.DOMAIN + p.canonical(VECTOR["payload"]) == bytes.fromhex(VECTOR["message_hex"])
    assert p.policy_from_bytes(wire(VECTOR["policy"])).sha256 == VECTOR["payload"]["policy_sha256"]
    assert p.candidate_digest(snapshot()) == VECTOR["payload"]["candidate_sha256"]
    result = run()
    assert result == p.Verdict(7, "b" * 40)
    assert result.mode == "offline-only" and result.publication_authorized is False


def test_wire_order_whitespace_and_exact_body_cap():
    envelope = VECTOR["envelope"]
    raw = json.dumps(
        {
            "signature": envelope["signature"],
            "payload": dict(reversed(list(envelope["payload"].items()))),
        },
        indent=2,
    ).encode()
    assert run(raw=raw) == run()
    raw += b" " * (8192 - len(raw))
    assert run(raw=raw) == run()
    refuses(lambda: run(raw=raw + b" "), p.Code.FORMAT)


@pytest.mark.parametrize(
    "raw",
    [
        b"",
        b"\xff",
        b"\xef\xbb\xbf{}",
        b"{}{}",
        b"null",
        b"true",
        b"[]",
        b'{"x":1,"x":2}',
        b'{"x":-0}',
        b'{"x":-1}',
        b'{"x":1.0}',
        b'{"x":1e0}',
        b'{"x":NaN}',
        b'{"x":Infinity}',
        b'{"x":9007199254740992}',
        b'{"x":10000000000000000}',
        b'{"x":"\\ud800"}',
        '{"x":"é"}'.encode(),
        b'{"payload":{"nested":{}}}',
        b'{"x":[1]}',
        b'{"x":',
        b"}{",
        b'{"x":"unterminated}',
        b"\x00{}",
        b" " * 8193,
    ],
)
def test_malformed_envelopes(raw):
    refuses(lambda: run(raw=raw), p.Code.FORMAT)


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", True),
        ("version", 2),
        ("repository_id", 0),
        ("pr_number", -1),
        ("scan_completed_at", False),
        ("issued_at", None),
        ("expires_at", "1000900"),
        ("base_sha", "A" * 40),
        ("head_sha", "b" * 39),
        ("candidate_sha256", "g" * 64),
        ("policy_sha256", "a" * 65),
        ("proof_id", "A" * 32),
        ("proof_id", "1" * 31),
        ("key_id", ""),
        ("key_id", "x" * 65),
        ("profile_id", "private/name"),
        ("profile_id", CANARY),
        ("profile_id", None),
    ],
)
def test_closed_payload_types(field, value):
    envelope = deepcopy(VECTOR["envelope"])
    envelope["payload"][field] = value
    refuses(lambda: run(raw=wire(envelope)), p.Code.FORMAT)


@pytest.mark.parametrize("field", sorted(p.PAYLOAD_FIELDS))
def test_missing_payload_field(field):
    envelope = deepcopy(VECTOR["envelope"])
    del envelope["payload"][field]
    refuses(lambda: run(raw=wire(envelope)), p.Code.FORMAT)


@pytest.mark.parametrize(
    "mutation",
    [
        "extra-root",
        "extra-payload",
        "null-payload",
        "missing-sig",
        "duplicate-payload-field",
        "duplicate-root",
    ],
)
def test_envelope_closure(mutation):
    envelope = deepcopy(VECTOR["envelope"])
    if mutation == "extra-root":
        envelope[CANARY] = "https://invalid.example/never-fetch"
    elif mutation == "extra-payload":
        envelope["payload"][CANARY] = 1
    elif mutation == "null-payload":
        envelope["payload"] = None
    elif mutation == "missing-sig":
        del envelope["signature"]
    elif mutation == "duplicate-payload-field":
        refuses(lambda: run(raw=wire(envelope).replace(b'"version":1', b'"version":1,"version":1')))
        return
    else:
        refuses(
            lambda: run(raw=wire(envelope).replace(b'"payload":', b'"payload":{},"payload":', 1))
        )
        return
    refuses(lambda: run(raw=wire(envelope)), p.Code.FORMAT)


@pytest.mark.parametrize(
    "signature", ["", "A" * 85, "A" * 87, "A" * 86 + "=", "/" * 86, "A" * 85 + "B", None, 3, CANARY]
)
def test_noncanonical_signature_encoding(signature):
    envelope = deepcopy(VECTOR["envelope"])
    envelope["signature"] = signature
    refuses(lambda: run(raw=wire(envelope)), p.Code.FORMAT)


@pytest.mark.parametrize("mutation", ["bit", "message", "domain", "key"])
def test_signature_tampering(mutation):
    envelope = deepcopy(VECTOR["envelope"])
    if mutation == "bit":
        sig = bytearray(p.unbase64(envelope["signature"], 64))
        sig[0] ^= 1
        envelope["signature"] = base64.urlsafe_b64encode(sig).rstrip(b"=").decode()
    elif mutation == "message":
        envelope["payload"]["proof_id"] = "2" * 32
    elif mutation == "domain":
        refuses(lambda: run(raw=signing(envelope["payload"], b"wrong-domain\0")), p.Code.SIGNATURE)
        return
    else:
        policy = deepcopy(VECTOR["policy"])
        policy["keys"][0]["public_key"] = (
            base64.urlsafe_b64encode(b"\x01" * 32).rstrip(b"=").decode()
        )
        raw, policy_raw = resigned_policy(policy)
        refuses(lambda: run(raw=raw, policy=policy_raw), p.Code.SIGNATURE)
        return
    refuses(lambda: run(raw=wire(envelope)), p.Code.SIGNATURE)


@pytest.mark.parametrize(
    "field,value",
    [
        ("version", 2),
        ("version", True),
        ("contract", CANARY),
        ("algorithm", "RSA"),
        ("base_branch", "other"),
        ("repository_id", 0),
        ("repository_name", "wrong"),
        ("profiles", []),
        ("profiles", ["synthetic-v1", "synthetic-v1"]),
        ("profiles", ["Bad"]),
        ("keys", []),
        ("keys", None),
        ("aggregate_files", ["data/aggregates/view1.jsonl"]),
    ],
)
def test_policy_shape(field, value):
    policy = deepcopy(VECTOR["policy"])
    policy[field] = value
    refuses(lambda: run(policy=wire(policy)))


@pytest.mark.parametrize("field", list(VECTOR["policy"]))
def test_policy_missing_fields(field):
    policy = deepcopy(VECTOR["policy"])
    del policy[field]
    refuses(lambda: run(policy=wire(policy)), p.Code.POLICY)


@pytest.mark.parametrize("field", sorted(p.LIMITS))
def test_no_automatic_limit_widening(field):
    policy = deepcopy(VECTOR["policy"])
    policy["limits"][field] += 1
    refuses(lambda: run(policy=wire(policy)), p.Code.POLICY)


@pytest.mark.parametrize(
    "field,value",
    [
        ("key_id", CANARY),
        ("public_key", "A"),
        ("profiles", []),
        ("profiles", ["unregistered"]),
        ("not_before", 2000000),
        ("not_after", 0),
        ("not_after", True),
        ("revoked", "false"),
        ("private_key", CANARY),
    ],
)
def test_key_registry_schema(field, value):
    policy = deepcopy(VECTOR["policy"])
    policy["keys"][0][field] = value
    refuses(lambda: run(policy=wire(policy)), p.Code.POLICY)


def test_duplicate_key_and_extra_policy_field():
    policy = deepcopy(VECTOR["policy"])
    policy["keys"].append(deepcopy(policy["keys"][0]))
    refuses(lambda: run(policy=wire(policy)), p.Code.POLICY)
    policy = deepcopy(VECTOR["policy"])
    policy[CANARY] = 1
    refuses(lambda: run(policy=wire(policy)), p.Code.POLICY)


@pytest.mark.parametrize(
    "kind",
    ["revoked", "unknown-key", "unknown-profile", "profile-key-mismatch", "old-policy-digest"],
)
def test_current_policy_controls(kind):
    policy, payload = deepcopy(VECTOR["policy"]), deepcopy(VECTOR["payload"])
    if kind == "revoked":
        policy["keys"][0]["revoked"] = True
    elif kind == "unknown-key":
        payload["key_id"] = "unregistered"
    elif kind == "unknown-profile":
        payload["profile_id"] = "unregistered"
    elif kind == "profile-key-mismatch":
        policy["profiles"].append("second")
        payload["profile_id"] = "second"
    else:
        policy["keys"][0]["not_after"] += 1
    if kind != "old-policy-digest":
        payload["policy_sha256"] = p.digest(p.canonical(policy))
    refuses(lambda: run(raw=signing(payload), policy=wire(policy)), p.Code.POLICY)


@pytest.mark.parametrize(
    "scan,issued,expiry,now,valid",
    [
        (1000000, 1000000, 1000900, 1000000, True),
        (1000000, 1000300, 1000900, 1000300, True),
        (1000000, 1000301, 1000900, 1000301, False),
        (1000000, 1000030, 1000901, 1000030, False),
        (1000000, 1000030, 1000900, 1000899, True),
        (1000000, 1000030, 1000900, 1000900, False),
        (1000000, 1000030, 1000900, 1000901, False),
        (1000000, 1000030, 1000900, 999970, True),
        (1000000, 1000030, 1000900, 999969, False),
        (1000000, 1000000, 1000900, 999940, True),
        (1000000, 1000000, 1000900, 999939, False),
        (1000031, 1000030, 1000900, 1000060, False),
        (1000000, 1000030, 1000030, 1000060, False),
        (1000000, 1000030, 1000029, 1000060, False),
    ],
)
def test_time_boundaries(scan, issued, expiry, now, valid):
    payload = deepcopy(VECTOR["payload"])
    payload.update(scan_completed_at=scan, issued_at=issued, expires_at=expiry)
    if valid:
        assert run(raw=signing(payload), now=now).publication_authorized is False
    else:
        refuses(lambda: run(raw=signing(payload), now=now), p.Code.TIME)


@pytest.mark.parametrize(
    "start,end,valid",
    [
        (1000030, 1000061, True),
        (1000031, 2000000, False),
        (0, 1000060, False),
        (0, 1000030, False),
        (1000060, 2000000, False),
    ],
)
def test_key_half_open_validity(start, end, valid):
    policy = deepcopy(VECTOR["policy"])
    policy["keys"][0].update(not_before=start, not_after=end)
    raw, policy_raw = resigned_policy(policy)
    if valid:
        run(raw=raw, policy=policy_raw)
    else:
        refuses(lambda: run(raw=raw, policy=policy_raw), p.Code.TIME)


@pytest.mark.parametrize(
    "field,value",
    [
        ("repository_id", 124),
        ("repository_id", True),
        ("repository_name", "other/synthetic"),
        ("head_repository_id", 124),
        ("pr_number", 8),
        ("pr_number", False),
        ("state", "closed"),
        ("state", "merged"),
        ("base_branch", "other"),
        ("current_main", "c" * 40),
        ("current_main", "invalid"),
        ("base_sha", "c" * 40),
        ("head_sha", "c" * 40),
        ("parents", ()),
        ("parents", ("a" * 40, "c" * 40)),
        ("parents", ("c" * 40,)),
    ],
)
def test_target_binding(field, value):
    refuses(lambda: run(snap=replace(snapshot(), **{field: value})), p.Code.TARGET)


@pytest.mark.parametrize("value", [False, None, 1])
def test_incomplete_snapshot(value):
    refuses(lambda: run(snap=replace(snapshot(), complete=value)), p.Code.BLOCKED)


@pytest.mark.parametrize("value", [True, -1, 1.5, None, p.SAFE_INT + 1])
def test_unusable_clock(value):
    refuses(lambda: run(now=value), p.Code.BLOCKED)


def test_no_head_base_alias():
    snap = replace(snapshot(), head_sha="a" * 40)
    payload = deepcopy(VECTOR["payload"])
    payload["head_sha"] = snap.head_sha
    refuses(lambda: run(raw=signing(payload), snap=snap), p.Code.TARGET)


@pytest.mark.parametrize("path", [*p.MANDATORY, p.AGGREGATES[0]])
def test_exact_raw_bytes_not_normalized(path):
    snap = changed(snapshot(), path, data=b"Modified\r\n")
    refuses(lambda: run(snap=snap), p.Code.CANDIDATE)


def test_unchanged_boundary_files_included():
    snap = snapshot()
    unchanged = snap.head_files[0]
    snap = refreshed(replace(snap, base_files=(*snap.base_files, unchanged)))
    assert run(snap=snap) == run()
    # A forged unchanged file in both parent and head still changes the bound full surface.
    replacement = replace(unchanged, data=b"Changed but absent from the diff.\n")
    snap = replace(
        snap,
        base_files=tuple(replacement if f == unchanged else f for f in snap.base_files),
        head_files=tuple(replacement if f == unchanged else f for f in snap.head_files),
    )
    refuses(lambda: run(snap=snap), p.Code.CANDIDATE)


@pytest.mark.parametrize(
    "kind",
    [
        "missing-manifest",
        "missing-coverage",
        "missing-aggregate",
        "extra-aggregate",
        "bare-aggregate",
        "code-change",
        "delete",
        "duplicate",
        "no-change",
        "wrong-summary",
        "duplicate-summary",
        "empty-summary",
        "rename",
        "copy",
    ],
)
def test_candidate_closure(kind):
    snap = snapshot()
    if kind.startswith("missing-"):
        path = {
            "missing-manifest": p.MANDATORY[1],
            "missing-coverage": p.MANDATORY[0],
            "missing-aggregate": p.AGGREGATES[0],
        }[kind]
        snap = refreshed(
            replace(snap, head_files=tuple(f for f in snap.head_files if f.path != path))
        )
    elif kind in ("extra-aggregate", "bare-aggregate"):
        path = "data/aggregates/extra.jsonl" if kind == "extra-aggregate" else "data/aggregates"
        extra = p.Blob(path, "100644", b"unchanged")
        snap = replace(
            snap, base_files=(*snap.base_files, extra), head_files=(*snap.head_files, extra)
        )
    elif kind == "code-change":
        snap = changed(snap, "README.md", data=b"altered")
    elif kind == "delete":
        snap = replace(snap, head_files=tuple(f for f in snap.head_files if f.path != "README.md"))
    elif kind == "duplicate":
        snap = replace(snap, head_files=(*snap.head_files, snap.head_files[0]))
    elif kind == "no-change":
        snap = replace(snap, base_files=snap.head_files, changes=())
    elif kind == "empty-summary":
        snap = replace(snap, changes=())
    elif kind == "duplicate-summary":
        snap = replace(snap, changes=(snap.changes[0], snap.changes[0], snap.changes[2]))
    else:
        status = {"wrong-summary": "modified", "rename": "renamed", "copy": "copied"}[kind]
        snap = replace(snap, changes=(replace(snap.changes[0], status=status), *snap.changes[1:]))
    refuses(lambda: run(snap=snap), p.Code.CANDIDATE)


@pytest.mark.parametrize("mode", ["100755", "120000", "160000", "040000", CANARY])
def test_boundary_modes(mode):
    refuses(lambda: run(snap=changed(snapshot(), p.AGGREGATES[0], mode=mode)), p.Code.CANDIDATE)


@pytest.mark.parametrize("path", ["../x", "/x", "a//b", "a/./b", "a/../b", "a\\b", "a\nb", "é", ""])
def test_unsafe_paths(path):
    extra = p.Blob(path, "100644", b"test")
    snap = snapshot()
    snap = replace(snap, base_files=(*snap.base_files, extra), head_files=(*snap.head_files, extra))
    refuses(lambda: run(snap=snap), p.Code.CANDIDATE)


def test_file_and_candidate_size_boundaries():
    snap = snapshot()
    fourth = p.Blob(p.AGGREGATES[1], "100644", b"x" * p.LIMITS["file_bytes"])
    snap = refreshed(replace(snap, head_files=(*snap.head_files, fourth)))
    for path in p.ALLOWED:
        snap = changed(snap, path, data=b"x" * p.LIMITS["file_bytes"])
    payload = deepcopy(VECTOR["payload"])
    payload["candidate_sha256"] = p.candidate_digest(snap)
    assert run(raw=signing(payload), snap=snap).publication_authorized is False
    snap = changed(snap, p.AGGREGATES[0], data=b"x" * (p.LIMITS["file_bytes"] + 1))
    refuses(lambda: run(snap=snap), p.Code.CANDIDATE)
    # With four allowed files, the per-file caps also imply the aggregate cap.


def test_no_network_execution_or_private_reads():
    tree = ast.parse(Path(p.__file__).read_text())
    imported = {node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)}
    imported |= {node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)}
    assert imported == {
        "__future__",
        "base64",
        "dataclasses",
        "enum",
        "hashlib",
        "json",
        "re",
        "typing",
        "cryptography.exceptions",
        "cryptography.hazmat.primitives.asymmetric.ed25519",
    }
    banned = {"open", "eval", "exec", "__import__", "compile", "input"}
    assert not any(
        isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in banned
        for node in ast.walk(tree)
    )
    # URL text remains bytes; this core does not implement private URL/name scanning.
    snap = changed(snapshot(), p.AGGREGATES[0], data=b"https://invalid.example/never-fetch\n")
    payload = deepcopy(VECTOR["payload"])
    payload["candidate_sha256"] = p.candidate_digest(snap)
    assert run(raw=signing(payload), snap=snap).publication_authorized is False


def test_missing_dependency_has_no_permissive_fallback():
    root = str(Path(p.__file__).parent)
    result = subprocess.run(
        [
            sys.executable,
            "-I",
            "-S",
            "-c",
            f"import sys; sys.path.insert(0, {root!r}); import proof",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode != 0 and "cryptography" in result.stderr
    assert "attestation-valid-at-check-time" not in result.stdout


def test_unsupported_algorithm_is_blocked(monkeypatch):
    class Unavailable:
        @staticmethod
        def from_public_bytes(_):
            raise UnsupportedAlgorithm(CANARY)

    monkeypatch.setattr(p, "Ed25519PublicKey", Unavailable)
    refuses(run, p.Code.BLOCKED)


def test_verification_is_repeatable_not_replay_storage_or_merge_permission():
    assert run() == run()
    refuses(lambda: run(now=1000900), p.Code.TIME)
    # This test cannot establish Git SHA authenticity or private-producer honesty.
    # Those are explicit future adapter/producer trust boundaries.


def test_noncanonical_base64_key_and_string_bound_scanner():
    refuses(lambda: p.unbase64("A" * 42 + "B", 32))
    assert p.parse(
        b'{"x":"braces: { [ ] } and quote: \\" and slash: \\\\"}', cap=100, depth=1, arrays=False
    )["x"].startswith("braces")
    refuses(lambda: p.canonical({"x": 1.2}))
    refuses(lambda: p.canonical({1: "bad"}))


@pytest.mark.parametrize(
    "pub,sig", [(b"x", b"x" * 64), (b"x" * 32, b"x"), ("x" * 32, b"x" * 64), (b"x" * 32, "x" * 64)]
)
def test_signature_byte_lengths(pub, sig):
    refuses(lambda: p.verify_signature(pub, sig, b""), p.Code.SIGNATURE)


@pytest.mark.parametrize("message_kind", ["raw-json", "newline", "no-domain"])
def test_incorrect_signed_message(message_kind):
    payload = VECTOR["payload"]
    messages = {
        "raw-json": p.DOMAIN + wire(payload),
        "newline": p.DOMAIN + p.canonical(payload) + b"\n",
        "no-domain": p.canonical(payload),
    }
    signature = Ed25519PrivateKey.from_private_bytes(SEED).sign(messages[message_kind])
    envelope = {
        "payload": payload,
        "signature": base64.urlsafe_b64encode(signature).rstrip(b"=").decode(),
    }
    refuses(lambda: run(raw=wire(envelope)), p.Code.SIGNATURE)


@pytest.mark.parametrize(
    "kind",
    [
        "prefix-collision",
        "too-many-files",
        "large-blob",
        "large-snapshot",
        "long-path",
        "invalid-change-path",
        "wrong-change-type",
        "wrong-blob-type",
        "blob-not-bytes",
        "changed-policy",
        "nested-aggregate",
        "case-confusable",
    ],
)
def test_additional_snapshot_refusals(kind):
    snap = snapshot()
    if kind == "prefix-collision":
        extra = (p.Blob("data", "100644", b"collision"),)
    elif kind == "too-many-files":
        extra = tuple(p.Blob(f"other/{n}", "100644", b"") for n in range(5001))
    elif kind == "large-blob":
        extra = (p.Blob("large", "100644", b"x" * (5 * 1048576 + 1)),)
    elif kind == "large-snapshot":
        blob = b"x" * (5 * 1048576)
        extra = tuple(p.Blob(f"other/{n}", "100644", blob) for n in range(11))
    elif kind == "long-path":
        extra = (p.Blob("x" * 4097, "100644", b""),)
    elif kind == "invalid-change-path":
        snap = replace(snap, changes=(p.Change([], "added"), *snap.changes[1:]))
        extra = ()
    elif kind == "wrong-change-type":
        snap = replace(snap, changes=(None, *snap.changes[1:]))
        extra = ()
    elif kind == "wrong-blob-type":
        snap = replace(snap, head_files=(*snap.head_files, None))
        extra = ()
    elif kind == "blob-not-bytes":
        snap = changed(snap, p.AGGREGATES[0], data="not bytes")
        extra = ()
    else:
        path = {
            "changed-policy": "policy.json",
            "nested-aggregate": "data/aggregates/sub/view1.jsonl",
            "case-confusable": "data/aggregates/View1.jsonl",
        }[kind]
        snap = refreshed(replace(snap, head_files=(*snap.head_files, p.Blob(path, "100644", b""))))
        extra = ()
    if extra:
        snap = replace(
            snap, base_files=(*snap.base_files, *extra), head_files=(*snap.head_files, *extra)
        )
    refuses(lambda: run(snap=snap), p.Code.CANDIDATE)


def test_wrong_snapshot_types_and_container_types():
    refuses(lambda: run(snap={}), p.Code.BLOCKED)
    refuses(lambda: p.candidate_digest(None), p.Code.BLOCKED)
    refuses(lambda: run(snap=replace(snapshot(), changes=[])), p.Code.CANDIDATE)
    refuses(lambda: run(snap=replace(snapshot(), head_files=[])), p.Code.CANDIDATE)


@pytest.mark.parametrize(
    "kind",
    [
        "oversize",
        "too-many-keys",
        "too-many-profiles",
        "duplicate-json",
        "boolean-limit",
        "extra-limit",
        "extra-key-field",
    ],
)
def test_policy_resource_and_closure_limits(kind):
    policy = deepcopy(VECTOR["policy"])
    if kind == "oversize":
        refuses(lambda: run(policy=b" " * 65537), p.Code.FORMAT)
        return
    if kind == "too-many-keys":
        policy["keys"] *= 17
    elif kind == "too-many-profiles":
        policy["profiles"] = [f"p{n}" for n in range(33)]
    elif kind == "duplicate-json":
        refuses(
            lambda: run(policy=wire(policy).replace(b'"version":1', b'"version":1,"version":1'))
        )
        return
    elif kind == "boolean-limit":
        policy["limits"]["body_bytes"] = True
    elif kind == "extra-limit":
        policy["limits"]["new"] = 1
    else:
        policy["keys"][0][CANARY] = "private"
    refuses(lambda: run(policy=wire(policy)), p.Code.POLICY)


def test_valid_modification_and_two_aggregate_ordering():
    snap = snapshot()
    before = tuple(
        replace(f, data=b"previous") if f.path in p.ALLOWED else f for f in snap.head_files
    )
    snap = refreshed(replace(snap, base_files=before))
    assert run(snap=snap) == run()
    assert p.candidate_digest(replace(snap, head_files=tuple(reversed(snap.head_files)))) == (
        p.candidate_digest(snap)
    )
    extra = p.Blob(p.AGGREGATES[1], "100644", b"second\n")
    snap = refreshed(replace(snap, head_files=(*snap.head_files, extra)))
    payload = deepcopy(VECTOR["payload"])
    payload["candidate_sha256"] = p.candidate_digest(snap)
    run(raw=signing(payload), snap=snap)


def test_refresh_does_not_revoke_valid_old_proof_or_extend_old_scan():
    old = deepcopy(VECTOR["payload"])
    new = {**old, "proof_id": "3" * 32, "issued_at": 1000050}
    assert run(raw=signing(old)) == run(raw=signing(new))
    stale = {**new, "issued_at": 1000310, "expires_at": 1001210}
    refuses(lambda: run(raw=signing(stale), now=1000310), p.Code.TIME)


def test_untrusted_snapshot_is_not_authenticated_by_core():
    # Deliberately fabricated but internally matching Git IDs are accepted.
    # This is evidence of the missing trusted adapter, not a security success.
    snap = replace(snapshot(), head_sha="c" * 40)
    payload = {**VECTOR["payload"], "head_sha": snap.head_sha}
    verdict = run(raw=signing(payload), snap=snap)
    assert verdict.head_sha == snap.head_sha and verdict.publication_authorized is False


@pytest.mark.parametrize("kind", ["noncanonical-scalar", "invalid-point", "zero-signature"])
def test_library_rejects_invalid_signature_components(kind):
    signature = p.unbase64(VECTOR["envelope"]["signature"], 64)
    if kind == "noncanonical-scalar":
        order = 2**252 + 27742317777372353535851937790883648493
        scalar = int.from_bytes(signature[32:], "little")
        signature = signature[:32] + (scalar + order).to_bytes(32, "little")
    elif kind == "invalid-point":
        signature = b"\xff" * 32 + signature[32:]
    else:
        signature = b"\0" * 64
    refuses(
        lambda: p.verify_signature(
            bytes.fromhex(VECTOR["public_key_hex"]), signature, bytes.fromhex(VECTOR["message_hex"])
        ),
        p.Code.SIGNATURE,
    )
