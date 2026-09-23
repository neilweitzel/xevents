"""Exercise the real pinned CLI in disposable local repositories."""

import json
from pathlib import Path
import py_compile
import subprocess
import sys
import tempfile
import unittest

from test_reference_evidence import sample_policy


class EvidenceRunnerTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.source = Path(__file__).parent
        self.code = ["tests/invariants/" + name for name in (
            "checks.py", "reference_inventory.py", "reference_evidence.py",
            "run_reference_evidence.py")]
        tree, _, _ = sample_policy()
        tree.update({path: (self.source / Path(path).name).read_bytes() for path in self.code})
        for path, data in tree.items():
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
        self.git("init", "--quiet")
        self.git("config", "user.name", "Evidence Test")
        self.git("config", "user.email", "test@example.invalid")
        self.git("config", "commit.gpgsign", "false")
        self.base = self.commit()

    def git(self, *args):
        return subprocess.run(["git", "-C", str(self.root), *args],
                              capture_output=True, check=True, text=True).stdout.strip()

    def commit(self):
        self.git("add", ".")
        self.git("commit", "--quiet", "-m", "Synthetic evidence test")
        return self.git("rev-parse", "HEAD")

    def run_cli(self, code=None, policy=None, head=None):
        result = subprocess.run(
            [sys.executable, "-B", str(self.root / self.code[-1]),
             "--code-ref", self.base if code is None else code,
             "--policy-ref", self.base if policy is None else policy,
             "--head", self.base if head is None else head],
            capture_output=True, text=True, timeout=30)
        self.assertEqual(result.stderr, "")
        self.assertEqual(result.returncode, 1)
        return json.loads(result.stdout)

    def blocked(self, report):
        self.assertEqual(report, {"mode": "shadow-only", "result": "failed_or_blocked"})

    def test_real_runner_reports_raw_failure_and_exact_pins(self):
        report = self.run_cli()
        self.assertEqual(report["raw_findings"], 1)
        self.assertEqual(report["resolved_findings"], 0)
        self.assertEqual(report["revisions"], dict.fromkeys(("code", "policy", "head"), self.base))
        self.assertEqual(self.git("status", "--porcelain"), "")

    def test_mutable_or_invalid_pins_are_rejected(self):
        for name in ("code", "policy", "head"):
            for value in ("HEAD", "main", "a" * 39, "0" * 40):
                with self.subTest(name=name, value=value):
                    self.blocked(self.run_cli(**{name: value}))

    def test_modified_local_import_is_blocked_before_execution(self):
        marker = self.root / "executed"
        path = self.root / "tests/invariants/checks.py"
        path.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        self.blocked(self.run_cli())
        self.assertFalse(marker.exists())

    def test_self_edited_candidate_policy_cannot_approve_itself(self):
        path = self.root / "docs/reference-evidence.json"
        policy = json.loads(path.read_text())
        policy["rules"]["PR-01"]["complete"] = True
        path.write_text(json.dumps(policy))
        candidate = self.commit()
        self.blocked(self.run_cli(head=candidate))

    def test_candidate_code_is_data_not_executed(self):
        marker = self.root / "executed"
        path = self.root / "tests/invariants/checks.py"
        path.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        candidate = self.commit()
        self.git("checkout", self.base, "--", *self.code)
        report = self.run_cli(head=candidate)
        self.assertEqual(report["raw_findings"], 1)
        self.assertFalse(marker.exists())

    def test_symlink_snapshot_is_blocked(self):
        (self.root / "untrusted-link").symlink_to("/etc/passwd")
        candidate = self.commit()
        self.blocked(self.run_cli(head=candidate))

    def test_symlink_import_is_blocked_before_execution(self):
        path = self.root / "tests/invariants/reference_evidence.py"
        alternate = self.root / "alternate.py"
        alternate.write_bytes(path.read_bytes())
        path.unlink()
        path.symlink_to(alternate)
        self.blocked(self.run_cli())

    def test_candidate_source_change_has_sanitized_failure(self):
        path = self.root / "README.md"
        path.write_bytes(path.read_bytes() + b"\nPRIVATE-CANARY-DO-NOT-ECHO\n")
        candidate = self.commit()
        report = self.run_cli(head=candidate)
        self.blocked(report)
        self.assertNotIn("PRIVATE-CANARY", json.dumps(report))

    def test_unchecked_cached_bytecode_cannot_replace_verified_source(self):
        marker = self.root / "executed"
        path = self.root / "tests/invariants/checks.py"
        trusted = path.read_bytes()
        path.write_text(f"from pathlib import Path\nPath({str(marker)!r}).touch()\n")
        py_compile.compile(str(path), doraise=True,
                           invalidation_mode=py_compile.PycInvalidationMode.UNCHECKED_HASH)
        path.write_bytes(trusted)
        report = self.run_cli()
        self.assertEqual(report["raw_findings"], 1)
        self.assertFalse(marker.exists())


if __name__ == "__main__":
    unittest.main()
