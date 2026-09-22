import unittest
from checks import docs_audit
from test_nygard_immutability import OLD

TREE = {
    "docs/adr/0001-example.md": OLD,
    "docs/glossary.md": b"# Glossary\n\n- **observation**: A source claim.\n",
    "docs/open-decisions.md": b"## 1. Scope\n\n- **DECIDED:** in scope.\n\n## 2. Pending\n\nUnresolved.\n",
}


class DocsTests(unittest.TestCase):
    def test_existing_links_references_and_real_glossary_loaded(self):
        tree = {**TREE, "docs/example.md": b"[ADR](adr/0001-example.md) and ADR 0001.\nAn observation.\n"}
        result = docs_audit(tree)
        self.assertEqual(result["issues"], [])
        self.assertEqual(result["glossary_terms"], 1)
        self.assertGreater(result["glossary_usage"]["observation"], 0)

    def test_missing_local_paths_and_adrs_reported(self):
        tree = {**TREE, "README.md": b"ADR 9999 and `docs/missing.md` and [missing](no.md).\n"}
        self.assertEqual({r["code"] for r in docs_audit(tree)["issues"]},
                         {"unresolved_adr", "unresolved_reference"})

    def test_decision_drift_is_flagged_only_with_decided_reference(self):
        for phrase in ("UNDECIDED per ADR 0001.", "TBD per open-decisions.md #1.",
                       "Proposed per decision #1.", "to be decided under ADR 0001."):
            result = docs_audit({**TREE, "README.md": phrase.encode()})
            self.assertIn("possible_decision_language_drift", [r["code"] for r in result["issues"]])
        for phrase in ("TBD per decision #2.", "Status: proposed\n\nAuthority: ADR 0001.",
                       "Example token `TBD` under ADR 0001.",
                       "```text\nUNDECIDED ADR 9999\n```\n"):
            self.assertEqual(docs_audit({**TREE, "README.md": phrase.encode()})["issues"], [])

    def test_relative_links_external_urls_and_reference_checkout(self):
        tree = {"docs/private.md": b"[up](../README.md) and [web](https://example.com) and [same](./private.md).\n",
                "README.md": b"Local.\n"}
        self.assertEqual(docs_audit(tree, TREE)["issues"], [])

    def test_missing_or_ambiguous_glossary_fails_instead_of_deferral(self):
        for tree in ({}, {**TREE, "docs/glossary.md": b"# Empty"},
                     {**TREE, "docs/glossary.md": b"- **term**: one\n- **Term**: two\n"}):
            with self.assertRaises(ValueError):
                docs_audit(tree)

    def test_metadata_globs_and_undecided_are_not_false_positives(self):
        tree = {**TREE,
                "docs/open-decisions.md": b"## 1. Pending\n\nUNDECIDED\n",
                "README.md": b"Status: proposed\nAuthority: ADR 0001.\n\n"
                             b"`docs/*.md` and `docs/adr/*` and [query](?q=1).\n\n"
                             b"TBD per decision #1.\n"}
        self.assertEqual(docs_audit(tree)["issues"], [])
        tree["README.md"] += b"\n## Rules\n\nStatus: proposed per ADR 0001.\n"
        self.assertEqual(docs_audit(tree)["issues"][0]["line"], 10)

    def test_code_and_comments_preserve_diagnostic_line_numbers(self):
        tree = {**TREE, "README.md": b"```text\nx\n```\n\n<!-- hidden\nx -->\n\nTBD per ADR 0001.\n"}
        self.assertEqual(docs_audit(tree)["issues"][0]["line"], 8)
