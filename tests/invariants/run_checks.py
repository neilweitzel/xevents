"""Read-only public check runner; execute this from trusted code in future CI."""

import argparse
import json
from pathlib import Path
import sys

from checks import (
    ADR_PATH, declaration, diff_gate, docs_audit, g5_gate, git, jsonl_audit,
    nygard, read_pr, require, snapshot, text,
)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("check", choices=("boundary-write-set", "docs-qa", "jsonl-headers",
                                          "nygard-immutability", "boundary-write-set-in-diff",
                                          "g5-report-present-and-valid"))
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--base")
    parser.add_argument("--head")
    parser.add_argument("--pr", type=int)
    args = parser.parse_args()
    try:
        head = args.head or git(args.root, "rev-parse", "HEAD").decode().strip()
        if args.check in ("boundary-write-set-in-diff", "g5-report-present-and-valid"):
            require(args.pr is not None and args.head is not None, "pr_and_head_required")
            pr, files = read_pr(args.pr, args.head)
            base = snapshot(args.root, pr["base"]["sha"])
            gate = diff_gate if args.check == "boundary-write-set-in-diff" else g5_gate
            gate(files, pr["head"]["ref"], text(base, ADR_PATH))
        else:
            tree = snapshot(args.root, head)
            if args.check == "boundary-write-set":
                declaration(text(tree, ADR_PATH))
            elif args.check == "jsonl-headers":
                jsonl_audit(tree)
            elif args.check == "docs-qa":
                result = docs_audit(tree)
                print(json.dumps(result, sort_keys=True))
                return int(bool(result["issues"]))
            else:
                require(args.base is not None, "base_required")
                # Validate before supplying a revision to git.
                snapshot(args.root, args.base)
                merge_base = git(args.root, "merge-base", args.base, head).decode().strip()
                errors = nygard(snapshot(args.root, merge_base), tree)
                print(json.dumps({"issues": errors}, sort_keys=True))
                return int(bool(errors))
        print(json.dumps({"check": args.check, "result": "pass"}))
        return 0
    except Exception:
        # No raw API errors, PR bodies, or arbitrary paths are echoed.
        print(json.dumps({"check": args.check, "result": "failed_or_blocked"}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
