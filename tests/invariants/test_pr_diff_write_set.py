import copy
import subprocess
import unittest
from unittest.mock import patch

import checks
from test_boundary_write_set import ADR


def rows(*paths):
    return [{"filename": path, "status": "modified"} for path in paths]


class DiffTests(unittest.TestCase):
    def test_documentation_operator_pr_noop(self):
        self.assertTrue(checks.diff_gate(rows("docs/new.md", "README.md"), "operator/docs", ADR))

    def test_boundary_only_paths_pass_path_gate_not_proof_gate(self):
        for branch in ("boundary/batch", "operator/data"):
            self.assertTrue(checks.diff_gate(rows("data/aggregates/week.jsonl",
                                                *checks.WRITE_SET[1:]), branch, ADR))

    def test_mixed_data_and_code_refused_for_every_author_branch(self):
        for branch in ("boundary/batch", "renamed-branch", "main"):
            with self.subTest(branch=branch), self.assertRaises(ValueError):
                checks.diff_gate(rows("data/aggregates/a.jsonl", "scripts/escape.py"), branch, ADR)

    def test_boundary_branch_cannot_hide_as_docs_only(self):
        with self.assertRaises(ValueError):
            checks.diff_gate(rows("README.md"), "boundary/docs", ADR)

    def test_old_rename_and_copy_paths_are_checked(self):
        for status in ("renamed", "copied"):
            for old, new in (("data/aggregates/a.jsonl", "docs/a.md"),
                             ("docs/a.md", "data/aggregates/a.jsonl")):
                with self.subTest(status=status), self.assertRaises(ValueError):
                    checks.diff_gate([{"filename": new, "previous_filename": old,
                                       "status": status}], "operator", ADR)
        self.assertTrue(checks.diff_gate([{"filename": "data/aggregates/b.jsonl",
                                          "previous_filename": "data/aggregates/a.jsonl",
                                          "status": "renamed"}], "operator", ADR))

    def test_invalid_paths_and_non_jsonl_boundary_files_refused(self):
        for path in ("../escape", "/absolute", "data//aggregates/a.jsonl",
                     "data/aggregates/../escape", "data\\aggregates\\a.jsonl",
                     "data/aggregates/a\n.jsonl", "data/aggregates/a.py", "data/aggregates"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                checks.diff_gate(rows(path), "boundary/batch", ADR)

    def test_deletions_are_boundary_related_and_empty_or_malformed_diffs_fail(self):
        self.assertTrue(checks.boundary_related(
            [{"filename": "evidence-manifest.jsonl", "status": "removed"}], "operator"))
        for files in ([], rows("README.md", "README.md"), [{"filename": "README.md", "status": "?"}],
                      [{"filename": "README.md", "status": "renamed"}],
                      [{"filename": "README.md", "status": "modified", "previous_filename": "old"}]):
            with self.subTest(files=files), self.assertRaises((ValueError, KeyError)):
                checks.changed_paths(files)


class PublicApiTests(unittest.TestCase):
    def pr(self, count=1):
        return {"state": "open", "changed_files": count,
                "head": {"sha": "a" * 40, "ref": "operator/docs"},
                "base": {"sha": "b" * 40, "ref": "main",
                         "repo": {"full_name": checks.REPO}}}

    def test_all_pages_and_stable_head_are_required(self):
        pr = self.pr(101)
        first = rows(*(f"docs/{n}.md" for n in range(100)))
        with patch.object(checks, "api") as unused:
            data = iter([pr, first, rows("docs/100.md"), copy.deepcopy(pr)])
            calls = []
            def read(path):
                calls.append(path)
                return next(data)
            meta, files = checks.read_pr(25, "a" * 40, read)
            self.assertEqual(len(files), 101)
            self.assertIn("page=2", calls[2])
            self.assertEqual(meta, pr)
            unused.assert_not_called()

    def test_truncation_changed_base_head_wrong_target_and_limits_refused(self):
        pr = self.pr()
        for after in ({**pr, "changed_files": 2},
                      {**pr, "head": {"sha": "c" * 40, "ref": "operator/docs"}},
                      {**pr, "base": {**pr["base"], "sha": "c" * 40}}):
            with self.subTest(after=after), self.assertRaises(ValueError):
                checks.read_pr(25, "a" * 40, lambda _, data=iter([pr, rows("README.md"), after]): next(data))
        for first in (self.pr(3000), self.pr(0), {**pr, "state": "closed"},
                      {**pr, "base": {**pr["base"], "repo": {"full_name": "other/repo"}}}):
            with self.assertRaises(ValueError):
                checks.read_pr(25, "a" * 40, lambda _: first)
        for number, head in ((0, "a" * 40), (True, "a" * 40), (25, "bad"), (25, "b" * 40)):
            with self.assertRaises(ValueError):
                checks.read_pr(number, head, lambda _: pr)
        with self.assertRaises(ValueError):
            checks.read_pr(25, "a" * 40, lambda _, data=iter([pr, []]): next(data))

    def test_api_destination_fixed_read_only_and_failure_sanitized(self):
        for code in (0, 1):
            result = subprocess.CompletedProcess([], code, b'{"ok":true}', b"private-error")
            with patch.object(checks.subprocess, "run", return_value=result) as run:
                if code:
                    with self.assertRaisesRegex(ValueError, "^public_api_failed$"):
                        checks.api("pulls/25")
                else:
                    self.assertEqual(checks.api("pulls/25"), {"ok": True})
                self.assertEqual(run.call_args.args[0],
                                 ["gh", "api", "--hostname", "github.com", "repos/neilweitzel/xevents/pulls/25"])
