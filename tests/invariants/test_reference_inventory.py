"""Preparation cannot suppress diagnostics or authorize its own dispositions."""

import copy
from hashlib import sha256
from pathlib import Path
import unittest
from unittest.mock import patch

import checks
from reference_inventory import validate_inventory
from test_docs_qa import TREE


def sample():
    tree = {**TREE, "README.md": b"Planned `docs/missing.md`.\n"}
    issues = checks.docs_audit(tree)["issues"]
    proposal = {
        "schema_version": 1, "status": "proposal-only", "scope": "public",
        "baseline_sha": "a" * 40, "public_baseline_sha": None,
        "records": [{
            "id": "PR-01", "prior_id": "P01", "finding": issues[0],
            "source_sha256": sha256(tree["README.md"]).hexdigest(),
            "kind": "planned", "owner": "public", "milestone": "M2",
            "action": "Deliver real implementation with acceptance evidence.",
            "authority": "Synthetic milestone acceptance criterion.",
        }],
    }
    return tree, issues, proposal


class ReferenceInventoryTests(unittest.TestCase):
    def setUp(self):
        self.tree, self.issues, self.proposal = sample()

    def validate(self):
        return validate_inventory(self.proposal, self.tree, self.issues, "public")

    def test_review_validity_is_not_resolution(self):
        before = copy.deepcopy((self.proposal, self.tree, self.issues))
        report = self.validate()
        self.assertTrue(report["inventory_valid"])
        self.assertTrue(report["proposal_only"])
        self.assertEqual(report["resolved_findings"], 0)
        self.assertEqual(report["raw_findings"], 1)
        self.assertEqual((self.proposal, self.tree, self.issues), before)
        self.assertEqual(checks.docs_audit(self.tree)["issues"], self.issues)

    def test_missing_record_fails(self):
        self.proposal["records"].clear()
        with self.assertRaisesRegex(ValueError, "coverage"):
            self.validate()

    def test_duplicate_record_fails(self):
        self.proposal["records"] *= 2
        with self.assertRaises(ValueError):
            self.validate()

    def test_duplicate_finding_under_new_id_fails(self):
        row = copy.deepcopy(self.proposal["records"][0])
        row.update(id="PR-02", prior_id="P02")
        self.proposal["records"].append(row)
        with self.assertRaisesRegex(ValueError, "duplicate_finding"):
            self.validate()

    def test_new_unmapped_diagnostic_fails(self):
        self.issues.append({**self.issues[0], "detail": "docs/new-miss.md"})
        with self.assertRaisesRegex(ValueError, "coverage"):
            self.validate()

    def test_stale_source_fails_even_if_finding_text_is_unchanged(self):
        self.tree["README.md"] += b"\nUnrelated source change.\n"
        with self.assertRaisesRegex(ValueError, "source_changed"):
            self.validate()

    def test_missing_source_fails(self):
        del self.tree["README.md"]
        with self.assertRaisesRegex(ValueError, "source_missing"):
            self.validate()

    def test_extra_fields_and_claimed_approval_fail(self):
        for field, value in (("waiver", True), ("resolved", True),
                             ("private_evidence", "not-allowed")):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.proposal)
                altered["records"][0][field] = value
                with self.assertRaises(ValueError):
                    validate_inventory(altered, self.tree, self.issues, "public")
        self.proposal["status"] = "approved"
        with self.assertRaisesRegex(ValueError, "not_proposal"):
            self.validate()

    def test_scope_cannot_be_relabelled_at_call_site(self):
        with self.assertRaisesRegex(ValueError, "scope"):
            validate_inventory(self.proposal, self.tree, self.issues, "private")

    def test_public_inventory_rejects_private_baseline_field(self):
        self.proposal["public_baseline_sha"] = "b" * 40
        with self.assertRaises(ValueError):
            self.validate()

    def test_unknown_kinds_owners_and_milestones_fail(self):
        for field, value in (("kind", "ignore"), ("owner", "any"),
                             ("milestone", None), ("milestone", "M99")):
            with self.subTest(field=field):
                altered = copy.deepcopy(self.proposal)
                altered["records"][0][field] = value
                with self.assertRaises(ValueError):
                    validate_inventory(altered, self.tree, self.issues, "public")

    def test_private_kind_requires_private_owner(self):
        self.proposal["records"][0].update(kind="private_owned", milestone=None)
        with self.assertRaisesRegex(ValueError, "owner_kind"):
            self.validate()

    def test_history_cannot_excuse_reference_failure(self):
        self.proposal["records"][0].update(kind="preserved_history", milestone=None)
        with self.assertRaisesRegex(ValueError, "kind_code"):
            self.validate()

    def test_unsafe_source_path_fails(self):
        for path in ("../README.md", "/README.md", "docs\\file.md", "docs//a.md"):
            with self.subTest(path=path):
                altered = copy.deepcopy(self.proposal)
                altered["records"][0]["finding"]["path"] = path
                with self.assertRaises(ValueError):
                    validate_inventory(altered, self.tree, self.issues, "public")

    def test_malformed_digests_lines_and_versions_fail(self):
        for field, value in (("baseline_sha", "main"), ("schema_version", True)):
            altered = {**self.proposal, field: value}
            with self.assertRaises(ValueError):
                validate_inventory(altered, self.tree, self.issues, "public")
        for line in (True, 0, -1, 999):
            altered = copy.deepcopy(self.proposal)
            altered["records"][0]["finding"]["line"] = line
            with self.assertRaises(ValueError):
                validate_inventory(altered, self.tree, self.issues, "public")
        self.proposal["records"][0]["source_sha256"] = "not-a-hash"
        with self.assertRaises(ValueError):
            self.validate()

    def test_no_network_or_subprocess_and_deterministic_report(self):
        with patch.object(checks, "api", side_effect=AssertionError("network")), \
             patch.object(checks.subprocess, "run", side_effect=AssertionError("process")):
            self.assertEqual(self.validate(), self.validate())

    def test_duplicate_raw_diagnostics_are_rejected(self):
        self.issues *= 2
        with self.assertRaisesRegex(ValueError, "duplicate_diagnostic"):
            self.validate()

    def test_real_public_inventory_covers_current_tree_without_suppression(self):
        root = Path(__file__).resolve().parents[2]
        # Complete public file inventory, not only Markdown target candidates.
        names = checks.git(root, "ls-files", "--cached", "--others",
                           "--exclude-standard", "-z").decode().split("\0")
        tree = {}
        for name in filter(None, names):
            path = root / checks.safe_path(name)
            checks.require(not any(p.is_symlink() for p in (path, *path.parents)),
                           "symlink_in_checkout")
            if path.is_file():
                tree[name] = path.read_bytes()
        inventory = checks.decode(tree["docs/reference-findings.json"])
        issues = checks.docs_audit(tree)["issues"]
        report = validate_inventory(inventory, tree, issues, "public")
        self.assertEqual(report["raw_findings"], 23)
        self.assertEqual(report["resolved_findings"], 0)
        self.assertEqual(report["counts_by_kind"], {
            "bounded_template": 2, "example": 1, "external_public": 1,
            "historical_target": 1, "planned": 3, "preserved_history": 3,
            "private_owned": 12})
