"""Positive and adversarial examples for the bounded Markdown diagnostics."""

import unittest

from checks import docs_audit, nygard, semantic_units
from test_docs_qa import TREE
from test_nygard_immutability import OLD, PATH


class MarkdownContextTests(unittest.TestCase):
    def audit(self, prose):
        return docs_audit({**TREE, "README.md": prose.encode()})["issues"]

    def assert_drift(self, prose, line=None):
        issues = [r for r in self.audit(prose)
                  if r["code"] == "possible_decision_language_drift"]
        self.assertTrue(issues, prose)
        if line is not None:
            self.assertEqual(issues[0]["line"], line)

    def test_bold_and_plain_preamble_status_formats(self):
        for status in ("Status: proposed", "- Status: proposed",
                       "**Status:** proposed", "**Status**: proposed",
                       "Status: **proposed**"):
            with self.subTest(status=status):
                self.assertEqual(self.audit(
                    f"# Vocabulary\n\n{status}, 2026-09-22.\nSee ADR 0001.\n"), [])

    def test_preamble_removal_does_not_hide_a_second_claim_on_same_line(self):
        self.assert_drift("**Status:** proposed. TBD per ADR 0001.", 1)

    def test_body_status_is_not_metadata(self):
        self.assert_drift(
            "# Title\n\n**Status:** proposed\n\n## Rules\n\n"
            "**Status:** proposed per ADR 0001.\n", 7)

    def test_unknown_status_value_is_not_silently_removed(self):
        self.assert_drift("Status: TBD per ADR 0001.", 1)

    def test_list_items_do_not_borrow_other_items_authority(self):
        self.assertEqual(self.audit(
            '- Checker flags "proposed"/"undecided" language.\n'
            "- Cadence follows decision #1.\n"), [])

    def test_numbered_and_nested_items_are_separate(self):
        self.assertEqual(self.audit(
            "1. Future detail remains TBD.\n"
            "2. Accepted scope follows ADR 0001.\n"
            "   - Another pending detail is proposed.\n"
            "   - Scope follows decision #1.\n"), [])

    def test_wrapped_authority_stays_in_its_list_item(self):
        self.assert_drift(
            "- Settled first item.\n- Cadence remains UNDECIDED\n"
            "  under decision #1.\n", 2)

    def test_active_child_item_still_fails(self):
        self.assert_drift("- Parent.\n  - TBD per ADR 0001.\n", 2)

    def test_table_rows_do_not_borrow_authority(self):
        self.assertEqual(self.audit(
            '| Check | Rule |\n|---|---|\n'
            '| Token detector | Flags "proposed" language. |\n'
            '| Scope | ADR 0001 applies. |\n'), [])

    def test_active_claim_in_same_table_row_still_fails(self):
        self.assert_drift(
            "| Check | Rule |\n|---|---|\n| TBD | Per ADR 0001. |\n", 3)

    def test_detector_token_examples_within_authoritative_unit(self):
        self.assertEqual(self.audit(
            'ADR 0001: checker flags "proposed", "UNDECIDED", and "TBD" tokens.\n'), [])

    def test_quotes_without_detector_context_are_not_exempt(self):
        for word in ("proposed", "UNDECIDED", "TBD"):
            self.assert_drift(f'The policy is "{word}" per ADR 0001.')

    def test_detector_examples_do_not_hide_active_claim_in_same_unit(self):
        self.assert_drift(
            'Checker flags "TBD"; scope remains UNDECIDED per ADR 0001.')

    def test_unrelated_detection_verb_does_not_excuse_quoted_policy(self):
        self.assert_drift(
            'Checker flags invalid data; scope is "TBD" per ADR 0001.')

    def test_lowercase_and_curly_quoted_detector_tokens(self):
        self.assertEqual(self.audit(
            'ADR 0001: detector flags “undecided”/“proposed” language.'), [])

    def test_acceptance_criterion_token_vocabulary_is_not_active_uncertainty(self):
        criterion = ('Docs QA per ADR 0001: decision-consistency check '
                     '(no `TBD` / `UNDECIDED` / "proposed" language '
                     'in text that references an accepted ADR).')
        self.assertEqual(self.audit(criterion), [])
        self.assert_drift(criterion + ' The scope is still TBD per decision #1.')

    def test_explicitly_superseded_strikeout_is_history(self):
        self.assertEqual(self.audit(
            "| ~~Earlier proposed archive~~ **DEFERRED** under decision #1. |\n"), [])

    def test_strikeout_alone_is_not_a_waiver(self):
        self.assert_drift("| ~~proposed~~ per decision #1. |\n")

    def test_superseded_marker_does_not_hide_current_clause(self):
        self.assert_drift(
            "| ~~Earlier proposed option~~ **SUPERSEDED**; "
            "replacement TBD per decision #1. |\n")

    def test_historical_marker_inside_strikeout_is_not_authority(self):
        self.assert_drift("| ~~SUPERSEDED proposed~~ per decision #1. |\n")

    def test_unrelated_or_negated_markers_do_not_excuse_struck_claim(self):
        for prose in (
            "~~proposed~~ not **DEFERRED** per decision #1.",
            "**DEFERRED**: unrelated matter; ~~proposed~~ per decision #1.",
            "~~old option~~ **DEFERRED**; ~~proposed~~ per decision #1.",
        ):
            self.assert_drift(prose)

    def test_explicit_dated_strikeout_disposition(self):
        self.assertEqual(self.audit(
            "~~Earlier proposed option~~ **DEFERRED 2026-09-21** per decision #1."), [])

    def test_exact_past_tense_does_not_reopen_decision(self):
        self.assertEqual(self.audit("The implementation was a TBD per decision #1."), [])

    def test_past_tense_does_not_hide_current_uncertainty(self):
        self.assert_drift(
            "This was a TBD but remains UNDECIDED per decision #1.")

    def test_current_tense_still_fails(self):
        self.assert_drift("The implementation is a TBD per decision #1.")

    def test_unrelated_superseded_list_item_is_not_current_doctrine(self):
        self.assertEqual(self.audit(
            "- **Superseded proposal:** an earlier draft proposed a rule.\n"
            "- Current rule: ADR 0001 applies.\n"), [])

    def test_historical_reference_existence_is_still_checked(self):
        result = self.audit("| ~~proposed ADR 9999~~ **DEFERRED** per decision #1. |\n")
        self.assertEqual([r["code"] for r in result], ["unresolved_adr"])

    def test_templates_future_examples_and_private_labels_still_report_missing(self):
        for prose in (
            "Future M9: `docs/future.md`.",
            "Private-owned: `docs/private.md`.",
            "Example: `docs/example.md`.",
            "Template: `tests/fixtures/<id>/`.",
            "Runtime: `tests/fixtures/${{ inputs.batch_id }}/`.",
        ):
            with self.subTest(prose=prose):
                self.assertEqual([r["code"] for r in self.audit(prose)],
                                 ["unresolved_reference"])

    def test_path_validation_does_not_ignore_struck_or_quoted_targets(self):
        self.assertEqual([r["code"] for r in self.audit(
            '~~`docs/missing.md`~~ **DEFERRED**; detector flags "proposed".')],
            ["unresolved_reference"])

    def test_unit_lines_preserved_for_prose_heading_and_table(self):
        self.assertEqual(list(semantic_units(
            "# Title\n\nParagraph\nwrapped\n\n- One\n  wrapped\n"
            "- Two\n\n| A | B |\n| C | D |\n")),
            [(1, "# Title"), (3, "Paragraph\nwrapped"),
             (6, "- One\n  wrapped"), (8, "- Two"),
             (10, "| A | B |"), (11, "| C | D |")])

    def test_no_exception_list_or_cross_repository_fallback_is_implied(self):
        self.assertEqual(len(self.audit("`docs/missing.md`")), 1)
        self.assertEqual(len(self.audit("`docs/missing.md`")), 1)

    def test_metadata_recognition_does_not_weaken_nygard(self):
        changed = OLD.replace(b"accepted", b"proposed")
        self.assertTrue(nygard({PATH: OLD}, {PATH: changed}))
        changed = OLD.replace(b"Status: accepted", b"**Status:** proposed")
        self.assertTrue(nygard({PATH: OLD}, {PATH: changed}))
