import unittest
from checks import g5_gate
from test_boundary_write_set import ADR
from test_pr_diff_write_set import rows


class G5GateTests(unittest.TestCase):
    def test_documentation_pr_scoped_noop(self):
        self.assertTrue(g5_gate(rows("docs/new.md"), "operator/docs", ADR))

    def test_every_boundary_data_pr_blocked_without_public_contract(self):
        for branch in ("boundary/test", "operator/data", "renamed", "main"):
            with self.subTest(branch=branch), self.assertRaisesRegex(
                    ValueError, "public-proof-contract-not-implemented"):
                g5_gate(rows("data/aggregates/a.jsonl"), branch, ADR)

    def test_boundary_named_docs_pr_and_boundary_deletion_are_blocked(self):
        for files, branch in ((rows("README.md"), "boundary/docs"),
                              ([{"filename": "evidence-manifest.jsonl", "status": "removed"}], "operator")):
            with self.assertRaisesRegex(ValueError, "public-proof-contract-not-implemented"):
                g5_gate(files, branch, ADR)

    def test_arbitrary_report_claims_are_not_an_input_or_escape_hatch(self):
        import inspect
        self.assertEqual(list(inspect.signature(g5_gate).parameters), ["files", "branch", "adr"])
        for _claim in (None, "{malformed", '{"outcome":"pass"}', "https://example.com/report"):
            with self.assertRaises(ValueError):
                g5_gate(rows("evidence-manifest.jsonl"), "operator", ADR)
