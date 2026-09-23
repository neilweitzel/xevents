"""Pinned, offline public shadow runner. Never executes audited code."""

import argparse
import json
from pathlib import Path
import re
import subprocess
import sys
from types import ModuleType

CODE_FILES = ("checks.py", "reference_inventory.py", "reference_evidence.py",
              "run_reference_evidence.py")


def verify_code(root, revision, paths):
    if not re.fullmatch(r"[0-9a-f]{40}", revision):
        raise ValueError("invalid_code_revision")
    verified = {}
    for name in paths:
        path = root / name
        if any(p.is_symlink() for p in (path, *path.parents)):
            raise ValueError("code_symlink")
        result = subprocess.run(["git", "-C", str(root), "show", f"{revision}:{name}"],
                                capture_output=True, check=True, timeout=30)
        if path.read_bytes() != result.stdout:
            raise ValueError("code_revision_mismatch")
        verified[name] = result.stdout
    return verified


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--code-ref", required=True)
    parser.add_argument("--policy-ref", required=True)
    parser.add_argument("--head", required=True)
    args = parser.parse_args()
    try:
        root = Path(__file__).resolve().parents[2]
        verified = verify_code(root, args.code_ref,
                               ["tests/invariants/" + p for p in CODE_FILES])
        # Execute the verified bytes directly, never a cached or re-read module.
        for name in ("checks", "reference_inventory", "reference_evidence"):
            path = "tests/invariants/" + name + ".py"
            module = ModuleType(name)
            module.__file__ = str(root / path)
            sys.modules[name] = module
            exec(compile(verified[path], module.__file__, "exec"), module.__dict__)
        snapshot = sys.modules["checks"].snapshot
        answer = sys.modules["reference_evidence"].audit_public(
            snapshot(root, args.head), snapshot(root, args.policy_ref))
        answer["revisions"] = {"code": args.code_ref, "policy": args.policy_ref,
                               "head": args.head}
        print(json.dumps(answer, sort_keys=True))
        # A shadow report cannot turn existing strict failures into a success.
        return int(bool(answer["raw_findings"]) or
                   "evidence-invalid-or-stale" in answer["counts"])
    except Exception:
        print(json.dumps({"mode": "shadow-only", "result": "failed_or_blocked"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
