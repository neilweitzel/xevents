"""End-to-end pipeline tests with a mocked RansomLook API."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

import httpx
import pytest

from xevents import config
from xevents.models import Observation, PollRun
from xevents.pipeline import (
    last_successful_poll_at,
    redact_png,
    run_backfill,
    run_poll,
    should_poll,
)
from xevents.storage import DataStore

NOW = datetime(2026, 9, 20, 18, 0, 0, tzinfo=UTC)
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64


def raw_item(uuid: str, title: str = "ACME CORP", **overrides: object) -> dict[str, object]:
    item: dict[str, object] = {
        "post_title": title,
        "group_name": "lockbit",
        "discovered": "2026-09-19 12:00:00",
        "description": "d",
        "link": "/post/x",
        "magnet": "None",
        "screen": "screenshots/x.png",
        "private": "False",
        "misp_uuid": uuid,
    }
    item.update(overrides)
    return item


def make_client(
    items: list[dict[str, object]],
    *,
    screenshot_404: bool = False,
    api_500: bool = False,
    calls: list[str] | None = None,
) -> httpx.Client:
    def handler(request: httpx.Request) -> httpx.Response:
        if calls is not None:
            calls.append(str(request.url))
        path = request.url.path
        if path.startswith("/api/"):
            if api_500:
                return httpx.Response(500, text="boom")
            return httpx.Response(200, json=items)
        if path.startswith("/screenshots/"):
            if screenshot_404:
                return httpx.Response(404, text="gone")
            return httpx.Response(200, content=PNG)
        return httpx.Response(404, text="unexpected")

    return httpx.Client(transport=httpx.MockTransport(handler))


def read_observations(root: Path) -> list[Observation]:
    return [Observation.from_dict(r) for r in DataStore(root).read_jsonl("observations.jsonl")]


def read_runs(root: Path) -> list[PollRun]:
    return [PollRun.from_dict(r) for r in DataStore(root).read_jsonl("poll_runs.jsonl")]


def test_full_poll_run(tmp_path: Path) -> None:
    items = [
        raw_item("uuid-1"),
        raw_item("uuid-2", group_name="audit team"),
        raw_item("uuid-3", private="True"),
    ]
    run = run_poll(str(tmp_path), make_client(items), now=NOW)

    assert run.status == "ok"
    assert run.items_seen == 3
    assert run.items_new == 1
    assert run.items_filtered == 2
    assert run.items_errored == 0
    assert run.evidence_bytes > 0

    observations = read_observations(tmp_path)
    assert len(observations) == 1
    obs = observations[0]
    assert obs.subject_raw == "ACME CORP"  # verbatim, un-normalized
    assert obs.source_item_key == "uuid-1"
    assert obs.claim_type == "victim_listing"
    assert obs.observed_at == NOW
    assert obs.source_claimed_at == datetime(2026, 9, 19, 12, 0, tzinfo=UTC)
    assert obs.pipeline_version == config.POLLER_VERSION
    assert len(obs.evidence_hashes) == 2  # raw_payload + screenshot

    store = DataStore(tmp_path)
    assert len(store.read_jsonl("evidence_artifacts.jsonl")) == 2
    for digest in obs.evidence_hashes:
        assert store.verify_evidence(digest)

    runs = read_runs(tmp_path)
    assert len(runs) == 1
    assert runs[0].finished_at is not None


def test_rerun_is_idempotent(tmp_path: Path) -> None:
    client = make_client([raw_item("uuid-1")])
    run_poll(str(tmp_path), client, now=NOW)
    second = run_poll(str(tmp_path), client, now=NOW + timedelta(hours=7), force=True)
    assert second.items_seen == 1
    assert second.items_new == 0
    assert len(read_observations(tmp_path)) == 1

    state = DataStore(tmp_path).load_listing_state()
    assert state["uuid-1"]["last_seen_at"] == (NOW + timedelta(hours=7)).isoformat()


def test_guard_skips_rapid_repoll(tmp_path: Path) -> None:
    calls: list[str] = []
    client = make_client([raw_item("uuid-1")], calls=calls)
    first = run_poll(str(tmp_path), client, now=NOW)
    assert first.status == "ok"
    api_calls_before = len([u for u in calls if "/api/" in u])
    second = run_poll(str(tmp_path), client, now=NOW + timedelta(hours=1))
    assert second.status == "skipped"
    api_calls_after = len([u for u in calls if "/api/" in u])
    assert api_calls_after == api_calls_before  # the API was never hit again
    assert len(read_runs(tmp_path)) == 2  # skips are still manifested


def test_force_bypasses_guard(tmp_path: Path) -> None:
    client = make_client([raw_item("uuid-1")])
    run_poll(str(tmp_path), client, now=NOW)
    run = run_poll(str(tmp_path), client, now=NOW + timedelta(minutes=5), force=True)
    assert run.status == "ok"


def test_guard_allows_after_interval(tmp_path: Path) -> None:
    client = make_client([raw_item("uuid-1")])
    run_poll(str(tmp_path), client, now=NOW)
    run = run_poll(str(tmp_path), client, now=NOW + timedelta(hours=7))
    assert run.status == "ok"


def test_screenshot_failure_is_partial_not_fatal(tmp_path: Path) -> None:
    run = run_poll(str(tmp_path), make_client([raw_item("uuid-1")], screenshot_404=True), now=NOW)
    assert run.status == "partial"
    assert run.items_new == 1
    assert run.items_errored == 1
    obs = read_observations(tmp_path)[0]
    assert len(obs.evidence_hashes) == 1  # raw_payload only


def test_api_failure_manifests_error(tmp_path: Path) -> None:
    run = run_poll(str(tmp_path), make_client([], api_500=True), now=NOW)
    assert run.status == "error"
    assert run.error_log is not None
    assert read_observations(tmp_path) == []


def test_unparseable_item_does_not_kill_run(tmp_path: Path) -> None:
    bad = raw_item("uuid-bad")
    del bad["misp_uuid"]
    run = run_poll(str(tmp_path), make_client([bad, raw_item("uuid-1")]), now=NOW)
    assert run.status == "partial"
    assert run.items_errored == 1
    assert run.items_new == 1


def test_backfill_clock_semantics(tmp_path: Path) -> None:
    from datetime import date

    backfill_at = datetime(2026, 9, 20, 20, 0, tzinfo=UTC)
    run = run_backfill(
        str(tmp_path),
        make_client([raw_item("uuid-1")]),
        date(2026, 1, 1),
        date(2026, 1, 31),
        now=backfill_at,
    )
    assert run.status == "ok"
    obs = read_observations(tmp_path)[0]
    assert obs.observed_at == backfill_at  # we saw it during backfill...
    assert obs.source_claimed_at == datetime(2026, 9, 19, 12, 0, tzinfo=UTC)
    assert len(obs.evidence_hashes) == 1  # screenshots off by default for backfill


def test_model_version_registered_once(tmp_path: Path) -> None:
    client = make_client([raw_item("uuid-1")])
    run_poll(str(tmp_path), client, now=NOW)
    run_poll(str(tmp_path), client, now=NOW + timedelta(hours=7))
    versions = DataStore(tmp_path).read_jsonl("model_versions.jsonl")
    assert len(versions) == 1
    assert versions[0]["version"] == config.POLLER_VERSION


def test_redact_png_valid() -> None:
    data, note = redact_png(PNG)
    assert data == PNG
    assert note is None


def test_redact_png_rejects_non_png() -> None:
    with pytest.raises(ValueError, match="not a PNG"):
        redact_png(b"definitely not png")


def test_should_poll_unit() -> None:
    assert should_poll(None, NOW, 6.0)
    assert should_poll(NOW - timedelta(hours=7), NOW, 6.0)
    assert should_poll(NOW - timedelta(hours=6), NOW, 6.0)  # boundary counts
    assert not should_poll(NOW - timedelta(hours=5, minutes=59), NOW, 6.0)


def test_last_successful_poll_ignores_skips_and_errors(tmp_path: Path) -> None:
    store = DataStore(tmp_path)
    run_poll(str(tmp_path), make_client([raw_item("uuid-1")], api_500=True), now=NOW)
    assert last_successful_poll_at(store) is None
    run_poll(str(tmp_path), make_client([raw_item("uuid-1")]), now=NOW, force=True)
    assert last_successful_poll_at(store) == NOW
