import unittest
from pathlib import Path
from checks import declaration, WRITE_SET

ROOT = Path(__file__).resolve().parents[2]
ADR = (ROOT / "docs/adr/0012-aggregation-boundary-transport.md").read_text()


class BoundaryDeclarationTests(unittest.TestCase):
    def test_current_public_declaration(self):
        self.assertEqual(set(declaration(ADR)), set(WRITE_SET))

    def test_synthetic_missing_duplicate_added_and_widened_paths_rejected(self):
        for body in ("", ADR.replace("### Boundary write set", "### Elsewhere"),
                     ADR + "\n### Boundary write set\n",
                     ADR.replace("- `data/aggregates/`", "- `data/`"),
                     ADR.replace("Nothing else.", "- `other/`\n\nNothing else."),
                     ADR.replace("- `data/aggregates/`", "- `data/aggregates/`\n- `data/aggregates/`")):
            with self.subTest(body=body[:20]), self.assertRaises(ValueError):
                declaration(body)

    def test_unrelated_backticks_are_not_declarations(self):
        self.assertEqual(declaration(ADR + "\n`not-a-boundary-path`\n"), declaration(ADR))
