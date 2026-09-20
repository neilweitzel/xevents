"""Tests for the frozen data model: round-trips, immutability, two clocks."""

from __future__ import annotations

import dataclasses
from datetime import UTC, datetime

import pytest

from xevents.models import EvidenceArtifact, Observation, PollRun, SourceItem

DT = datetime(2026, 9, 20, 17, 44, 25, tzinfo=UTC)


def test_source_item_round_trip() -> None:
    item = SourceItem(
        misp_uuid="uuid-1",
        post_title="ACME",
        group_name="lockbit",
        discovered_utc=DT,
        description="d",
        link_url="https://www.ransomlook.io/post/x",
        magnet=None,
        screen_url="https://www.ransomlook.io/screenshots/x.png",
        private=False,
    )
    assert SourceItem.from_dict(item.to_dict()) == item


def test_observation_round_trip() -> None:
    obs = Observation(
        id="obs-1",
        source_name="ransomlook_api",
        source_item_key="uuid-1",
        claim_type="victim_listing",
        subject_raw="ACME CORP",
        observed_at=DT,
        source_claimed_at=datetime(2026, 9, 19, 12, 0, tzinfo=UTC),
        raw_payload={"post_title": "ACME CORP"},
        pipeline_version="ingest-ransomlook/v0.1.0",
        evidence_hashes=("abc", "def"),
    )
    assert Observation.from_dict(obs.to_dict()) == obs


def test_observation_two_clocks_preserved() -> None:
    """observed_at (we saw it) and source_claimed_at (they claim it)
    are distinct and both survive serialization."""
    observed = datetime(2026, 9, 20, 18, 0, tzinfo=UTC)
    claimed = datetime(2026, 9, 19, 12, 0, tzinfo=UTC)
    obs = Observation(
        id="o",
        source_name="s",
        source_item_key="k",
        claim_type="victim_listing",
        subject_raw="X",
        observed_at=observed,
        source_claimed_at=claimed,
        raw_payload={},
        pipeline_version="v",
    )
    back = Observation.from_dict(obs.to_dict())
    assert back.observed_at == observed
    assert back.source_claimed_at == claimed
    assert back.observed_at != back.source_claimed_at


def test_observation_null_claimed_at() -> None:
    obs = Observation(
        id="o",
        source_name="s",
        source_item_key="k",
        claim_type="victim_listing",
        subject_raw="X",
        observed_at=DT,
        source_claimed_at=None,
        raw_payload={},
        pipeline_version="v",
    )
    assert Observation.from_dict(obs.to_dict()).source_claimed_at is None


@pytest.mark.parametrize("cls_name", ["Observation", "SourceItem", "EvidenceArtifact", "PollRun"])
def test_models_are_frozen(cls_name: str) -> None:
    import xevents.models as m

    cls = getattr(m, cls_name)
    instance = cls.__new__(cls)
    with pytest.raises(dataclasses.FrozenInstanceError):
        instance.id = "mutated"


def test_evidence_artifact_round_trip_with_null_note() -> None:
    artifact = EvidenceArtifact(
        sha256="deadbeef",
        kind="screenshot",
        captured_at=DT,
        byte_size=42,
        redaction_note=None,
    )
    assert EvidenceArtifact.from_dict(artifact.to_dict()) == artifact


def test_evidence_artifact_round_trip_with_note() -> None:
    artifact = EvidenceArtifact(
        sha256="deadbeef",
        kind="screenshot",
        captured_at=DT,
        byte_size=42,
        redaction_note="blurred phone number",
    )
    assert EvidenceArtifact.from_dict(artifact.to_dict()).redaction_note == ("blurred phone number")


def test_poll_run_round_trip_null_finished() -> None:
    run = PollRun(
        id="r",
        source_name="ransomlook_api",
        started_at=DT,
        finished_at=None,
        status="skipped",
        items_seen=0,
        items_new=0,
        items_filtered=0,
        items_errored=0,
        poller_version="v",
        error_log=None,
        evidence_bytes=0,
    )
    assert PollRun.from_dict(run.to_dict()) == run


def test_from_dict_rejects_wrong_types() -> None:
    obs = Observation(
        id="o",
        source_name="s",
        source_item_key="k",
        claim_type="victim_listing",
        subject_raw="X",
        observed_at=DT,
        source_claimed_at=None,
        raw_payload={},
        pipeline_version="v",
    )
    bad = obs.to_dict()
    bad["observed_at"] = 12345
    with pytest.raises(TypeError, match="observed_at"):
        Observation.from_dict(bad)


def test_from_dict_rejects_bool_as_int() -> None:
    run = PollRun(
        id="r",
        source_name="s",
        started_at=DT,
        finished_at=DT,
        status="ok",
        items_seen=1,
        items_new=1,
        items_filtered=0,
        items_errored=0,
        poller_version="v",
        error_log=None,
        evidence_bytes=0,
    )
    bad = run.to_dict()
    bad["items_seen"] = True
    with pytest.raises(TypeError, match="items_seen"):
        PollRun.from_dict(bad)
