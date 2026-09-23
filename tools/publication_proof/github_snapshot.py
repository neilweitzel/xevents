"""Read-only GitHub admission snapshots. No signer, merge, status or deploy API.

The trusted runner supplies its own installed code and authenticated gh/git
environment. Candidate content is read as bytes, never checked out or executed.
"""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Protocol, cast

import proof

REPOSITORY = "neilweitzel/xevents"
REPOSITORY_ID = 1378759643
MAX_FILES = 5000
MAX_ENTRIES = 10000
MAX_TREE_BYTES = 50 * 1048576
MAX_BLOB = 5 * 1048576
MAX_METADATA = 1048576
SHA = re.compile(r"[0-9a-f]{40}")


class SnapshotRefused(ValueError):
    """Fixed diagnostics only; never include PR bodies or command stderr."""


def need(condition: bool, code: str) -> None:
    if not condition:
        raise SnapshotRefused(code)


def oid(value: object) -> str:
    need(isinstance(value, str) and SHA.fullmatch(value) is not None, "object_identity")
    return cast(str, value)


def record(value: object) -> dict[str, object]:
    need(type(value) is dict, "metadata_shape")
    return cast(dict[str, object], value)


def number(value: object) -> int:
    need(type(value) is int and 0 < value <= proof.SAFE_INT, "metadata_shape")
    return cast(int, value)


class API(Protocol):
    def __call__(self, path: str) -> dict[str, object]: ...


class Objects(Protocol):
    def prepare(self, base: str, head: str) -> None: ...
    def read(self, kind: str, object_id: str, maximum: int) -> bytes: ...


def command(args: list[str], maximum: int) -> bytes:
    try:
        result = subprocess.run(args, capture_output=True, check=False, timeout=120)
    except OSError, subprocess.SubprocessError:
        raise SnapshotRefused("transport_unavailable") from None
    need(result.returncode == 0 and len(result.stdout) <= maximum, "transport_unavailable")
    return result.stdout


def _pairs(items: list[tuple[str, object]]) -> dict[str, object]:
    result: dict[str, object] = {}
    for key, value in items:
        need(key not in result, "metadata_shape")
        result[key] = value
    return result


def github_api(path: str) -> dict[str, object]:
    # Paths are constructed here, not obtained from candidate-provided URLs.
    need(
        re.fullmatch(
            rf"repos/{re.escape(REPOSITORY)}(?:/pulls/[1-9][0-9]*|/git/ref/heads/main)?",
            path,
        )
        is not None,
        "transport_target",
    )
    # Host/authentication come from the trusted runner, including its approved
    # proxy when present. Never override that route or accept a host from a PR.
    raw = command(["gh", "api", "--method", "GET", path], MAX_METADATA)
    try:
        return record(json.loads(raw, object_pairs_hook=_pairs))
    except ValueError, UnicodeError, RecursionError:
        raise SnapshotRefused("metadata_shape") from None


class GitObjects:
    """Fresh bare object database; fixed HTTPS remote, no working tree."""

    def __init__(self, directory: Path):
        self.root = directory
        need(not directory.exists(), "object_store_exists")
        command(["git", "init", "--bare", "--template=", str(directory)], MAX_METADATA)

    def git(self, *args: str, maximum: int = MAX_METADATA) -> bytes:
        return command(
            [
                "git",
                "-c",
                "core.hooksPath=/dev/null",
                "-c",
                "protocol.file.allow=never",
                "-c",
                "protocol.ext.allow=never",
                "-c",
                "fetch.fsckObjects=true",
                "-c",
                "transfer.fsckObjects=true",
                "--git-dir",
                str(self.root),
                *args,
            ],
            maximum,
        )

    def prepare(self, base: str, head: str) -> None:
        self.git(
            "fetch",
            "--quiet",
            "--no-tags",
            "--depth=1",
            "--no-recurse-submodules",
            f"https://github.com/{REPOSITORY}.git",
            oid(base),
            oid(head),
        )

    def read(self, kind: str, object_id: str, maximum: int) -> bytes:
        need(kind in ("commit", "tree", "blob"), "object_type")
        object_id = oid(object_id)
        need(self.git("cat-file", "-t", object_id).strip() == kind.encode(), "object_type")
        size = self.git("cat-file", "-s", object_id).strip()
        need(size.isdigit() and int(size) <= maximum, "object_size")
        raw = self.git("cat-file", kind, object_id, maximum=maximum)
        need(len(raw) == int(size), "object_size")
        return raw


def verified(objects: Objects, kind: str, object_id: str, maximum: int) -> bytes:
    raw = objects.read(kind, oid(object_id), maximum)
    need(type(raw) is bytes and len(raw) <= maximum, "object_size")
    # Git's SHA-1 object identity is checked in addition to fetch.fsckObjects.
    # The publication descriptor independently uses SHA-256 for raw file bytes.
    actual = hashlib.sha1(f"{kind} {len(raw)}\0".encode() + raw).hexdigest()
    need(actual == object_id, "object_identity")
    return raw


def commit(objects: Objects, object_id: str) -> tuple[str, tuple[str, ...]]:
    raw = verified(objects, "commit", object_id, 262144)
    need(b"\n\n" in raw, "commit_shape")
    headers = raw.split(b"\n\n", 1)[0].split(b"\n")
    trees = [line[5:] for line in headers if line.startswith(b"tree ")]
    parents = [line[7:] for line in headers if line.startswith(b"parent ")]
    need(len(trees) == 1 and headers[0] == b"tree " + trees[0], "commit_shape")
    try:
        return oid(trees[0].decode("ascii")), tuple(oid(p.decode("ascii")) for p in parents)
    except UnicodeError:
        raise SnapshotRefused("commit_shape") from None


def files(objects: Objects, tree_id: str) -> tuple[proof.Blob, ...]:
    """Read and hash every entry, including unchanged, non-boundary files."""
    result: list[proof.Blob] = []
    entries = 0
    total = 0

    def walk(tree: str, prefix: str, depth: int) -> None:
        nonlocal entries, total
        need(depth <= 64, "tree_limit")
        raw = verified(objects, "tree", tree, MAX_METADATA)
        position = 0
        seen: set[str] = set()
        ordering: list[bytes] = []
        while position < len(raw):
            space = raw.find(b" ", position)
            end = raw.find(b"\0", space + 1)
            need(space > position and end > space and end + 21 <= len(raw), "tree_shape")
            mode = raw[position:space]
            name = raw[space + 1 : end]
            child = raw[end + 1 : end + 21].hex()
            position = end + 21
            entries += 1
            need(entries <= MAX_ENTRIES, "tree_limit")
            need(re.fullmatch(rb"[A-Za-z0-9_.-]+", name) is not None, "tree_path")
            part = name.decode("ascii")
            need(part not in ("", ".", "..") and part not in seen, "tree_path")
            seen.add(part)
            path = prefix + part
            need(len(path) <= 4096, "tree_path")
            need(mode in (b"40000", b"100644", b"100755"), "tree_mode")
            ordering.append(name + (b"/" if mode == b"40000" else b""))
            if mode == b"40000":
                walk(child, path + "/", depth + 1)
            else:
                need(len(result) < MAX_FILES, "tree_limit")
                data = verified(objects, "blob", child, MAX_BLOB)
                total += len(data)
                need(total <= MAX_TREE_BYTES, "tree_limit")
                result.append(proof.Blob(path, mode.decode(), data))
        need(ordering == sorted(ordering), "tree_order")

    walk(oid(tree_id), "", 0)
    return tuple(sorted(result, key=lambda item: item.path))


@dataclass(frozen=True)
class State:
    number: int
    base: str
    head: str
    branch: str
    body: bytes
    changed_files: int


def observe(api: API, pr_number: int) -> State:
    number(pr_number)
    repo = api(f"repos/{REPOSITORY}")
    need(
        number(repo.get("id")) == REPOSITORY_ID
        and repo.get("full_name") == REPOSITORY
        and repo.get("private") is False,
        "repository_identity",
    )
    pr = api(f"repos/{REPOSITORY}/pulls/{pr_number}")
    need(
        number(pr.get("number")) == pr_number
        and pr.get("state") == "open"
        and pr.get("merged") is False
        and pr.get("draft") is False
        and number(pr.get("commits")) == 1,
        "pr_state",
    )
    base, head = record(pr.get("base")), record(pr.get("head"))
    for side in (base, head):
        identity = record(side.get("repo"))
        need(
            number(identity.get("id")) == REPOSITORY_ID
            and identity.get("full_name") == REPOSITORY
            and identity.get("private") is False,
            "repository_identity",
        )
    need(base.get("ref") == "main", "pr_state")
    branch = head.get("ref")
    need(isinstance(branch, str) and 0 < len(branch) <= 255, "pr_state")
    body = pr.get("body")
    need(isinstance(body, str), "proof_body")
    try:
        body_bytes = cast(str, body).encode("utf-8")
    except UnicodeError:
        raise SnapshotRefused("proof_body") from None
    need(len(body_bytes) <= proof.LIMITS["body_bytes"], "proof_body")
    changed = number(pr.get("changed_files"))
    need(changed <= len(proof.ALLOWED), "diff_incomplete")
    reference = api(f"repos/{REPOSITORY}/git/ref/heads/main")
    obj = record(reference.get("object"))
    need(
        reference.get("ref") == "refs/heads/main"
        and obj.get("type") == "commit"
        and oid(obj.get("sha")) == oid(base.get("sha")),
        "base_changed",
    )
    need(base["sha"] != head.get("sha"), "pr_state")
    return State(
        pr_number, oid(base["sha"]), oid(head.get("sha")), cast(str, branch), body_bytes, changed
    )


@dataclass(frozen=True)
class Admission:
    snapshot: proof.Snapshot
    state: State
    candidate_sha256: str
    publication_authorized: bool = False


def read_admission(api: API, objects: Objects, pr_number: int) -> Admission:
    """Authenticate immutable content and reread mutable metadata. No authorization."""
    before = observe(api, pr_number)
    objects.prepare(before.base, before.head)
    base_tree, _ = commit(objects, before.base)
    head_tree, parents = commit(objects, before.head)
    need(parents == (before.base,), "commit_shape")
    base_files, head_files = files(objects, base_tree), files(objects, head_tree)
    old = {blob.path: blob for blob in base_files}
    new = {blob.path: blob for blob in head_files}
    need(set(old) <= set(new), "candidate_shape")
    changes = tuple(
        proof.Change(path, "modified" if path in old else "added")
        for path in sorted(new)
        if old.get(path) != new[path]
    )
    need(len(changes) == before.changed_files, "diff_incomplete")
    snapshot = proof.Snapshot(
        REPOSITORY_ID,
        REPOSITORY,
        REPOSITORY_ID,
        pr_number,
        "open",
        "main",
        before.base,
        before.base,
        before.head,
        parents,
        base_files,
        head_files,
        changes,
        True,
    )
    try:
        candidate = proof.candidate_digest(snapshot)
    except proof.Refused:
        raise SnapshotRefused("candidate_shape") from None
    need(observe(api, pr_number) == before, "state_changed")
    return Admission(snapshot, before, candidate)


class PolicyReader(Protocol):
    """Trusted runner selects current approved policy independently of the PR."""

    def __call__(self) -> bytes: ...


class Clock(Protocol):
    def __call__(self) -> int: ...


def check_admission(
    api: API, objects: Objects, pr_number: int, policy_reader: PolicyReader, clock: Clock
) -> proof.Verdict:
    """Point-in-time verification, not a merge/deploy instruction or safe-key registry."""
    policy = policy_reader()
    start = clock()
    proof.integer(start, code=proof.Code.BLOCKED)
    admitted = read_admission(api, objects, pr_number)
    proof.verify_offline(admitted.state.body, policy, admitted.snapshot, start)
    need(policy_reader() == policy, "policy_changed")
    need(observe(api, pr_number) == admitted.state, "state_changed")
    end = clock()
    proof.integer(end, code=proof.Code.BLOCKED)
    need(end >= start, "clock_changed")
    # Rerun expiry/key validity after all reads, not at the beginning of I/O.
    return proof.verify_offline(admitted.state.body, policy, admitted.snapshot, end)


def main() -> int:
    import argparse

    parser = argparse.ArgumentParser(description="Read-only public snapshot diagnostic")
    parser.add_argument("--pr", type=int, required=True)
    args = parser.parse_args()
    try:
        with tempfile.TemporaryDirectory(prefix="xevents-public-objects-") as directory:
            result = read_admission(github_api, GitObjects(Path(directory) / "objects"), args.pr)
        print(
            json.dumps(
                {
                    "result": "snapshot-validated-read-only",
                    "candidate_sha256": result.candidate_sha256,
                    "publication_authorized": False,
                }
            )
        )
        return 0
    except Exception:
        # No traceback, command stderr, object names or attacker-controlled values.
        print('{"result":"snapshot-refused","publication_authorized":false}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
