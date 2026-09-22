import unittest
from checks import jsonl, jsonl_audit

GOOD = b'{"file_purpose":"Test","schema_version":"0"}\n{"value":1}\n'


class HeaderTests(unittest.TestCase):
    def test_header_is_separate_from_data(self):
        header, rows = jsonl(GOOD)
        self.assertEqual(header["schema_version"], "0")
        self.assertEqual(rows, [{"value": 1}])

    def test_missing_malformed_and_duplicate_headers_fail(self):
        for raw in (b"", GOOD[:-1], b'{}\n', b'{"value":1}\n', GOOD + b"\n",
                    b"\xef\xbb\xbf" + GOOD, b"[]\n",
                    b'{"file_purpose":"A","file_purpose":"B","schema_version":"0"}\n',
                    b'{"file_purpose":"A","schema_version":0}\n',
                    GOOD + b'{"n":NaN}\n'):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                jsonl(raw)

    def test_audit_requires_manifest_and_checks_nested_aggregates(self):
        tree = {"evidence-manifest.jsonl": GOOD, "data/aggregates/week/a.jsonl": GOOD}
        self.assertEqual(len(jsonl_audit(tree)), 2)
        for bad in ({}, {**tree, "data/aggregates/b.jsonl": b"{}\n"}):
            with self.assertRaises(ValueError):
                jsonl_audit(bad)

    def test_explicit_private_profiles_preserve_existing_contracts(self):
        static = b'{"file_purpose":"Static names"}\n{"entity_id":"synthetic"}\n'
        homoglyphs = b'{"table_version":"1.0.0","note":"Mapping"}\n{"source_char":"x","target_char":"y"}\n'
        tree = {"evidence-manifest.jsonl": GOOD, "denylist/static.jsonl": static,
                "denylist/homoglyphs.jsonl": homoglyphs}
        self.assertEqual(len(jsonl_audit(tree, private=True)), 3)
        for raw, profile in ((static, "standard"), (homoglyphs, "standard"),
                             (GOOD, "unknown"), (b'{"file_purpose":"x","entity_id":"data"}\n', "static"),
                             (b'{"file_purpose":"x","schema_version":0}\n', "static")):
            with self.subTest(profile=profile), self.assertRaises(ValueError):
                jsonl(raw, profile)
        for bad in ({"evidence-manifest.jsonl": GOOD},
                    {**tree, "denylist/new.jsonl": static}):
            with self.assertRaises(ValueError):
                jsonl_audit(bad, private=True)
