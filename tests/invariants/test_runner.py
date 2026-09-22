from contextlib import redirect_stdout
import io
import runpy
import subprocess
import sys
import unittest
from unittest.mock import patch

import checks
import run_checks
from test_boundary_write_set import ADR
from test_docs_qa import TREE
from test_jsonl_headers import GOOD
import test_pr_diff_write_set as pr_tests


class RunnerTests(unittest.TestCase):
    def test_git_snapshot_rejects_symlink_submodule_and_bad_revision(self):
        for entry in (b"120000 blob " + b"a"*40 + b"\tlink\0",
                      b"160000 commit " + b"a"*40 + b"\tsubmodule\0"):
            with patch.object(checks, "git", return_value=entry), self.assertRaises(ValueError):
                checks.snapshot(".", "b"*40)
        with self.assertRaises(ValueError):
            checks.snapshot(".", "--all")
        with patch.object(checks, "git", side_effect=[
                b"100644 blob " + b"a"*40 + b"\tREADME.md\0", b"hello"]):
            self.assertEqual(checks.snapshot(".", "b"*40), {"README.md": b"hello"})

    def test_git_command_is_explicit_read_and_errors_sanitized(self):
        for code in (0, 1):
            with patch.object(checks.subprocess, "run", return_value=
                              subprocess.CompletedProcess([], code, b"ok", b"secret")) as run:
                if code:
                    with self.assertRaisesRegex(ValueError, "^git_read_failed$"):
                        checks.git("/repo", "rev-parse", "HEAD")
                else:
                    self.assertEqual(checks.git("/repo", "rev-parse", "HEAD"), b"ok")
                self.assertEqual(run.call_args.args[0][:3], ["git", "-C", "/repo"])

    def test_all_runner_modes_pass_only_their_actual_checks(self):
        tree = {**TREE, checks.ADR_PATH: ADR.encode(), "evidence-manifest.jsonl": GOOD}
        for mode in ("boundary-write-set", "docs-qa", "jsonl-headers", "nygard-immutability",
                     "boundary-write-set-in-diff", "g5-report-present-and-valid"):
            with self.subTest(mode=mode), patch.object(sys, "argv", [
                    "run", mode, "--head", "a"*40, "--base", "b"*40, "--pr", "25"]), \
                 patch.object(run_checks, "snapshot", return_value=tree), \
                 patch.object(run_checks, "git", return_value=b"a"*40 + b"\n"), \
                 patch.object(run_checks, "read_pr", return_value=(pr_tests.PublicApiTests().pr(), pr_tests.rows("README.md"))), \
                 redirect_stdout(io.StringIO()):
                # Real ADR references other docs absent from this synthetic tree.
                self.assertEqual(run_checks.main(), 1 if mode == "docs-qa" else 0)

    def test_runner_does_not_echo_exception_secrets(self):
        with patch.object(sys, "argv", ["run", "g5-report-present-and-valid"]), \
             patch.object(run_checks, "git", side_effect=ValueError("private-secret")), \
             redirect_stdout(io.StringIO()) as output:
            self.assertEqual(run_checks.main(), 1)
            self.assertNotIn("private-secret", output.getvalue())

    def test_script_entrypoint_fails_closed(self):
        with patch.object(sys, "argv", ["run", "g5-report-present-and-valid", "--head", "a"*40]), \
             redirect_stdout(io.StringIO()), self.assertRaises(SystemExit) as result:
            runpy.run_path(run_checks.__file__, run_name="__main__")
        self.assertEqual(result.exception.code, 1)
