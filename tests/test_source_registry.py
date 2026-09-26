"""Source licence registry rules (ADR 0030). Offline; reads repository files only."""

import datetime
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "source-registry.json"
RESEARCH_APP = ROOT / "app" / "research.mjs"
AGGREGATE_APP = ROOT / "app" / "aggregate.mjs"
README = ROOT / "README.md"
EVIDENCE = ROOT / "research" / "licence-research-2026-09.md"

FIELDS = {
    "name", "kind", "independence_class", "status", "right", "licence", "licence_url",
    "reading", "explicit_grant", "noncommercial", "sharealike", "attribution_required",
    "credit", "republishes_other_sources", "reviewed_on",
}
RIGHTS = {"publish", "corroborate", "enrich", "excluded"}
STATUSES = {"active", "candidate", "excluded"}
KINDS = {"aggregator", "regulator", "court", "breach_catalog", "vuln_feed",
         "curated_dataset", "directory", "primary_crawler"}
# A named, citable licence or a written public-domain status (ADR 0030 item 5).
NAMED_GRANTS = ("CC0 1.0", "CC BY 4.0", "CC BY-SA 4.0", "The Unlicense", "MIT", "BSD",
                "US federal government work, public domain under 17 U.S.C. 105")
OBJECTION = "If you think we have read your terms wrong"


def load():
    def unique(pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise ValueError(f"duplicate key {key}")
            out[key] = value
        return out
    return json.loads(REGISTRY.read_text(encoding="utf-8"), object_pairs_hook=unique)


def sources():
    return load()["sources"]


def attribution_section():
    text = RESEARCH_APP.read_text(encoding="utf-8")
    match = re.search(r"<h2>Attribution</h2>(.*?)<h2>", text, re.S)
    if not match:
        raise AssertionError("research app has no Attribution section")
    return match.group(1)


class RegistryShape(unittest.TestCase):
    def test_header_names_policy_evidence_and_output_licence(self):
        registry = load()
        self.assertEqual(registry["schema_version"], "source-registry/v1")
        self.assertEqual(registry["output_licence"], "CC BY 4.0")
        self.assertTrue((ROOT / registry["policy"]).is_file())
        self.assertTrue((ROOT / registry["evidence"]).is_file())
        self.assertEqual(set(registry["rights"]), RIGHTS)

    def test_every_entry_is_complete_and_well_typed(self):
        names = [s["name"] for s in sources()]
        self.assertEqual(len(names), len(set(names)))
        for s in sources():
            with self.subTest(source=s.get("name")):
                self.assertEqual(set(s), FIELDS)
                self.assertRegex(s["name"], r"^[a-z0-9_]+$")
                self.assertIn(s["kind"], KINDS)
                self.assertIn(s["status"], STATUSES)
                self.assertIn(s["right"], RIGHTS)
                self.assertTrue(s["licence"].strip())
                self.assertTrue(s["reading"].strip())
                self.assertTrue(s["licence_url"].startswith("https://"))
                for flag in ("explicit_grant", "noncommercial", "sharealike",
                             "attribution_required", "republishes_other_sources"):
                    self.assertIsInstance(s[flag], bool)
                datetime.date.fromisoformat(s["reviewed_on"])

    def test_every_source_is_evidenced_in_the_licence_research(self):
        evidence = EVIDENCE.read_text(encoding="utf-8")
        for s in sources():
            with self.subTest(source=s["name"]):
                self.assertIn(f"`{s['name']}`", evidence)


class Rights(unittest.TestCase):
    def test_publish_requires_terms_compatible_with_the_cc_by_output(self):
        for s in sources():
            if s["right"] == "publish":
                with self.subTest(source=s["name"]):
                    self.assertFalse(s["noncommercial"])
                    self.assertFalse(s["sharealike"])
                    self.assertFalse(s["republishes_other_sources"])
                    self.assertTrue(s["credit"], "every published source is credited")
                    self.assertIsNotNone(s["independence_class"])

    def test_restricted_terms_never_publish(self):
        for s in sources():
            if s["noncommercial"] or s["sharealike"] or s["republishes_other_sources"]:
                with self.subTest(source=s["name"]):
                    self.assertNotEqual(s["right"], "publish")

    def test_a_permissive_licence_over_republished_rows_is_not_a_class(self):
        for s in sources():
            if s["republishes_other_sources"]:
                with self.subTest(source=s["name"]):
                    self.assertEqual(s["right"], "excluded")
                    self.assertIsNone(s["independence_class"])

    def test_enrichment_contributes_no_independence_class(self):
        for s in sources():
            if s["right"] == "enrich":
                with self.subTest(source=s["name"]):
                    self.assertIsNone(s["independence_class"])

    def test_explicit_grant_names_a_citable_licence(self):
        for s in sources():
            if s["explicit_grant"]:
                with self.subTest(source=s["name"]):
                    self.assertTrue(s["licence"].startswith(NAMED_GRANTS), s["licence"])

    def test_silence_and_prose_are_not_grants(self):
        for s in sources():
            if s["licence"].startswith(("No licence stated", "No named data licence",
                                        "Not stated", "Not retrieved")):
                with self.subTest(source=s["name"]):
                    self.assertFalse(s["explicit_grant"])

    def test_attribution_required_means_a_credit_when_used_publicly(self):
        for s in sources():
            if s["attribution_required"] and s["right"] == "publish":
                with self.subTest(source=s["name"]):
                    self.assertTrue(s["credit"])

    def test_status_and_right_agree(self):
        for s in sources():
            with self.subTest(source=s["name"]):
                self.assertEqual(s["status"] == "excluded", s["right"] == "excluded")

    def test_ransomware_live_stays_excluded(self):
        entry = {s["name"]: s for s in sources()}["ransomware_live"]
        self.assertEqual((entry["status"], entry["right"]), ("excluded", "excluded"))

    def test_only_approved_sources_are_active(self):
        # Activating a source needs its own ADR and approval (AGENTS.md scope rule).
        active = sorted(s["name"] for s in sources() if s["status"] == "active")
        self.assertEqual(active, ["ransomlook_api"])


class Attribution(unittest.TestCase):
    def active_publishers(self):
        return [s for s in sources() if s["status"] == "active" and s["right"] == "publish"]

    def test_export_attribution_is_the_registry_credit_line(self):
        credits = "; ".join(s["credit"] for s in self.active_publishers())
        text = AGGREGATE_APP.read_text(encoding="utf-8")
        found = re.findall(r'attribution: "([^"]*)"', text)
        self.assertEqual(found, [credits])

    def test_site_attribution_names_every_active_published_source(self):
        section = attribution_section()
        for s in self.active_publishers():
            with self.subTest(source=s["name"]):
                publisher, licence = s["credit"].split(";")[0].split(", ", 1)
                self.assertIn(publisher, section)
                self.assertIn(licence, section)

    def test_site_and_readme_carry_the_objection_path(self):
        for text in (attribution_section(), README.read_text(encoding="utf-8")):
            self.assertIn(OBJECTION, " ".join(text.split()))


if __name__ == "__main__":
    unittest.main()
