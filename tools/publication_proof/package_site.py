"""Explicit static artifact allowlist: no repo, tests, private input or tooling."""
from __future__ import annotations

import argparse
from pathlib import Path

ASSETS = (
    "index.html", "bootstrap.mjs", "research.mjs", "aggregate.mjs", "app.mjs",
    "model.mjs", "style.css", "favicon.svg", "fonts/LICENSE",
    "fonts/ibm-plex-sans-latin-400-normal.woff2",
    "fonts/ibm-plex-sans-latin-500-normal.woff2",
    "fonts/ibm-plex-sans-latin-600-normal.woff2",
)
DATA = ("data/aggregates/view1.jsonl", "evidence-manifest.jsonl",
        "coverage-boundary-statement.md")


def package(root: Path, output: Path) -> None:
    if output.exists():
        raise ValueError("output_exists")
    rows = [(root / "app" / name, output / name) for name in ASSETS]
    rows += [(root / name, output / name) for name in DATA]
    for source, _ in rows:
        if source.is_symlink() or not source.is_file() or source.stat().st_size > 1048576:
            raise ValueError("unsafe_asset")
    for source, destination in rows:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(source.read_bytes())
    (output / ".nojekyll").write_bytes(b"")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    package(args.root, args.output)
