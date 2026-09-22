"""Offline assertions for the staged WS7 baseline, not live enforcement tests."""

import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
CONFIG = json.loads((ROOT / "docs/branch-protection-bootstrap.json").read_text())
RULES = {rule["type"]: rule for rule in CONFIG["rules"]}


class BranchProtectionConfigTests(unittest.TestCase):
    def test_single_exact_active_main_target(self):
        self.assertEqual(CONFIG["name"], "xevents-main")
        self.assertEqual(CONFIG["target"], "branch")
        self.assertEqual(CONFIG["enforcement"], "active")
        self.assertEqual(CONFIG["conditions"],
                         {"ref_name": {"include": ["refs/heads/main"], "exclude": []}})

    def test_no_bypass_actor(self):
        self.assertEqual(CONFIG["bypass_actors"], [])

    def test_all_four_baseline_rules_present_once(self):
        self.assertEqual(set(RULES),
                         {"required_signatures", "pull_request", "deletion", "non_fast_forward"})
        self.assertEqual(len(CONFIG["rules"]), 4)

    def test_no_extra_top_level_fields(self):
        self.assertEqual(set(CONFIG),
                         {"name", "target", "enforcement", "bypass_actors", "conditions", "rules"})

    def test_required_pr_has_zero_approvals_and_no_extra_review_gate(self):
        parameters = RULES["pull_request"]["parameters"]
        self.assertEqual(parameters["required_approving_review_count"], 0)
        for key in ("dismiss_stale_reviews_on_push", "require_code_owner_review",
                    "require_last_push_approval", "required_review_thread_resolution"):
            self.assertIs(parameters[key], False)
        self.assertEqual(set(parameters), {
            "allowed_merge_methods", "required_approving_review_count",
            "dismiss_stale_reviews_on_push", "require_code_owner_review",
            "require_last_push_approval", "required_review_thread_resolution"})

    def test_existing_merge_methods_preserved(self):
        self.assertEqual(RULES["pull_request"]["parameters"]["allowed_merge_methods"],
                         ["merge", "squash", "rebase"])

    def test_signature_deletion_and_force_push_rules_have_no_exceptions(self):
        for name in ("required_signatures", "deletion", "non_fast_forward"):
            self.assertEqual(RULES[name], {"type": name})

    def test_unimplemented_checks_not_required_by_bootstrap(self):
        # Replace this assertion only after all five producer/check contracts
        # have passed their positive and negative tests in WS9/WS10.
        self.assertNotIn("required_status_checks", RULES)


if __name__ == "__main__":
    unittest.main()
