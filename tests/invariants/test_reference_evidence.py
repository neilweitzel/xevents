"""Adversarial tests for offline bindings, not operational acceptance."""

import copy
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import checks
import reference_evidence as evidence
from test_reference_inventory import sample


def file_binding(path, data, heading=None):
    return {"type": "file", "path": path, "sha256": evidence.hashed(data),
            "section": None if heading is None else {
                "heading": heading,
                "sha256": evidence.hashed(evidence.section_bytes(data, heading))}}


def sample_policy():
    tree, _, inventory = sample()
    rule = {"kind": "planned", "target": "docs/missing.md",
            "deliverable": "synthetic-document", "milestone": "M2", "criteria": ["AC2.1"]}
    tree[evidence.INVENTORY] = json.dumps(inventory).encode()
    policy = {"schema_version": 1, "mode": "shadow-only", "scope": "public",
              "inventory_sha256": evidence.hashed(tree[evidence.INVENTORY]),
              "rules": {"PR-01": rule}}
    tree[evidence.POLICY] = json.dumps(policy).encode()
    return tree, inventory["records"][0], rule


def working_tree():
    root = Path(__file__).resolve().parents[2]
    names = checks.git(root, "ls-files", "--cached", "--others",
                       "--exclude-standard", "-z").decode().split("\0")
    tree = {}
    for name in filter(None, names):
        path = root / checks.safe_path(name)
        checks.require(not any(p.is_symlink() for p in (path, *path.parents)),
                       "symlink_in_checkout")
        if path.is_file():
            tree[name] = path.read_bytes()
    return tree


class EvidenceBindingTests(unittest.TestCase):
    def setUp(self):
        self.path = "docs/target.md"
        self.data = b"# Target\n\n## Evidence\nDECIDED: real text.\n\n## Other\nOther.\n"
        self.tree = {self.path: self.data}
        self.file = file_binding(self.path, self.data, "## Evidence")

    def test_exact_file_and_section_bind(self):
        self.assertEqual(evidence.binding(self.tree, self.file), self.data)

    def test_missing_empty_and_changed_files_fail(self):
        for tree in ({}, {self.path: b""}, {self.path: self.data + b"changed"}):
            with self.subTest(tree=tree), self.assertRaises(ValueError):
                evidence.binding(tree, self.file)

    def test_unsafe_file_paths_fail(self):
        for path in ("../target", "/target", "docs//target", "docs\\target", "docs/./target"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                evidence.binding({path: self.data}, {**self.file, "path": path})

    def test_missing_duplicate_and_wrong_section_hash_fail(self):
        for data in (b"# No section\n", self.data + b"\n## Evidence\nDuplicate\n"):
            with self.subTest(data=data), self.assertRaises(ValueError):
                evidence.section_bytes(data, "## Evidence")
        item = copy.deepcopy(self.file)
        item["section"]["sha256"] = "0" * 64
        with self.assertRaises(ValueError):
            evidence.binding(self.tree, item)

    def test_section_stops_at_peer_but_includes_child(self):
        data = b"# A\n## B\ntext\n### C\nchild\n## D\nother\n"
        self.assertEqual(evidence.section_bytes(data, "## B"),
                         b"## B\ntext\n### C\nchild\n")

    def test_directory_requires_exact_nonempty_members(self):
        item = {"type": "directory", "path": "data",
                "members": {"data/a.json": evidence.hashed(b"{}")}}
        evidence.binding({"data/a.json": b"{}"}, item)
        for tree in ({}, {"data/a.json": b""},
                     {"data/a.json": b"{}", "data/b.json": b"{}"},
                     {"data": b"file", "data/a.json": b"{}"}):
            with self.subTest(tree=tree), self.assertRaises(ValueError):
                evidence.binding(tree, item)

    def test_directory_prefix_collision_is_not_membership(self):
        item = {"type": "directory", "path": "data",
                "members": {"database/a": evidence.hashed(b"x")}}
        with self.assertRaises(ValueError):
            evidence.binding({"database/a": b"x"}, item)

    def test_unknown_binding_fields_fail(self):
        with self.assertRaises(ValueError):
            evidence.binding(self.tree, {**self.file, "waiver": True})

    def test_named_test_is_parsed_never_executed(self):
        data = b"raise RuntimeError('must not execute')\nclass T:\n def test_real(self): pass\n"
        test = {"file": file_binding("tests/test_x.py", data), "class": "T", "method": "test_real"}
        evidence.test_binding({"tests/test_x.py": data}, test)

    def test_missing_duplicate_or_non_test_methods_fail(self):
        for data, method in (
            (b"class T:\n def other(self): pass\n", "test_real"),
            (b"class T:\n def other(self): pass\n", "other"),
            (b"class T:\n def test_real(self): pass\n def test_real(self): pass\n", "test_real"),
            (b"class T: pass\nclass T:\n def test_real(self): pass\n", "test_real"),
        ):
            item = {"file": file_binding("tests/test_x.py", data), "class": "T", "method": method}
            with self.subTest(data=data), self.assertRaises(ValueError):
                evidence.test_binding({"tests/test_x.py": data}, item)


class EvidencePolicyTests(unittest.TestCase):
    def setUp(self):
        self.tree, self.row, self.rule = sample_policy()

    def test_shadow_cannot_suppress_raw_diagnostics_or_mutate_input(self):
        before = copy.deepcopy(self.tree)
        report = evidence.audit_public(self.tree, self.tree)
        self.assertEqual(report["raw_findings"], 1)
        self.assertEqual(report["resolved_findings"], 0)
        self.assertTrue(report["strict_failure_preserved"])
        self.assertEqual(report["counts"], {"planned-target-absent-state-unknown": 1})
        self.assertEqual(self.tree, before)

    def test_candidate_cannot_rewrite_policy_or_inventory(self):
        for path in (evidence.POLICY, evidence.INVENTORY):
            candidate = {**self.tree, path: self.tree[path] + b"\n"}
            with self.subTest(path=path), self.assertRaisesRegex(ValueError, "candidate_policy"):
                evidence.audit_public(candidate, self.tree)

    def test_missing_extra_and_unbound_rules_fail(self):
        for mutate in (
            lambda p: p["rules"].clear(),
            lambda p: p["rules"].update({"PR-99": self.rule}),
            lambda p: p.update(inventory_sha256="0" * 64),
            lambda p: p.update(mode="approved"),
            lambda p: p.update(schema_version=True),
            lambda p: p.update(waiver=True),
        ):
            policy = checks.decode(self.tree[evidence.POLICY])
            mutate(policy)
            tree = {**self.tree, evidence.POLICY: json.dumps(policy).encode()}
            with self.subTest(policy=policy), self.assertRaises(ValueError):
                evidence.audit_public(tree, tree)

    def test_malformed_and_duplicate_key_policy_fail(self):
        for data in (b'{"mode":"shadow-only","mode":"approved"}', b'{"x":NaN}', b'bad'):
            tree = {**self.tree, evidence.POLICY: data}
            with self.subTest(data=data), self.assertRaises(ValueError):
                evidence.audit_public(tree, tree)

    def test_changed_source_and_new_unmapped_reference_fail(self):
        candidate = {**self.tree, "README.md": self.tree["README.md"] + b"\nchanged\n"}
        with self.assertRaises(ValueError):
            evidence.audit_public(candidate, self.tree)
        candidate = {**self.tree, "docs/new.md": b"`docs/another-missing.md`\n"}
        with self.assertRaises(ValueError):
            evidence.audit_public(candidate, self.tree)

    def test_planned_target_presence_is_not_completion(self):
        trees = {"public": {self.rule["target"]: b"placeholder"}}
        self.assertEqual(evidence.evaluate(self.row, self.rule, trees),
                         "planned-target-present-state-unknown")

    def test_planned_target_in_wrong_owner_is_not_present(self):
        trees = {"public": {}, "private": {self.rule["target"]: b"decoy"}}
        self.assertEqual(evidence.evaluate(self.row, self.rule, trees),
                         "planned-target-absent-state-unknown")

    def test_milestone_mismatch_and_completion_claims_fail(self):
        for rule in ({**self.rule, "milestone": "M4"},
                     {**self.rule, "criteria": ["AC4.1"]},
                     {**self.rule, "criteria": ["AC2.1", "AC2.1"]},
                     {**self.rule, "complete": True},
                     {**self.rule, "waiver": True}):
            with self.subTest(rule=rule), self.assertRaises(ValueError):
                evidence.evaluate(self.row, rule, {"public": {}})

    def test_public_private_owner_requires_deferral_not_evidence(self):
        row = {**self.row, "owner": "private"}
        self.assertEqual(evidence.evaluate(row, {"kind": "owner-deferred"}, {"public": {}}),
                         "private-not-checked")
        with self.assertRaises(ValueError):
            evidence.evaluate(row, self.rule, {"public": {}})

    def test_external_reference_never_attests_remote_existence(self):
        row = {**self.row, "kind": "external_public", "owner": "external-public"}
        rule = {"kind": "external", "repository": "example/project",
                "path": self.row["finding"]["detail"]}
        self.assertEqual(evidence.evaluate(row, rule, {}), "external-not-checked")
        with self.assertRaises(ValueError):
            evidence.evaluate(row, {**rule, "verified": True}, {})

    def test_failure_output_is_sanitized(self):
        inventory = {"records": [self.row]}
        rows = evidence.results(inventory, {"PR-01": {"secret": "DO-NOT-ECHO"}}, {"public": {}})
        self.assertEqual(rows, [{"id": "PR-01", "status": "evidence-invalid-or-stale"}])
        self.assertNotIn("DO-NOT-ECHO", json.dumps(rows))

    def test_deterministic_offline_no_process_execution(self):
        with patch.object(checks, "api", side_effect=AssertionError("network")), \
             patch.object(checks.subprocess, "run", side_effect=AssertionError("subprocess")):
            self.assertEqual(evidence.audit_public(self.tree, self.tree),
                             evidence.audit_public(self.tree, self.tree))

    def test_history_requires_exact_number_section_and_ruling(self):
        row = {**self.row, "kind": "preserved_history",
               "finding": {**self.row["finding"], "detail": "2"}}
        path, heading = "docs/open-decisions.md", "## 2. Ruling"
        data = b"## 2. Ruling\n- **DECIDED 2026-09-20 by the user:** exact ruling\n"
        rule = {"kind": "history", "decision": "2", "authority": file_binding(path, data, heading)}
        self.assertEqual(evidence.evaluate(row, rule, {"public": {path: data}}),
                         "historical-ruling-bound")
        for data in (b"## 2. Ruling\nStill proposed\n", b"## 2. Ruling\nUNDECIDED\n"):
            # A substring in UNDECIDED must not count as a positive decision.
            rule["authority"] = file_binding(path, data, heading)
            with self.subTest(data=data), self.assertRaises(ValueError):
                evidence.evaluate(row, rule, {"public": {path: data}})

    def test_real_public_shadow_preserves_all_twenty_three_findings(self):
        tree = working_tree()
        report = evidence.audit_public(tree, tree)
        self.assertEqual(report["raw_findings"], 23)
        self.assertEqual(report["resolved_findings"], 0)
        self.assertEqual(report["counts"], {
            "private-not-checked": 17, "historical-ruling-bound": 3,
            "example-test-bound-not-executed": 1, "external-not-checked": 1,
            "planned-target-absent-state-unknown": 1})
        self.assertNotIn("IR-", json.dumps(report))


if __name__ == "__main__":
    unittest.main()
