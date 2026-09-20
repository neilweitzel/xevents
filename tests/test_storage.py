"""Tests for the file-backed store: append-only JSONL, atomic state,
content-addressed evidence."""

from __future__ import annotations

from pathlib import Path

import pytest

from xevents.storage import APPEND_ONLY_FILES, DataStore


@pytest.fixture()
def store(tmp_path: Path) -> DataStore:
    return DataStore(tmp_path)


def test_append_and_read_round_trip(store: DataStore) -> None:
    store.append_jsonl("observations.jsonl", {"id": "a"})
    store.append_jsonl("observations.jsonl", {"id": "b"})
    records = store.read_jsonl("observations.jsonl")
    assert [r["id"] for r in records] == ["a", "b"]


def test_read_missing_file_is_empty(store: DataStore) -> None:
    assert store.read_jsonl("observations.jsonl") == []


def test_read_skips_blank_lines(store: DataStore, tmp_path: Path) -> None:
    (tmp_path / "data" / "observations.jsonl").write_text('{"id":"a"}\n\n{"id":"b"}\n')
    assert [r["id"] for r in store.read_jsonl("observations.jsonl")] == ["a", "b"]


def test_read_rejects_non_object_lines(store: DataStore, tmp_path: Path) -> None:
    (tmp_path / "data" / "observations.jsonl").write_text("[1,2]\n")
    with pytest.raises(TypeError, match="JSON object"):
        store.read_jsonl("observations.jsonl")


def test_append_only_invariant(store: DataStore, tmp_path: Path) -> None:
    """A later append must never rewrite earlier lines. This is the
    CI-level guarantee from AGENTS.md, tested at the unit level."""
    store.append_jsonl("observations.jsonl", {"id": "first"})
    before = (tmp_path / "data" / "observations.jsonl").read_bytes()
    store.append_jsonl("observations.jsonl", {"id": "second"})
    after = (tmp_path / "data" / "observations.jsonl").read_bytes()
    assert after.startswith(before)
    assert after[len(before) :].strip() == b'{"id": "second"}'


def test_listing_state_round_trip(store: DataStore) -> None:
    state = {"uuid-1": {"last_seen_at": "2026-09-20T00:00:00+00:00", "observation_id": "o1"}}
    store.save_listing_state(state)
    assert store.load_listing_state() == state


def test_listing_state_missing_is_empty(store: DataStore) -> None:
    assert store.load_listing_state() == {}


def test_listing_state_save_is_atomic(store: DataStore, tmp_path: Path) -> None:
    store.save_listing_state({"k": {"v": "1"}})
    leftovers = list((tmp_path / "data").glob("listing_state.*"))
    assert leftovers == [tmp_path / "data" / "listing_state.json"]


def test_listing_state_rejects_non_object(store: DataStore, tmp_path: Path) -> None:
    (tmp_path / "data" / "listing_state.json").write_text("[1]\n")
    with pytest.raises(TypeError, match="JSON object"):
        store.load_listing_state()


def test_write_evidence_content_addressed(store: DataStore) -> None:
    digest = store.write_evidence(b"hello")
    assert digest == "2cf24dba5fb0a30e26e83b2ac5b9e29e1b161e5c1fa7425e73043362938b9824"
    assert store.read_evidence(digest) == b"hello"


def test_write_evidence_write_once(store: DataStore, tmp_path: Path) -> None:
    digest = store.write_evidence(b"hello")
    # Second write of identical bytes is a no-op, not an overwrite.
    assert store.write_evidence(b"hello") == digest
    assert store.read_evidence(digest) == b"hello"


def test_verify_evidence_true(store: DataStore) -> None:
    digest = store.write_evidence(b"bytes")
    assert store.verify_evidence(digest)


def test_verify_evidence_detects_tamper(store: DataStore, tmp_path: Path) -> None:
    digest = store.write_evidence(b"bytes")
    (tmp_path / "evidence" / digest).write_bytes(b"tampered")
    assert not store.verify_evidence(digest)


def test_verify_evidence_missing_is_false(store: DataStore) -> None:
    assert not store.verify_evidence("0" * 64)


def test_evidence_size_bytes(store: DataStore) -> None:
    store.write_evidence(b"12345")
    store.write_evidence(b"1234567")
    assert store.evidence_size_bytes() == 12


def test_creates_directories(tmp_path: Path) -> None:
    DataStore(tmp_path / "nested" / "root")
    assert (tmp_path / "nested" / "root" / "data").is_dir()
    assert (tmp_path / "nested" / "root" / "evidence").is_dir()


def test_append_only_file_registry() -> None:
    assert "observations.jsonl" in APPEND_ONLY_FILES
    assert "poll_runs.jsonl" in APPEND_ONLY_FILES
