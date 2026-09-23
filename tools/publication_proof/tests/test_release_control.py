"""Trusted-main routing, native controls, exact exports and deployment provenance."""
import base64
import copy
from unittest.mock import patch

import pytest
from test_github_snapshot import Fixture
from test_proof import NOW, VECTOR, wire

import github_snapshot as g
import package_site as site
import proof as p
import release_control as c


def rules():
    return {"enforcement": "active", "bypass_actors": [],
            "conditions": {"ref_name": {"include": ["refs/heads/main"], "exclude": []}},
            "rules": [{"type": name} for name in
                      ("required_signatures", "pull_request", "deletion", "non_fast_forward")]
            + [{"type": "required_status_checks", "parameters": {
                "strict_required_status_checks_policy": True,
                "required_status_checks": [{"context": c.CHECK_NAME, "integration_id": 15368}]}}]}


def setup(monkeypatch, merged=False):
    f = Fixture()
    policy = f.signed()
    f.pr["user"] = {"login": c.APP_LOGIN, "type": "Bot"}
    f.pr["head"]["ref"] = "xevents-release-123-abcdef123456"
    commit = {"author": {"login": c.APP_LOGIN},
              "commit": {"verification": {"verified": True}}}
    lookup = {}
    if merged:
        tree, _ = g.commit(f.objects, f.head)
        merge = f.objects.commit(tree, (f.base, f.head))
        f.pr.update(state="closed", merged=True, merge_commit_sha=merge)
        f.ref["object"]["sha"] = merge
        lookup[f"repos/{g.REPOSITORY}/commits/{merge}"] = commit
    lookup[f"repos/{g.REPOSITORY}/commits/{f.head}"] = commit
    lookup[f"repos/{g.REPOSITORY}/rulesets/23845612"] = rules()
    original = f.api
    def api(path):
        return copy.deepcopy(lookup[path]) if path in lookup else original(path)
    monkeypatch.setattr(c, "api", api)
    monkeypatch.setattr(c, "policy", lambda: policy)
    monkeypatch.setattr(c.time, "time", lambda: NOW)
    monkeypatch.setattr(g, "GitObjects", lambda _: f.objects)
    return f, lookup


def test_admission_and_exact_scanned_bytes(monkeypatch, tmp_path):
    f, _ = setup(monkeypatch)
    assert c.classify(7) == "attestation-valid-at-check-time"
    for blob in f.read().snapshot.head_files:
        if blob.path in p.ALLOWED:
            path = tmp_path / blob.path
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(blob.data)
    c.exact_candidate(7, tmp_path)
    (tmp_path / "evidence-manifest.jsonl").write_bytes(b"changed")
    with pytest.raises(g.SnapshotRefused, match="export_bytes"):
        c.exact_candidate(7, tmp_path)


def test_code_only_change_needs_no_publication_proof(monkeypatch):
    f, _ = setup(monkeypatch)
    blob = f.objects.add("blob", b"Changed documentation only\n")
    f.head = f.objects.commit(f.objects.tree([("100644", "README.md", blob)]), (f.base,))
    f.pr["head"]["sha"] = f.head
    f.pr["body"] = "No proof: this is a documentation change."
    with patch.object(c, "admission") as admission:
        assert c.classify(7) == "code-only"
        admission.assert_not_called()


def test_mixed_code_and_data_change_refused(monkeypatch):
    f, _ = setup(monkeypatch)
    blob = f.objects.add("blob", b"Unreviewed code change\n")
    entries = [row for row in f.entries if row[1] != "README.md"]
    entries.append(("100644", "README.md", blob))
    f.head = f.objects.commit(f.objects.tree(entries), (f.base,))
    f.pr["head"]["sha"] = f.head
    with pytest.raises(g.SnapshotRefused, match="mixed_boundary_change"):
        c.classify(7)


@pytest.mark.parametrize("change", ["human", "branch", "unsigned", "wrong-author"])
def test_non_app_identity_refused(monkeypatch, change):
    f, lookup = setup(monkeypatch)
    record = lookup[f"repos/{g.REPOSITORY}/commits/{f.head}"]
    if change == "human":
        f.pr["user"]["login"] = "human"
    elif change == "branch":
        f.pr["head"]["ref"] = "anything"
    elif change == "unsigned":
        record["commit"]["verification"]["verified"] = False
    else:
        record["author"]["login"] = "human"
    with pytest.raises(g.SnapshotRefused):
        c.admission(7)


@pytest.mark.parametrize("change", ["disabled", "bypass", "branch", "exclude", "signature",
                                   "pull_request", "deletion", "non_fast_forward", "checks",
                                   "loose", "spoof", "wrong-context"])
def test_native_protection_changes_refused(monkeypatch, change):
    value = rules()
    if change == "disabled":
        value["enforcement"] = "disabled"
    elif change == "bypass":
        value["bypass_actors"] = [{"actor_id": 1}]
    elif change in ("branch", "exclude"):
        value["conditions"]["ref_name"]["include" if change == "branch" else "exclude"] = ["*"]
    elif change in ("signature", "pull_request", "deletion", "non_fast_forward", "checks"):
        name = {"signature": "required_signatures", "checks": "required_status_checks"}.get(change, change)
        value["rules"] = [r for r in value["rules"] if r["type"] != name]
    else:
        parameters = value["rules"][-1]["parameters"]
        if change == "loose":
            parameters["strict_required_status_checks_policy"] = False
        elif change == "spoof":
            parameters["required_status_checks"][0]["integration_id"] = 1
        else:
            parameters["required_status_checks"][0]["context"] = "Some check"
    monkeypatch.setattr(c, "api", lambda _: value)
    with pytest.raises(g.SnapshotRefused):
        c.controls()


def test_exact_two_parent_current_merge_deploys(monkeypatch):
    f, _ = setup(monkeypatch, merged=True)
    verdict = c.deployment(f.pr["merge_commit_sha"], 7)
    assert verdict.mode == "deployment"
    assert verdict.publication_authorized is False


@pytest.mark.parametrize("change", ["not-merged", "open", "wrong-merge", "wrong-main",
                                   "expired", "unsigned", "policy-race", "body-race"])
def test_deployment_refusals(monkeypatch, change):
    f, lookup = setup(monkeypatch, merged=True)
    merge = f.pr["merge_commit_sha"]
    if change == "not-merged":
        f.pr["merged"] = False
    elif change == "open":
        f.pr["state"] = "open"
    elif change == "wrong-merge":
        f.pr["merge_commit_sha"] = "f" * 40
    elif change == "wrong-main":
        f.ref["object"]["sha"] = f.head
    elif change == "expired":
        monkeypatch.setattr(c.time, "time", lambda: NOW + 1000)
    elif change == "unsigned":
        lookup[f"repos/{g.REPOSITORY}/commits/{merge}"]["commit"]["verification"]["verified"] = False
    elif change == "policy-race":
        original = c.policy()
        monkeypatch.setattr(c, "policy", iter((original, original + b" ")).__next__)
    else:
        original_api = c.api
        calls = 0
        def api(path):
            nonlocal calls
            row = original_api(path)
            if path.endswith("/pulls/7"):
                calls += 1
                if calls > 1:
                    row["body"] += " "
            return row
        monkeypatch.setattr(c, "api", api)
    with pytest.raises((g.SnapshotRefused, p.Refused)):
        c.deployment(merge, 7)


@pytest.mark.parametrize("parents", [(), ("base",), ("head", "base")])
def test_squash_rebase_or_wrong_parent_order_refused(monkeypatch, parents):
    f, lookup = setup(monkeypatch, merged=True)
    tree, _ = g.commit(f.objects, f.head)
    merge = f.objects.commit(tree, tuple(getattr(f, name) for name in parents))
    lookup[f"repos/{g.REPOSITORY}/commits/{merge}"] = lookup[f"repos/{g.REPOSITORY}/commits/{f.head}"]
    f.pr["merge_commit_sha"] = merge
    f.ref["object"]["sha"] = merge
    with pytest.raises(g.SnapshotRefused, match="merge_provenance"):
        c.deployment(merge, 7)


def test_check_is_explicitly_bound_to_candidate_head(monkeypatch):
    f, _ = setup(monkeypatch)
    with patch.object(g, "command") as transport:
        assert c.check_run(7, f.head) == "attestation-valid-at-check-time"
    transport.assert_not_called()


def test_failed_check_is_not_left_successful(monkeypatch):
    f, _ = setup(monkeypatch)
    f.pr["body"] = "{}"
    with patch.object(g, "command") as transport:
        with pytest.raises(p.Refused):
            c.check_run(7, f.head)
    transport.assert_not_called()


def test_native_job_refuses_a_different_event_head(monkeypatch):
    setup(monkeypatch)
    with patch.object(c, "classify") as classify:
        with pytest.raises(g.SnapshotRefused, match="event_head_changed"):
            c.check_run(7, "f" * 40)
    classify.assert_not_called()


def test_native_job_refuses_head_changed_during_verification(monkeypatch):
    f, _ = setup(monkeypatch)
    head = f.head
    def changed_head(number):
        f.pr["head"]["sha"] = "f" * 40
        return "attestation-valid-at-check-time"
    monkeypatch.setattr(c, "classify", changed_head)
    with pytest.raises(g.SnapshotRefused, match="event_head_changed"):
        c.check_run(7, head)


@pytest.mark.parametrize("head", [None, "", "wrong", "f" * 39])
def test_native_job_requires_a_well_formed_event_head(monkeypatch, head):
    setup(monkeypatch)
    with pytest.raises(g.SnapshotRefused):
        c.check_run(7, head)


def test_production_policy_rejects_known_test_key(monkeypatch):
    value = copy.deepcopy(VECTOR["policy"])
    value.update(repository_id=g.REPOSITORY_ID, repository_name=g.REPOSITORY)
    monkeypatch.setattr(c, "api", lambda _: {"type": "file", "encoding": "base64",
        "content": base64.b64encode(wire(value)).decode() + "\n"})
    with pytest.raises(g.SnapshotRefused, match="unsafe_production_key"):
        c.policy()


def test_packaging_allowlist_excludes_repository_and_tooling(tmp_path):
    root, out = tmp_path / "root", tmp_path / "out"
    for name in site.ASSETS:
        path = root / "app" / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"fixture")
    for name in site.DATA:
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b"public")
    (root / "app" / "secret.txt").write_bytes(b"do not include")
    site.package(root, out)
    assert set(str(p.relative_to(out)) for p in out.rglob("*") if p.is_file()) == (
        set(site.ASSETS) | set(site.DATA) | {".nojekyll"})
    with pytest.raises(ValueError, match="output_exists"):
        site.package(root, out)
