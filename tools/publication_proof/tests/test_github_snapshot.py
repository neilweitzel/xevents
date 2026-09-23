"""Synthetic Git objects and authenticated-transport substitutes; no network."""

import base64
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey
from test_proof import NOW, SEED, VECTOR, wire

import github_snapshot as g
import proof as p


def object_id(kind, raw):
    return hashlib.sha1(f"{kind} {len(raw)}\0".encode() + raw).hexdigest()


class Objects:
    def __init__(self):
        self.values = {}
        self.prepared = None

    def add(self, kind, data):
        oid = object_id(kind, data)
        self.values[oid] = (kind, data)
        return oid

    def tree(self, entries):
        rows = []
        for mode, name, oid in sorted(
            entries, key=lambda e: e[1] + ("/" if e[0] == "40000" else "")
        ):
            rows.append(mode.encode() + b" " + name.encode() + b"\0" + bytes.fromhex(oid))
        return self.add("tree", b"".join(rows))

    def commit(self, tree, parents=()):
        raw = f"tree {tree}\n" + "".join(f"parent {p}\n" for p in parents)
        raw += "author Synthetic <test@example.invalid> 1 +0000\n"
        raw += "committer Synthetic <test@example.invalid> 1 +0000\n\nSynthetic fixture\n"
        return self.add("commit", raw.encode())

    def read(self, kind, oid, maximum):
        actual, raw = self.values[oid]
        assert actual == kind
        return raw

    def prepare(self, base, head):
        self.prepared = base, head


class Fixture:
    def __init__(self):
        self.objects = Objects()
        o = self.objects
        code = o.add("blob", b"Unchanged inert code\n")
        self.base_tree = o.tree([("100644", "README.md", code)])
        self.base = o.commit(self.base_tree)
        ag = o.tree([("100644", "view1.jsonl", o.add("blob", b"Aggregate fixture\n"))])
        data = o.tree([("40000", "aggregates", ag)])
        self.entries = [
            ("100644", "README.md", code),
            ("40000", "data", data),
            ("100644", "evidence-manifest.jsonl", o.add("blob", b"Manifest fixture\n")),
            ("100644", "coverage-boundary-statement.md", o.add("blob", b"Coverage fixture\n")),
        ]
        self.head = o.commit(o.tree(self.entries), (self.base,))
        identity = {"id": g.REPOSITORY_ID, "full_name": g.REPOSITORY, "private": False}
        self.repo = copy.deepcopy(identity)
        self.pr = {
            "number": 7,
            "state": "open",
            "merged": False,
            "draft": False,
            "commits": 1,
            "changed_files": 3,
            "body": "{}",
            "base": {"sha": self.base, "ref": "main", "repo": copy.deepcopy(identity)},
            "head": {
                "sha": self.head,
                "ref": "boundary/synthetic",
                "repo": copy.deepcopy(identity),
            },
        }
        self.ref = {"ref": "refs/heads/main", "object": {"type": "commit", "sha": self.base}}
        self.calls = []
        self.mutation = None

    def api(self, path):
        self.calls.append(path)
        if self.mutation:
            self.mutation(self)
        choices = {
            f"repos/{g.REPOSITORY}": self.repo,
            f"repos/{g.REPOSITORY}/pulls/7": self.pr,
            f"repos/{g.REPOSITORY}/git/ref/heads/main": self.ref,
        }
        return copy.deepcopy(choices[path])

    def read(self):
        return g.read_admission(self.api, self.objects, 7)

    def signed(self):
        admitted = self.read()
        self.calls.clear()
        policy = copy.deepcopy(VECTOR["policy"])
        policy.update(repository_id=g.REPOSITORY_ID, repository_name=g.REPOSITORY)
        payload = copy.deepcopy(VECTOR["payload"])
        payload.update(
            repository_id=g.REPOSITORY_ID,
            base_sha=self.base,
            head_sha=self.head,
            candidate_sha256=admitted.candidate_sha256,
            policy_sha256=p.digest(p.canonical(policy)),
        )
        sig = Ed25519PrivateKey.from_private_bytes(SEED).sign(p.DOMAIN + p.canonical(payload))
        self.pr["body"] = json.dumps(
            {
                "payload": payload,
                "signature": base64.urlsafe_b64encode(sig).rstrip(b"=").decode(),
            }
        )
        return wire(policy)


def test_full_authentic_objects_and_snapshot_bind_to_existing_core():
    f = Fixture()
    policy = f.signed()
    verdict = g.check_admission(f.api, f.objects, 7, lambda: policy, lambda: NOW)
    assert verdict.publication_authorized is False
    assert verdict.head_sha == f.head
    assert len(f.calls) == 9
    assert f.objects.prepared == (f.base, f.head)
    assert len(f.read().snapshot.head_files) == 4


@pytest.mark.parametrize(
    "location,field,value",
    [
        ("repo", "id", 1),
        ("repo", "private", True),
        ("repo", "full_name", "wrong/repo"),
        ("pr", "number", True),
        ("pr", "number", 8),
        ("pr", "state", "closed"),
        ("pr", "merged", True),
        ("pr", "draft", True),
        ("pr", "commits", 2),
        ("pr", "changed_files", 2),
        ("pr", "changed_files", 5),
        ("pr", "changed_files", True),
        ("pr", "body", None),
        ("pr", "body", "x" * 8193),
        ("pr", "body", "\ud800"),
        ("ref", "ref", "refs/heads/other"),
    ],
)
def test_metadata_and_incomplete_diff_refused(location, field, value):
    f = Fixture()
    getattr(f, location)[field] = value
    with pytest.raises(g.SnapshotRefused):
        f.read()


@pytest.mark.parametrize(
    "side,field,value",
    [
        ("head", "repo", None),
        ("head", "ref", ""),
        ("head", "sha", "x" * 40),
        ("base", "sha", "a" * 40),
        ("base", "ref", "other"),
        ("head", "repo", {"id": 9, "full_name": g.REPOSITORY, "private": False}),
        ("head", "repo", {"id": g.REPOSITORY_ID, "full_name": "other/repo", "private": False}),
    ],
)
def test_fork_and_wrong_refs_refused(side, field, value):
    f = Fixture()
    f.pr[side][field] = value
    with pytest.raises(g.SnapshotRefused):
        f.read()


@pytest.mark.parametrize("change", ["body", "head", "main", "closed", "draft", "branch", "count"])
def test_mutable_state_is_reread_after_object_reconstruction(change):
    f = Fixture()

    def mutate(f):
        if len(f.calls) == 4:
            if change == "main":
                f.ref["object"]["sha"] = "c" * 40
            elif change == "head":
                f.pr["head"]["sha"] = "d" * 40
            elif change == "branch":
                f.pr["head"]["ref"] = "changed"
            else:
                field, value = {
                    "body": ("body", '{"changed":true}'),
                    "closed": ("state", "closed"),
                    "draft": ("draft", True),
                    "count": ("changed_files", 4),
                }[change]
                f.pr[field] = value

    f.mutation = mutate
    with pytest.raises(g.SnapshotRefused):
        f.read()


def test_policy_revocation_and_late_expiry_block_after_reads():
    f = Fixture()
    policy = f.signed()
    values = iter((policy, policy + b" "))
    with pytest.raises(g.SnapshotRefused, match="policy_changed"):
        g.check_admission(f.api, f.objects, 7, lambda: next(values), lambda: NOW)
    for final in (NOW - 1, VECTOR["payload"]["expires_at"]):
        clocks = iter((NOW, final))
        with pytest.raises((g.SnapshotRefused, p.Refused)):
            g.check_admission(f.api, f.objects, 7, lambda: policy, lambda: next(clocks))


def test_body_edit_at_final_checkpoint_is_not_a_cached_success():
    f = Fixture()
    policy = f.signed()

    def mutate(f):
        if len(f.calls) == 7:
            f.pr["body"] = "{}"

    f.mutation = mutate
    with pytest.raises(g.SnapshotRefused, match="state_changed"):
        g.check_admission(f.api, f.objects, 7, lambda: policy, lambda: NOW)


@pytest.mark.parametrize("kind", ["commit", "tree", "blob"])
def test_wrong_object_bytes_cannot_claim_the_requested_git_identity(kind):
    f = Fixture()
    target = next(oid for oid, (k, _) in f.objects.values.items() if k == kind)
    actual, raw = f.objects.values[target]
    f.objects.values[target] = actual, raw + b"corrupt"
    with pytest.raises(g.SnapshotRefused, match="object_identity"):
        f.read()


@pytest.mark.parametrize("mode", ["120000", "160000", "100600"])
def test_symlinks_submodules_and_invalid_modes_refused(mode):
    f = Fixture()
    oid = f.objects.tree([(mode, "unsafe", f.objects.add("blob", b"x"))])
    with pytest.raises(g.SnapshotRefused, match="tree_mode"):
        g.files(f.objects, oid)


@pytest.mark.parametrize("name", ["..", ".", "bad/name", "bad\nname", "unicodé"])
def test_unsafe_tree_paths_refused(name):
    f = Fixture()
    tree = f.objects.tree([("100644", name, f.objects.add("blob", b"x"))])
    with pytest.raises(g.SnapshotRefused, match="tree_path"):
        g.files(f.objects, tree)


def test_duplicate_unsorted_and_truncated_trees_refused():
    f = Fixture()
    blob = f.objects.add("blob", b"x")

    def row(name):
        return b"100644 " + name + b"\0" + bytes.fromhex(blob)

    for raw in (row(b"x") + row(b"x"), row(b"z") + row(b"a"), row(b"x")[:-1]):
        tree = f.objects.add("tree", raw)
        with pytest.raises(g.SnapshotRefused):
            g.files(f.objects, tree)


@pytest.mark.parametrize(
    "limit,value",
    [
        ("MAX_FILES", 0),
        ("MAX_ENTRIES", 1),
        ("MAX_TREE_BYTES", 1),
        ("MAX_BLOB", 1),
    ],
)
def test_local_resource_limits_never_truncate_to_success(limit, value):
    f = Fixture()
    with patch.object(g, limit, value), pytest.raises(g.SnapshotRefused):
        f.read()


def test_mixed_code_deletion_and_merge_commit_refused():
    for kind in ("code", "delete", "merge"):
        f = Fixture()
        entries = f.entries[:]
        if kind == "code":
            entries[0] = ("100644", "README.md", f.objects.add("blob", b"changed"))
            f.pr["changed_files"] = 4
        if kind == "delete":
            entries = entries[1:]
        parents = (f.base, "a" * 40) if kind == "merge" else (f.base,)
        f.pr["head"]["sha"] = f.objects.commit(f.objects.tree(entries), parents)
        with pytest.raises(g.SnapshotRefused):
            f.read()


def test_unchanged_boundary_bytes_are_also_reconstructed():
    f = Fixture()
    f.pr["head"]["sha"] = f.objects.commit(f.objects.tree(f.entries), (f.head,))
    f.pr["base"]["sha"] = f.ref["object"]["sha"] = f.head
    # Identical tree is not a data change, despite a claimed files count.
    with pytest.raises(g.SnapshotRefused, match="diff_incomplete"):
        f.read()


def test_transport_is_fixed_read_only_and_sanitizes_errors():
    with patch.object(g, "command", return_value=b'{"id":1}') as run:
        assert g.github_api(f"repos/{g.REPOSITORY}") == {"id": 1}
        args = run.call_args.args[0]
        assert args == [
            "gh",
            "api",
            "--method",
            "GET",
            f"repos/{g.REPOSITORY}",
        ]
    for path in ("https://evil.invalid", "repos/other/private", f"repos/{g.REPOSITORY}/issues"):
        with pytest.raises(g.SnapshotRefused, match="transport_target"):
            g.github_api(path)
    for raw in (b"invalid", b'{"id":1,"id":2}', b"[]", b"\xff"):
        with patch.object(g, "command", return_value=raw), pytest.raises(g.SnapshotRefused):
            g.github_api(f"repos/{g.REPOSITORY}")
    with patch.object(g.subprocess, "run", side_effect=OSError("PRIVATE_CANARY")):
        with pytest.raises(g.SnapshotRefused, match="^transport_unavailable$"):
            g.command(["gh"], 10)


def test_cli_failure_never_prints_exception_or_claims_authorization(capsys):
    with (
        patch("sys.argv", ["snapshot", "--pr", "7"]),
        patch.object(g, "GitObjects", side_effect=ValueError("PRIVATE_CANARY")),
    ):
        assert g.main() == 1
    output = capsys.readouterr()
    assert output.err == ""
    assert json.loads(output.out) == {"result": "snapshot-refused", "publication_authorized": False}


def test_real_bare_git_objects_reconstruct_full_signed_snapshot(tmp_path):
    f = Fixture()
    policy = f.signed()
    store = g.GitObjects(tmp_path / "objects")
    for oid, (kind, raw) in f.objects.values.items():
        actual = (
            subprocess.run(
                ["git", "--git-dir", str(store.root), "hash-object", "-w", "-t", kind, "--stdin"],
                input=raw,
                capture_output=True,
                check=True,
            )
            .stdout.strip()
            .decode()
        )
        assert actual == oid
    # The object transport is real; only the network fetch is substituted.
    with patch.object(store, "prepare") as fetch:
        verdict = g.check_admission(f.api, store, 7, lambda: policy, lambda: NOW)
        fetch.assert_called_once_with(f.base, f.head)
    assert verdict.publication_authorized is False
    assert verdict.head_sha == f.head
    with pytest.raises(g.SnapshotRefused, match="object_store_exists"):
        g.GitObjects(store.root)
    with pytest.raises(g.SnapshotRefused, match="object_type"):
        store.read("blob", f.base, g.MAX_METADATA)
    with pytest.raises(g.SnapshotRefused, match="object_size"):
        store.read("commit", f.base, 1)
    with pytest.raises(g.SnapshotRefused, match="transport_unavailable"):
        store.read("blob", "a" * 40, 10)
    assert not (store.root / "hooks").exists()


def test_git_fetch_is_fixed_https_and_never_checks_out_candidate(tmp_path):
    f = Fixture()
    with patch.object(g, "command", return_value=b"") as command:
        store = g.GitObjects(tmp_path / "objects")
        store.prepare(f.base, f.head)
        args = command.call_args.args[0]
        assert args[-8:] == [
            "fetch",
            "--quiet",
            "--no-tags",
            "--depth=1",
            "--no-recurse-submodules",
            f"https://github.com/{g.REPOSITORY}.git",
            f.base,
            f.head,
        ]
        assert "core.hooksPath=/dev/null" in args
        assert "fetch.fsckObjects=true" in args
        assert "protocol.file.allow=never" in args
        assert "protocol.ext.allow=never" in args
        assert not any("checkout" in arg for arg in args)
        with pytest.raises(g.SnapshotRefused, match="object_identity"):
            store.prepare("--upload-pack=evil", f.head)
        assert command.call_count == 2


@pytest.mark.parametrize("failure", ["timeout", "exit", "oversized"])
def test_command_failure_is_fixed_and_never_partial_success(failure):
    kwargs = (
        {"side_effect": subprocess.TimeoutExpired("PRIVATE_CANARY", 120)}
        if failure == "timeout"
        else {
            "return_value": subprocess.CompletedProcess(
                ["git"],
                1 if failure == "exit" else 0,
                b"x" * (11 if failure == "oversized" else 0),
                b"PRIVATE_CANARY",
            )
        }
    )
    with patch.object(g.subprocess, "run", **kwargs):
        with pytest.raises(g.SnapshotRefused, match="^transport_unavailable$"):
            g.command(["git"], 10)


@pytest.mark.parametrize("stage", ["first_api", "objects", "second_api", "final_api", "policy"])
def test_interrupted_reads_never_return_a_verdict(stage):
    f = Fixture()
    policy = f.signed()

    def api(path):
        next_call = len(f.calls) + 1
        if next_call == {"first_api": 1, "second_api": 4, "final_api": 7}.get(stage):
            raise g.SnapshotRefused("transport_unavailable")
        return f.api(path)

    calls = 0

    def policies():
        nonlocal calls
        calls += 1
        if stage == "policy" and calls == 2:
            raise g.SnapshotRefused("transport_unavailable")
        return policy

    if stage == "objects":
        del f.objects.values[f.base]
    with pytest.raises((g.SnapshotRefused, KeyError)):
        g.check_admission(api, f.objects, 7, policies, lambda: NOW)


def test_commit_header_shape_and_depth_limits():
    f = Fixture()
    for raw in (
        b"no header separator",
        b"author first\ntree " + f.base_tree.encode() + b"\n\nmessage",
        b"tree " + f.base_tree.encode() + b"\ntree " + f.base_tree.encode() + b"\n\nx",
        b"tree \xff\n\nx",
    ):
        bad = f.objects.add("commit", raw)
        with pytest.raises(g.SnapshotRefused):
            g.commit(f.objects, bad)
    tree = f.objects.tree([])
    for _ in range(65):
        tree = f.objects.tree([("40000", "nested", tree)])
    with pytest.raises(g.SnapshotRefused, match="tree_limit"):
        g.files(f.objects, tree)


def test_cli_snapshot_success_explicitly_not_authorization(capsys):
    f = Fixture()
    with (
        patch("sys.argv", ["snapshot", "--pr", "7"]),
        patch.object(g, "GitObjects", return_value=f.objects),
        patch.object(g, "github_api", side_effect=f.api),
    ):
        assert g.main() == 0
    result = json.loads(capsys.readouterr().out)
    assert result["result"] == "snapshot-validated-read-only"
    assert result["publication_authorized"] is False
    assert result["candidate_sha256"] == f.read().candidate_sha256


def test_executable_cli_rejects_invalid_pr_without_network():
    result = subprocess.run(
        [sys.executable, str(Path(g.__file__)), "--pr", "0"],
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 1
    assert result.stderr == b""
    assert json.loads(result.stdout) == {
        "result": "snapshot-refused",
        "publication_authorized": False,
    }
