"""Pure offline verification core. No I/O, signing, live policy, or gate integration.

Caller-supplied snapshots/policy are NOT authenticated by this module.
A future trusted adapter must bind them to complete immutable Git/API reads.
"""

from __future__ import annotations

import base64
import hashlib
import json
import re
from dataclasses import dataclass
from enum import StrEnum
from typing import cast

from cryptography.exceptions import InvalidSignature, UnsupportedAlgorithm
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

type JSON = None | bool | int | str | list[JSON] | dict[str, JSON]
SAFE_INT = 9007199254740991
DOMAIN = b"xevents-publication-proof/v1\0"
AGGREGATES = ("data/aggregates/view1.jsonl", "data/aggregates/view2.jsonl")
MANDATORY = ("coverage-boundary-statement.md", "evidence-manifest.jsonl")
ALLOWED = frozenset((*AGGREGATES, *MANDATORY))
PLACEHOLDER = "data/aggregates/.gitkeep"
LIMITS = {
    "body_bytes": 8192,
    "file_bytes": 1048576,
    "candidate_bytes": 4194304,
    "scan_lifetime": 900,
    "sign_delay": 300,
    "clock_skew": 60,
}
PAYLOAD_FIELDS = frozenset(
    (
        "version",
        "repository_id",
        "pr_number",
        "base_sha",
        "head_sha",
        "candidate_sha256",
        "policy_sha256",
        "profile_id",
        "key_id",
        "proof_id",
        "scan_completed_at",
        "issued_at",
        "expires_at",
    )
)


class Code(StrEnum):
    FORMAT = "invalid-format"
    POLICY = "invalid-policy"
    TARGET = "target-mismatch"
    CANDIDATE = "invalid-candidate"
    SIGNATURE = "invalid-signature"
    TIME = "invalid-or-expired-time"
    BLOCKED = "dependency-or-snapshot-unavailable"


class Refused(ValueError):
    """Fixed codes only; never include caller-provided text or chained errors."""

    def __init__(self, code: Code):
        self.code = code
        super().__init__(code.value)


def require(condition: bool, code: Code) -> None:
    if not condition:
        raise Refused(code)


def integer(value: object, *, positive: bool = False, code: Code = Code.FORMAT) -> int:
    require(type(value) is int, code)
    result = cast(int, value)
    require((1 if positive else 0) <= result <= SAFE_INT, code)
    return result


def string(value: object, pattern: str, code: Code = Code.FORMAT) -> str:
    require(type(value) is str, code)
    result = cast(str, value)
    require(re.fullmatch(pattern, result, flags=re.ASCII) is not None, code)
    return result


def label(value: object, code: Code = Code.FORMAT) -> str:
    return string(value, r"[a-z0-9][a-z0-9._-]{0,63}", code)


def object_fields(value: JSON, fields: frozenset[str], code: Code) -> dict[str, JSON]:
    require(type(value) is dict, code)
    result = cast(dict[str, JSON], value)
    require(result.keys() == fields, code)
    return result


def _pairs(pairs: list[tuple[str, JSON]]) -> dict[str, JSON]:
    result: dict[str, JSON] = {}
    for key, value in pairs:
        require(key not in result, Code.FORMAT)
        result[key] = value
    return result


def _int_token(token: str) -> int:
    require(re.fullmatch(r"0|[1-9][0-9]{0,15}", token) is not None, Code.FORMAT)
    return integer(int(token))


def _no_number(_: str) -> JSON:
    raise Refused(Code.FORMAT)


def _bounds(text: str, depth_limit: int, arrays: bool) -> None:
    """Bound containers before json.loads allocates nested structures."""
    depth = 0
    quoted = escaped = False
    for char in text:
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
        elif char == '"':
            quoted = True
        elif char in "[{":
            require(arrays or char != "[", Code.FORMAT)
            depth += 1
            require(depth <= depth_limit, Code.FORMAT)
        elif char in "]}":
            depth -= 1
            require(depth >= 0, Code.FORMAT)
    require(depth == 0 and not quoted, Code.FORMAT)


def _json_subset(value: JSON) -> None:
    """Only ASCII strings and safe integers; NOT a general-purpose JCS encoder."""
    if value is None or type(value) is bool:
        return
    if type(value) is int:
        integer(value)
    elif type(value) is str:
        require(value.isascii(), Code.FORMAT)
    elif type(value) is list:
        for item in value:
            _json_subset(item)
    elif type(value) is dict:
        for key, item in value.items():
            require(type(key) is str and key.isascii(), Code.FORMAT)
            _json_subset(item)
    else:
        raise Refused(Code.FORMAT)


def canonical(value: JSON) -> bytes:
    """RFC 8785-compatible for our validated ASCII/safe-integer subset only."""
    _json_subset(value)
    return json.dumps(
        value, sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False
    ).encode("utf-8")


def parse(raw: bytes, *, cap: int, depth: int, arrays: bool) -> JSON:
    require(type(raw) is bytes and 0 < len(raw) <= cap, Code.FORMAT)
    try:
        text = raw.decode("utf-8", errors="strict")
        require(not text.startswith("\ufeff"), Code.FORMAT)
        _bounds(text, depth, arrays)
        value = cast(
            JSON,
            json.loads(
                text,
                object_pairs_hook=_pairs,
                parse_int=_int_token,
                parse_float=_no_number,
                parse_constant=_no_number,
            ),
        )
        _json_subset(value)
        return value
    except UnicodeError, json.JSONDecodeError, RecursionError:
        raise Refused(Code.FORMAT) from None


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def unbase64(value: object, length: int, code: Code = Code.FORMAT) -> bytes:
    text = string(value, r"[A-Za-z0-9_-]+", code)
    require(len(text) == (length * 8 + 5) // 6, code)
    result = base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))
    require(len(result) == length, code)
    require(base64.urlsafe_b64encode(result).rstrip(b"=").decode() == text, code)
    return result


def labels(value: JSON) -> tuple[str, ...]:
    require(type(value) is list and 0 < len(value) <= 32, Code.POLICY)
    result = tuple(label(item, Code.POLICY) for item in cast(list[JSON], value))
    require(len(set(result)) == len(result), Code.POLICY)
    return result


@dataclass(frozen=True)
class Key:
    key_id: str
    public_key: bytes
    profiles: tuple[str, ...]
    not_before: int
    not_after: int
    revoked: bool


@dataclass(frozen=True)
class Policy:
    repository_id: int
    repository_name: str
    profiles: tuple[str, ...]
    keys: tuple[Key, ...]
    sha256: str


def policy_from_bytes(raw: bytes) -> Policy:
    """Validate an independently selected policy, never an envelope-supplied policy."""
    fields = frozenset(
        (
            "version",
            "contract",
            "algorithm",
            "repository_id",
            "repository_name",
            "base_branch",
            "limits",
            "aggregate_files",
            "profiles",
            "keys",
        )
    )
    obj = object_fields(parse(raw, cap=65536, depth=4, arrays=True), fields, Code.POLICY)
    require(integer(obj["version"]) == 1, Code.POLICY)
    require(obj["contract"] == "xevents-publication-proof/v1", Code.POLICY)
    require(obj["algorithm"] == "Ed25519" and obj["base_branch"] == "main", Code.POLICY)
    limits = object_fields(obj["limits"], frozenset(LIMITS), Code.POLICY)
    for field, expected in LIMITS.items():
        require(integer(limits[field], code=Code.POLICY) == expected, Code.POLICY)
    require(obj["aggregate_files"] == list(AGGREGATES), Code.POLICY)
    repo_id = integer(obj["repository_id"], positive=True, code=Code.POLICY)
    repo_name = string(
        obj["repository_name"], r"[A-Za-z0-9_.-]{1,100}/[A-Za-z0-9_.-]{1,100}", Code.POLICY
    )
    profiles = labels(obj["profiles"])
    rows = obj["keys"]
    require(type(rows) is list and 0 < len(rows) <= 16, Code.POLICY)
    keys: list[Key] = []
    key_fields = frozenset(
        (
            "key_id",
            "public_key",
            "profiles",
            "not_before",
            "not_after",
            "revoked",
        )
    )
    for item in cast(list[JSON], obj["keys"]):
        row = object_fields(item, key_fields, Code.POLICY)
        key_id = label(row["key_id"], Code.POLICY)
        require(key_id not in {key.key_id for key in keys}, Code.POLICY)
        public_key = unbase64(row["public_key"], 32, Code.POLICY)
        allowed = labels(row["profiles"])
        require(set(allowed) <= set(profiles), Code.POLICY)
        start = integer(row["not_before"], code=Code.POLICY)
        end = integer(row["not_after"], code=Code.POLICY)
        require(start < end and type(row["revoked"]) is bool, Code.POLICY)
        keys.append(Key(key_id, public_key, allowed, start, end, cast(bool, row["revoked"])))
    return Policy(repo_id, repo_name, profiles, tuple(keys), digest(canonical(obj)))


@dataclass(frozen=True)
class Blob:
    path: str
    mode: str
    data: bytes


@dataclass(frozen=True)
class Change:
    path: str
    status: str


@dataclass(frozen=True)
class Snapshot:
    """Fixture/adapter input, not proof of actual GitHub state or Git object identity."""

    repository_id: int
    repository_name: str
    head_repository_id: int
    pr_number: int
    state: str
    base_branch: str
    current_main: str
    base_sha: str
    head_sha: str
    parents: tuple[str, ...]
    base_files: tuple[Blob, ...]
    head_files: tuple[Blob, ...]
    changes: tuple[Change, ...]
    complete: bool


def _files(files: tuple[Blob, ...]) -> dict[str, Blob]:
    require(type(files) is tuple and len(files) <= 5000, Code.CANDIDATE)
    result: dict[str, Blob] = {}
    size = 0
    for file in files:
        require(type(file) is Blob, Code.CANDIDATE)
        path = string(file.path, r"[A-Za-z0-9_.\-/]+", Code.CANDIDATE)
        require(len(path) <= 4096, Code.CANDIDATE)
        require(all(part not in ("", ".", "..") for part in path.split("/")), Code.CANDIDATE)
        require(path not in result and file.mode in ("100644", "100755"), Code.CANDIDATE)
        require(type(file.data) is bytes and len(file.data) <= 5 * 1048576, Code.CANDIDATE)
        size += len(file.data)
        require(size <= 50 * 1048576, Code.CANDIDATE)
        result[path] = file
    for path in result:
        parts = path.split("/")
        require(
            all("/".join(parts[:index]) not in result for index in range(1, len(parts))),
            Code.CANDIDATE,
        )
    return result


def candidate_digest(snapshot: Snapshot) -> str:
    require(type(snapshot) is Snapshot, Code.BLOCKED)
    require(snapshot.complete is True, Code.BLOCKED)
    before, after = _files(snapshot.base_files), _files(snapshot.head_files)
    require(set(before) <= set(after), Code.CANDIDATE)
    changed = {path for path in after if before.get(path) != after[path]}
    require(bool(changed) and changed <= ALLOWED, Code.CANDIDATE)
    require(
        type(snapshot.changes) is tuple and len(snapshot.changes) == len(changed), Code.CANDIDATE
    )
    seen: set[str] = set()
    for change in snapshot.changes:
        require(type(change) is Change, Code.CANDIDATE)
        require(type(change.path) is str and change.path in changed, Code.CANDIDATE)
        require(change.path not in seen, Code.CANDIDATE)
        require(change.status == ("modified" if change.path in before else "added"), Code.CANDIDATE)
        seen.add(change.path)
    # Existing empty scaffolding is not release data. It must be byte-for-byte
    # unchanged in both authenticated trees; never expand the App write set.
    if PLACEHOLDER in after:
        inert = Blob(PLACEHOLDER, "100644", b"")
        require(before.get(PLACEHOLDER) == after[PLACEHOLDER] == inert, Code.CANDIDATE)
    surface = {
        p
        for p in after
        if p != PLACEHOLDER
        and (p in MANDATORY or p == "data/aggregates" or p.startswith("data/aggregates/"))
    }
    require(surface <= ALLOWED and set(MANDATORY) <= surface, Code.CANDIDATE)
    require(bool(set(AGGREGATES) & surface), Code.CANDIDATE)
    descriptor: list[JSON] = []
    total = 0
    for path in sorted(surface):
        blob = after[path]
        require(blob.mode == "100644" and len(blob.data) <= LIMITS["file_bytes"], Code.CANDIDATE)
        total += len(blob.data)
        descriptor.append(
            {
                "path": path,
                "mode": blob.mode,
                "size": len(blob.data),
                "sha256": digest(blob.data),
            }
        )
    require(total <= LIMITS["candidate_bytes"], Code.CANDIDATE)
    return digest(canonical({"files": descriptor}))


def payload_from_bytes(raw: bytes) -> tuple[dict[str, JSON], bytes]:
    obj = object_fields(
        parse(raw, cap=LIMITS["body_bytes"], depth=2, arrays=False),
        frozenset(("payload", "signature")),
        Code.FORMAT,
    )
    payload = object_fields(obj["payload"], PAYLOAD_FIELDS, Code.FORMAT)
    require(integer(payload["version"]) == 1, Code.FORMAT)
    for field in ("repository_id", "pr_number"):
        integer(payload[field], positive=True)
    for field in ("scan_completed_at", "issued_at", "expires_at"):
        integer(payload[field])
    for field in ("base_sha", "head_sha"):
        string(payload[field], r"[0-9a-f]{40}")
    for field in ("candidate_sha256", "policy_sha256"):
        string(payload[field], r"[0-9a-f]{64}")
    string(payload["proof_id"], r"[0-9a-f]{32}")
    label(payload["key_id"])
    label(payload["profile_id"])
    return payload, unbase64(obj["signature"], 64)


def verify_signature(public_key: bytes, signature: bytes, message: bytes) -> None:
    require(type(public_key) is bytes and len(public_key) == 32, Code.SIGNATURE)
    require(type(signature) is bytes and len(signature) == 64, Code.SIGNATURE)
    try:
        Ed25519PublicKey.from_public_bytes(public_key).verify(signature, message)
    except InvalidSignature, ValueError:
        raise Refused(Code.SIGNATURE) from None
    except UnsupportedAlgorithm:
        raise Refused(Code.BLOCKED) from None


@dataclass(frozen=True)
class Verdict:
    pr_number: int
    head_sha: str
    mode: str = "offline-only"
    result: str = "attestation-valid-at-check-time"
    publication_authorized: bool = False


def verify_offline(raw: bytes, policy_bytes: bytes, snapshot: Snapshot, now: int) -> Verdict:
    """Admission-mode core only. No live reads, state reread, deployment or side effects."""
    integer(now, code=Code.BLOCKED)
    require(type(snapshot) is Snapshot, Code.BLOCKED)
    policy = policy_from_bytes(policy_bytes)
    payload, signature = payload_from_bytes(raw)
    require(payload["policy_sha256"] == policy.sha256, Code.POLICY)
    require(payload["profile_id"] in policy.profiles, Code.POLICY)
    matches = [key for key in policy.keys if key.key_id == payload["key_id"]]
    require(len(matches) == 1, Code.POLICY)
    key = matches[0]
    require(not key.revoked and payload["profile_id"] in key.profiles, Code.POLICY)
    verify_signature(key.public_key, signature, DOMAIN + canonical(payload))
    scan = integer(payload["scan_completed_at"])
    issued = integer(payload["issued_at"])
    expiry = integer(payload["expires_at"])
    require(scan <= issued < expiry, Code.TIME)
    require(expiry - scan <= LIMITS["scan_lifetime"], Code.TIME)
    require(issued - scan <= LIMITS["sign_delay"], Code.TIME)
    require(scan <= now + LIMITS["clock_skew"] and issued <= now + LIMITS["clock_skew"], Code.TIME)
    require(now < expiry, Code.TIME)
    require(key.not_before <= issued < key.not_after, Code.TIME)
    require(key.not_before <= now < key.not_after, Code.TIME)
    require(snapshot.complete is True, Code.BLOCKED)
    integer(snapshot.repository_id, positive=True, code=Code.TARGET)
    integer(snapshot.head_repository_id, positive=True, code=Code.TARGET)
    integer(snapshot.pr_number, positive=True, code=Code.TARGET)
    for sha in (snapshot.current_main, snapshot.base_sha, snapshot.head_sha):
        string(sha, r"[0-9a-f]{40}", Code.TARGET)
    require(snapshot.repository_id == policy.repository_id == payload["repository_id"], Code.TARGET)
    require(snapshot.head_repository_id == policy.repository_id, Code.TARGET)
    require(snapshot.repository_name == policy.repository_name, Code.TARGET)
    require(snapshot.pr_number == payload["pr_number"], Code.TARGET)
    require(snapshot.state == "open" and snapshot.base_branch == "main", Code.TARGET)
    require(snapshot.current_main == snapshot.base_sha == payload["base_sha"], Code.TARGET)
    require(snapshot.head_sha == payload["head_sha"], Code.TARGET)
    require(snapshot.head_sha != snapshot.base_sha, Code.TARGET)
    require(snapshot.parents == (snapshot.base_sha,), Code.TARGET)
    require(candidate_digest(snapshot) == payload["candidate_sha256"], Code.CANDIDATE)
    return Verdict(snapshot.pr_number, snapshot.head_sha)
