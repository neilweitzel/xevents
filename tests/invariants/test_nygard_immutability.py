import unittest
from checks import nygard

PATH = "docs/adr/0001-example.md"
OLD = b"# ADR 0001: Example\n\n- Status: accepted\n- Date: 2026-09-22\n\n## Context\n\nKeep this historical body.\n"


class NygardTests(unittest.TestCase):
    def test_unchanged_metadata_and_html_comments_allowed(self):
        for new in (OLD, OLD.replace(b"2026-09-22", b"2026-09-23"),
                    OLD + b"\n<!-- editorial note -->\n"):
            self.assertEqual(nygard({PATH: OLD}, {PATH: new}), [])

    def test_new_adr_allowed(self):
        self.assertEqual(nygard({}, {PATH: OLD}), [])
        proposed = OLD.replace(b"accepted", b"proposed")
        self.assertEqual(nygard({PATH: proposed}, {PATH: proposed.replace(b"Keep", b"Edit")}), [])

    def test_base_status_protects_against_body_edits_deletion_and_downgrade(self):
        for tree in ({}, {PATH: OLD.replace(b"Keep", b"Rewrite")},
                     {PATH: OLD.replace(b"accepted", b"proposed")},
                     {PATH: OLD.replace(b"- Status: accepted\n", b"")},
                     {PATH: OLD + b"\n```comment\nNew policy\n```\n"}):
            with self.subTest(tree=tree):
                self.assertTrue(nygard({PATH: OLD}, tree))

    def test_supersession_requires_real_accepted_target_and_preserves_history(self):
        new = OLD.replace(b"Status: accepted", b"Status: superseded by ADR 0002")
        target = "docs/adr/0002-next.md"
        self.assertEqual(nygard({PATH: OLD}, {PATH: new, target: OLD}), [])
        for tree in ({PATH: new}, {PATH: new, target: OLD.replace(b"accepted", b"proposed")},
                     {PATH: new.replace(b"Keep", b"Rewrite"), target: OLD}):
            self.assertTrue(nygard({PATH: OLD}, tree))

    def test_superseded_and_partially_superseded_history_remains_protected(self):
        for status in (b"superseded-in-part", b"superseded by ADR 0002"):
            old = OLD.replace(b"accepted", status)
            self.assertTrue(nygard({PATH: old}, {PATH: old.replace(b"Keep", b"Rewrite")}))
