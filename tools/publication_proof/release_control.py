"""Trusted-main admission and deployment checks. No private repository access."""
from __future__ import annotations

import argparse
import base64
import json
import os
import re
import tempfile
import time
from dataclasses import replace
from pathlib import Path
from typing import cast

import github_snapshot as g
import proof as p

POLICY_PATH = "config/publication-policy.json"
APP_LOGIN = "xevents-boundary[bot]"
CHECK_NAME = "Boundary admission"


def api(path: str) -> dict[str, object]:
    g.need(path.startswith(f"repos/{g.REPOSITORY}/") or path == f"repos/{g.REPOSITORY}",
           "transport_target")
    raw = g.command(["gh", "api", "--method", "GET", path], 1048576)
    return g.record(json.loads(raw, object_pairs_hook=g._pairs))


def policy() -> bytes:
    row = api(f"repos/{g.REPOSITORY}/contents/{POLICY_PATH}?ref=main")
    g.need(row.get("type") == "file" and row.get("encoding") == "base64", "policy_unavailable")
    value = row.get("content")
    g.need(isinstance(value, str), "policy_unavailable")
    raw = base64.b64decode(cast(str, value).replace("\n", ""), validate=True)
    trusted = p.policy_from_bytes(raw)
    g.need(trusted.repository_id == g.REPOSITORY_ID
           and trusted.repository_name == g.REPOSITORY, "policy_target")
    # Production trust root is generated separately, never a test vector or
    # permissively parsed small-order identity point.
    for key in trusted.keys:
        g.need(key.public_key not in (
            bytes(32), b"\x01" + bytes(31),
            bytes.fromhex("d75a980182b10ab7d54bfed3c964073a0ee172f3daa62325af021a68f707511a"),
        ), "unsafe_production_key")
    return raw


def app_pr(pr: dict[str, object], head: str) -> None:
    user = g.record(pr.get("user"))
    g.need(user.get("login") == APP_LOGIN and user.get("type") == "Bot", "app_identity")
    branch = g.record(pr.get("head")).get("ref")
    g.need(isinstance(branch, str)
           and re.fullmatch(r"xevents-release-[0-9]+-[0-9a-f]{12}", branch) is not None,
           "app_branch")
    commit = api(f"repos/{g.REPOSITORY}/commits/{g.oid(head)}")
    data = g.record(commit.get("commit"))
    g.need(g.record(data.get("verification")).get("verified") is True
           and g.record(commit.get("author")).get("login") == APP_LOGIN, "app_commit")


def controls() -> None:
    rules = api(f"repos/{g.REPOSITORY}/rulesets/23845612")
    g.need(rules.get("enforcement") == "active" and not rules.get("bypass_actors"),
           "native_protection")
    conditions = g.record(rules.get("conditions"))
    names = g.record(conditions.get("ref_name"))
    g.need(names.get("include") == ["refs/heads/main"] and names.get("exclude") == [],
           "native_protection")
    rows = rules.get("rules")
    g.need(isinstance(rows, list), "native_protection")
    mapped = {g.record(row).get("type"): g.record(row) for row in cast(list[object], rows)}
    g.need({"required_signatures", "pull_request", "deletion", "non_fast_forward",
            "required_status_checks"} <= set(mapped), "native_protection")
    parameters = g.record(mapped["required_status_checks"].get("parameters"))
    g.need(parameters.get("strict_required_status_checks_policy") is True,
           "native_protection")
    checks = parameters.get("required_status_checks")
    g.need(isinstance(checks, list) and any(
        g.record(check).get("context") == CHECK_NAME
        and g.record(check).get("integration_id") == 15368
        for check in cast(list[object], checks)), "native_protection")

def preflight() -> bytes:
    row = api(f"repos/{g.REPOSITORY}")
    g.need(row.get("id") == g.REPOSITORY_ID and row.get("full_name") == g.REPOSITORY
           and row.get("private") is False, "target")
    controls()
    return policy()


def exact_candidate(number: int, directory: Path) -> None:
    with tempfile.TemporaryDirectory(prefix="xevents-exact-") as temporary:
        admitted = g.read_admission(api, g.GitObjects(Path(temporary) / "objects"), number)
    expected = set(p.MANDATORY) | {"data/aggregates/view1.jsonl"}
    exported = {blob.path: blob.data for blob in admitted.snapshot.head_files
                if blob.path in p.ALLOWED}
    g.need(set(exported) == expected, "export_set")
    for name in expected:
        path = directory / name
        g.need(path.is_file() and not path.is_symlink() and path.stat().st_size <= 1048576,
               "export_file")
        g.need(path.read_bytes() == exported[name], "export_bytes")


def check_run(number: int) -> str:
    """Publish a head-bound check explicitly; target workflows run on base SHA."""
    pr = api(f"repos/{g.REPOSITORY}/pulls/{number}")
    head = g.oid(g.record(pr.get("head")).get("sha"))
    request = {"name": CHECK_NAME, "head_sha": head, "status": "in_progress"}
    run = json.loads(g.command(
        ["gh", "api", "--method", "POST", f"repos/{g.REPOSITORY}/check-runs",
         "-f", f"name={CHECK_NAME}", "-f", f"head_sha={head}", "-f", "status=in_progress"],
        1048576))
    identifier = g.number(g.record(run).get("id"))
    result, conclusion = "release-refused", "failure"
    try:
        result = classify(number)
        again = api(f"repos/{g.REPOSITORY}/pulls/{number}")
        g.need(g.record(again.get("head")).get("sha") == request["head_sha"], "state_changed")
        conclusion = "success"
    finally:
        g.command(["gh", "api", "--method", "PATCH",
                   f"repos/{g.REPOSITORY}/check-runs/{identifier}",
                   "-f", "status=completed", "-f", f"conclusion={conclusion}"], 1048576)
    return result


def admission(number: int) -> p.Verdict:
    with tempfile.TemporaryDirectory(prefix="xevents-admission-") as temporary:
        objects = g.GitObjects(Path(temporary) / "objects")
        pr = api(f"repos/{g.REPOSITORY}/pulls/{number}")
        app_pr(pr, g.oid(g.record(pr.get("head")).get("sha")))
        return g.check_admission(api, objects, number, policy, lambda: int(time.time()))


def boundary_paths(changed: set[str]) -> bool:
    return any(path in p.MANDATORY or path == "data/aggregates"
               or path.startswith("data/aggregates/") for path in changed)


def classify(number: int) -> str:
    """Code-only PRs pass routing; any boundary changes require the full proof."""
    pr = api(f"repos/{g.REPOSITORY}/pulls/{number}")
    g.need(pr.get("state") == "open" and pr.get("merged") is False, "pr_state")
    base, head = g.record(pr.get("base")), g.record(pr.get("head"))
    g.need(base.get("ref") == "main"
           and g.record(base.get("repo")).get("id") == g.REPOSITORY_ID, "target")
    base_id, head_id = g.oid(base.get("sha")), g.oid(head.get("sha"))
    with tempfile.TemporaryDirectory(prefix="xevents-classification-") as temporary:
        objects = g.GitObjects(Path(temporary) / "objects")
        objects.prepare(base_id, head_id)
        old = {f.path: f for f in g.files(objects, g.commit(objects, base_id)[0])}
        new = {f.path: f for f in g.files(objects, g.commit(objects, head_id)[0])}
    changed = {path for path in old.keys() | new.keys() if old.get(path) != new.get(path)}
    again = api(f"repos/{g.REPOSITORY}/pulls/{number}")
    g.need(again.get("state") == "open"
           and g.record(again.get("head")).get("sha") == head_id
           and g.record(again.get("base")).get("sha") == base_id, "state_changed")
    if not boundary_paths(changed):
        return "code-only"
    g.need(changed <= p.ALLOWED, "mixed_boundary_change")
    admission(number)
    return "attestation-valid-at-check-time"


def deployment(merge_sha: str, number: int) -> p.Verdict:
    """Verify historical merge provenance, exact tree and a still-fresh proof."""
    merge_sha = g.oid(merge_sha)
    raw_policy = policy()
    pr = api(f"repos/{g.REPOSITORY}/pulls/{number}")
    g.need(pr.get("merged") is True and pr.get("state") == "closed"
           and pr.get("merge_commit_sha") == merge_sha, "merge_state")
    base, head = g.record(pr.get("base")), g.record(pr.get("head"))
    head_sha = g.oid(head.get("sha"))
    app_pr(pr, head_sha)
    merge_record = api(f"repos/{g.REPOSITORY}/commits/{merge_sha}")
    g.need(g.record(g.record(merge_record.get("commit")).get("verification")).get("verified")
           is True, "merge_signature")
    for side in (base, head):
        g.need(g.record(side.get("repo")).get("id") == g.REPOSITORY_ID, "target")
    g.need(base.get("ref") == "main", "target")
    body = pr.get("body")
    g.need(isinstance(body, str), "proof_body")
    body_bytes = cast(str, body).encode()
    payload, _ = p.payload_from_bytes(body_bytes)
    base_sha = cast(str, payload["base_sha"])
    with tempfile.TemporaryDirectory(prefix="xevents-deployment-") as temporary:
        objects = g.GitObjects(Path(temporary) / "objects")
        objects.prepare(base_sha, head_sha)
        objects.prepare(merge_sha, head_sha)
        merge_tree, parents = g.commit(objects, merge_sha)
        head_tree, head_parents = g.commit(objects, head_sha)
        g.need(parents == (base_sha, head_sha) and head_parents == (base_sha,)
               and merge_tree == head_tree, "merge_provenance")
        before = g.files(objects, g.commit(objects, base_sha)[0])
        after = g.files(objects, head_tree)
    old, new = {f.path: f for f in before}, {f.path: f for f in after}
    changes = tuple(p.Change(path, "modified" if path in old else "added")
                    for path in sorted(new) if old.get(path) != new[path])
    # The admission core authenticates the historical tuple after the real
    # merged/current-main state has been separately checked above and below.
    snapshot = p.Snapshot(g.REPOSITORY_ID, g.REPOSITORY, g.REPOSITORY_ID, number, "open",
                          "main", base_sha, base_sha, head_sha, head_parents,
                          before, after, changes, True)
    p.verify_offline(body_bytes, raw_policy, snapshot, int(time.time()))
    current = api(f"repos/{g.REPOSITORY}/git/ref/heads/main")
    g.need(g.record(current.get("object")).get("sha") == merge_sha, "deployment_main_changed")
    again = api(f"repos/{g.REPOSITORY}/pulls/{number}")
    g.need(again.get("body") == body and again.get("merged") is True
           and again.get("merge_commit_sha") == merge_sha
           and g.record(again.get("head")).get("sha") == head_sha, "deployment_pr_changed")
    g.need(policy() == raw_policy, "policy_changed")
    controls()
    return replace(p.verify_offline(body_bytes, raw_policy, snapshot, int(time.time())),
                   mode="deployment")


def merged_pr(merge_sha: str) -> int | None:
    """Only fresh App release merges deploy; ordinary code merges wait."""
    raw = g.command(["gh", "api", "--method", "GET",
                     f"repos/{g.REPOSITORY}/commits/{g.oid(merge_sha)}/pulls?per_page=100"],
                    1048576)
    rows = json.loads(raw, object_pairs_hook=g._pairs)
    g.need(isinstance(rows, list) and len(rows) < 100, "deployment_pr_lookup")
    matches = [g.record(row) for row in rows if g.record(row).get("merge_commit_sha") == merge_sha
               and g.record(g.record(row).get("user")).get("login") == APP_LOGIN]
    g.need(len(matches) <= 1, "deployment_pr_lookup")
    return g.number(matches[0].get("number")) if matches else None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=("admission", "check", "merge", "deployment",
                                        "preflight", "candidate"))
    parser.add_argument("--pr", type=int)
    parser.add_argument("--sha")
    parser.add_argument("--base")
    parser.add_argument("--body-sha")
    parser.add_argument("--directory", type=Path)
    args = parser.parse_args()
    try:
        if args.mode == "preflight":
            print(preflight().decode("utf-8"))
            return 0
        if args.mode == "check":
            result = check_run(g.number(args.pr))
        elif args.mode == "candidate":
            g.need(isinstance(args.directory, Path), "export_directory")
            exact_candidate(g.number(args.pr), args.directory)
            result = "exact-scanned-export"
        elif args.mode == "admission":
            result = classify(g.number(args.pr))
        elif args.mode == "merge":
            controls()
            verdict = admission(g.number(args.pr))
            g.need(verdict.head_sha == g.oid(args.sha), "merge_tuple")
            current = api(f"repos/{g.REPOSITORY}/pulls/{args.pr}")
            body = current.get("body")
            g.need(g.record(current.get("base")).get("sha") == g.oid(args.base), "merge_tuple")
            g.need(isinstance(body, str) and p.digest(body.encode()) == args.body_sha,
                   "merge_body")
            result = "merge-check-valid-at-check-time"
        else:
            number = args.pr or merged_pr(g.oid(args.sha))
            if number is None:
                result = "code-only-no-deployment"
            else:
                deployment(g.oid(args.sha), number)
                result = "deployment-check-valid-at-check-time"
                output = os.environ.get("GITHUB_OUTPUT")
                if output:
                    with Path(output).open("a") as handle:
                        handle.write(f"ready=true\npr={number}\n")
        print(json.dumps({"result": result}))
        return 0
    except Exception:
        print('{"result":"release-refused"}')
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
