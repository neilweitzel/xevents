"""Ingest pipeline: poll RansomLook, write immutable observations +
content-addressed evidence, emit a run manifest. Idempotent (ADR 0001);
the cadence guard implements the xfeeds dropped-slot pattern (ADR 0009)."""

from __future__ import annotations

import json
import uuid
from datetime import UTC, date, datetime, timedelta

import httpx
import structlog

from xevents import config
from xevents.models import EvidenceArtifact, Observation, PollRun
from xevents.ransomlook import (
    RansomLookError,
    fetch_last,
    fetch_period,
    is_noise,
    parse_item,
)
from xevents.storage import DataStore

log = structlog.get_logger()

_PNG_MAGIC = b"\x89PNG\r\n\x1a\n"


def utcnow() -> datetime:
    return datetime.now(UTC)


def should_poll(last_success_at: datetime | None, now: datetime, guard_hours: float) -> bool:
    """True if enough time has passed since the last successful poll.
    The cron fires more often than this; the guard holds the effective
    cadence (open-decisions.md #5)."""
    if last_success_at is None:
        return True
    return now - last_success_at >= timedelta(hours=guard_hours)


def last_successful_poll_at(store: DataStore) -> datetime | None:
    latest: datetime | None = None
    for record in store.read_jsonl("poll_runs.jsonl"):
        try:
            run = PollRun.from_dict(record)
        except (ValueError, TypeError):
            continue
        if (
            run.status == "ok"
            and run.finished_at is not None
            and (latest is None or run.finished_at > latest)
        ):
            latest = run.finished_at
    return latest


def redact_png(data: bytes) -> tuple[bytes, str | None]:
    """Redaction step (ADR 0003), versioned with the pipeline.

    MVP implementation: validates the PNG magic and stores the bytes
    unchanged with a null redaction note. Automated PII detection inside
    screenshots is heuristic-only at this stage — the documented limitation
    is that personal data visible in a leak-site screenshot is caught by the
    human review queue, not by this step. The step exists in the pipeline so
    hardening it later is a version bump, not an architecture change.
    """
    if not data.startswith(_PNG_MAGIC):
        raise ValueError("screenshot is not a PNG (upstream format change?)")
    return data, None


def ensure_model_version(store: DataStore, now: datetime, poller_version: str) -> None:
    """Register the pipeline version if not already registered
    (docs/data-model.md: model_version registry)."""
    for record in store.read_jsonl("model_versions.jsonl"):
        if record.get("version") == poller_version:
            return
    store.append_jsonl(
        "model_versions.jsonl",
        {
            "version": poller_version,
            "component": "ingest_pipeline",
            "params": {
                "source": config.SOURCE_NAME,
                "guard_hours": config.GUARD_INTERVAL_HOURS,
                "window_days": config.POLL_WINDOW_DAYS,
            },
            "decided_at": now.isoformat(),
            "decided_by": "xevents-pipeline",
            "notes": "RansomLook API ingest (ADR 0002, ADR 0009).",
        },
    )


def _store_artifact(
    store: DataStore,
    data: bytes,
    kind: str,
    captured_at: datetime,
    redaction_note: str | None,
) -> EvidenceArtifact:
    digest = store.write_evidence(data)
    artifact = EvidenceArtifact(
        sha256=digest,
        kind=kind,
        captured_at=captured_at,
        byte_size=len(data),
        redaction_note=redaction_note,
    )
    store.append_jsonl("evidence_artifacts.jsonl", artifact.to_dict())
    return artifact


def _ingest_items(
    store: DataStore,
    raw_items: list[dict[str, object]],
    *,
    observed_at: datetime,
    client: httpx.Client,
    fetch_screenshots: bool,
) -> dict[str, int]:
    """Process raw API records. Returns counters. Shared by poll + backfill."""
    counts = {"seen": len(raw_items), "new": 0, "filtered": 0, "errored": 0}
    evidence_bytes = 0
    state = store.load_listing_state()

    for raw in raw_items:
        try:
            item = parse_item(raw)
        except (ValueError, TypeError) as exc:
            counts["errored"] += 1
            log.warning("unparseable item skipped", error=str(exc))
            continue
        if is_noise(item):
            counts["filtered"] += 1
            continue

        key = item.misp_uuid
        entry = state.get(key)
        if entry is not None:
            entry["last_seen_at"] = observed_at.isoformat()
            continue

        artifacts: list[EvidenceArtifact] = []
        # Raw payload artifact: always captured (ADR 0003 minimum).
        payload_bytes = json.dumps(raw, sort_keys=True, ensure_ascii=False).encode("utf-8")
        artifacts.append(_store_artifact(store, payload_bytes, "raw_payload", observed_at, None))
        # Source screenshot artifact (docs/source-spec-ransomlook.md).
        if fetch_screenshots:
            try:
                response = client.get(item.screen_url, timeout=config.REQUEST_TIMEOUT_SECONDS)
                response.raise_for_status()
                redacted, note = redact_png(response.content)
                artifacts.append(_store_artifact(store, redacted, "screenshot", observed_at, note))
            except (httpx.HTTPError, ValueError) as exc:
                counts["errored"] += 1
                log.warning("screenshot fetch failed", uuid=key, error=str(exc))

        observation = Observation(
            id=uuid.uuid4().hex,
            source_name=config.SOURCE_NAME,
            source_item_key=key,
            claim_type="victim_listing",
            subject_raw=item.post_title,
            observed_at=observed_at,
            source_claimed_at=item.discovered_utc,
            raw_payload=raw,
            pipeline_version=config.POLLER_VERSION,
            evidence_hashes=tuple(a.sha256 for a in artifacts),
        )
        store.append_jsonl("observations.jsonl", observation.to_dict())
        state[key] = {
            "last_seen_at": observed_at.isoformat(),
            "observation_id": observation.id,
        }
        counts["new"] += 1
        evidence_bytes += sum(a.byte_size for a in artifacts)

    store.save_listing_state(state)
    counts["evidence_bytes"] = evidence_bytes
    return counts


def _manifest(
    store: DataStore,
    *,
    started_at: datetime,
    finished_at: datetime,
    status: str,
    counts: dict[str, int],
    error_log: str | None,
) -> PollRun:
    run = PollRun(
        id=uuid.uuid4().hex,
        source_name=config.SOURCE_NAME,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        items_seen=counts.get("seen", 0),
        items_new=counts.get("new", 0),
        items_filtered=counts.get("filtered", 0),
        items_errored=counts.get("errored", 0),
        poller_version=config.POLLER_VERSION,
        error_log=error_log,
        evidence_bytes=counts.get("evidence_bytes", 0),
    )
    store.append_jsonl("poll_runs.jsonl", run.to_dict())
    return run


def run_poll(
    root_path: str,
    client: httpx.Client,
    *,
    now: datetime | None = None,
    force: bool = False,
    fetch_screenshots: bool = True,
    window_days: int = config.POLL_WINDOW_DAYS,
    guard_hours: float = config.GUARD_INTERVAL_HOURS,
) -> PollRun:
    """One scheduled poll cycle. Idempotent; guarded; manifest always written."""
    from pathlib import Path

    started_at = now or utcnow()
    # A test-injected clock is frozen: finished_at follows it, so assertions
    # on guard intervals are deterministic. Production (now=None) uses the
    # real clock for both.
    finished_at = started_at if now is not None else utcnow()
    store = DataStore(Path(root_path))
    ensure_model_version(store, started_at, config.POLLER_VERSION)

    if not force and not should_poll(last_successful_poll_at(store), started_at, guard_hours):
        log.info("poll skipped by cadence guard")
        return _manifest(
            store,
            started_at=started_at,
            finished_at=finished_at,
            status="skipped",
            counts={},
            error_log=None,
        )

    try:
        raw_items = fetch_last(client, window_days)
    except RansomLookError as exc:
        log.error("poll fetch failed", error=str(exc))
        return _manifest(
            store,
            started_at=started_at,
            finished_at=finished_at,
            status="error",
            counts={},
            error_log=str(exc),
        )

    counts = _ingest_items(
        store,
        raw_items,
        observed_at=started_at,
        client=client,
        fetch_screenshots=fetch_screenshots,
    )
    status = "partial" if counts["errored"] > 0 else "ok"
    log.info("poll complete", status=status, **counts)
    return _manifest(
        store,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        counts=counts,
        error_log=None,
    )


def run_backfill(
    root_path: str,
    client: httpx.Client,
    start: date,
    end: date,
    *,
    now: datetime | None = None,
    fetch_screenshots: bool = False,
) -> PollRun:
    """First-run historical ingest. Two clocks keep provenance honest:
    observed_at is the backfill time, source_claimed_at is the source's
    `discovered` (docs/source-spec-ransomlook.md)."""
    from pathlib import Path

    started_at = now or utcnow()
    finished_at = started_at if now is not None else utcnow()
    store = DataStore(Path(root_path))
    ensure_model_version(store, started_at, config.POLLER_VERSION)

    try:
        raw_items = fetch_period(client, start, end)
    except RansomLookError as exc:
        log.error("backfill fetch failed", error=str(exc))
        return _manifest(
            store,
            started_at=started_at,
            finished_at=finished_at,
            status="error",
            counts={},
            error_log=str(exc),
        )

    counts = _ingest_items(
        store,
        raw_items,
        observed_at=started_at,
        client=client,
        fetch_screenshots=fetch_screenshots,
    )
    status = "partial" if counts["errored"] > 0 else "ok"
    log.info("backfill complete", status=status, **counts)
    return _manifest(
        store,
        started_at=started_at,
        finished_at=finished_at,
        status=status,
        counts=counts,
        error_log=None,
    )
