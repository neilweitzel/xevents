"""File-backed storage implementing the physical mapping in
docs/data-model.md: append-only JSONL under data/, content-addressed
evidence under evidence/<sha256>. No database server (ADR 0009)."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
from pathlib import Path

APPEND_ONLY_FILES = (
    "observations.jsonl",
    "correction_events.jsonl",
    "confidence_assessments.jsonl",
    "poll_runs.jsonl",
    "evidence_artifacts.jsonl",
    "model_versions.jsonl",
)


class DataStore:
    def __init__(self, root: Path) -> None:
        self.root = root
        self.data_dir = root / "data"
        self.evidence_dir = root / "evidence"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.evidence_dir.mkdir(parents=True, exist_ok=True)

    # -- JSONL tables --------------------------------------------------------

    def _jsonl_path(self, name: str) -> Path:
        return self.data_dir / name

    def append_jsonl(self, name: str, obj: dict[str, object]) -> None:
        """Append one record. Never rewrites existing lines."""
        with open(self._jsonl_path(name), "a", encoding="utf-8") as fh:
            fh.write(json.dumps(obj, sort_keys=True, ensure_ascii=False) + "\n")

    def read_jsonl(self, name: str) -> list[dict[str, object]]:
        """Read all records. Missing file reads as empty."""
        path = self._jsonl_path(name)
        if not path.exists():
            return []
        records: list[dict[str, object]] = []
        with open(path, encoding="utf-8") as fh:
            for line_number, line in enumerate(fh, start=1):
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                if not isinstance(record, dict):
                    raise TypeError(f"{name}:{line_number}: expected a JSON object")
                records.append(record)
        return records

    # -- listing state (mutable view, rewritten atomically) -------------------

    def load_listing_state(self) -> dict[str, dict[str, str]]:
        path = self.data_dir / "listing_state.json"
        if not path.exists():
            return {}
        with open(path, encoding="utf-8") as fh:
            payload = json.load(fh)
        if not isinstance(payload, dict):
            raise TypeError("listing_state.json must be a JSON object")
        state: dict[str, dict[str, str]] = {}
        for key, value in payload.items():
            if not isinstance(value, dict):
                raise TypeError(f"listing_state[{key!r}] must be an object")
            state[key] = {str(k): str(v) for k, v in value.items()}
        return state

    def save_listing_state(self, state: dict[str, dict[str, str]]) -> None:
        """Atomic rewrite: temp file + rename, so a crash never leaves a
        half-written state file."""
        path = self.data_dir / "listing_state.json"
        fd, tmp_name = tempfile.mkstemp(dir=str(self.data_dir), prefix="listing_state.")
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as fh:
                json.dump(state, fh, sort_keys=True, ensure_ascii=False, indent=2)
                fh.write("\n")
            os.replace(tmp_name, path)
        except BaseException:
            try:
                os.unlink(tmp_name)
            except OSError:
                pass
            raise

    # -- evidence (content-addressed, write-once) ------------------------------

    @staticmethod
    def sha256_bytes(data: bytes) -> str:
        return hashlib.sha256(data).hexdigest()

    def write_evidence(self, data: bytes) -> str:
        """Store bytes at evidence/<sha256>. Write-once: existing bytes are
        never overwritten."""
        digest = self.sha256_bytes(data)
        path = self.evidence_dir / digest
        if not path.exists():
            # Exclusive create: two writers racing is an error, not a silent
            # overwrite — but the pipeline is single-writer by concurrency
            # group, so this is a safety net, not a hot path.
            with open(path, "xb") as fh:
                fh.write(data)
        return digest

    def read_evidence(self, digest: str) -> bytes:
        with open(self.evidence_dir / digest, "rb") as fh:
            return fh.read()

    def verify_evidence(self, digest: str) -> bool:
        """True iff the stored bytes hash to the digest (ADR 0003)."""
        try:
            return self.sha256_bytes(self.read_evidence(digest)) == digest
        except OSError:
            return False

    def evidence_size_bytes(self) -> int:
        total = 0
        for entry in self.evidence_dir.iterdir():
            if entry.is_file():
                total += entry.stat().st_size
        return total
