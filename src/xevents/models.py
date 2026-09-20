"""Core data model: frozen dataclasses implementing the logical schema
(docs/data-model.md). Observations are immutable; corrections append."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime


def _require_str(payload: dict[str, object], key: str) -> str:
    value = payload.get(key)
    if not isinstance(value, str):
        raise TypeError(f"field {key!r} must be a string")
    return value


def _require_optional_str(payload: dict[str, object], key: str) -> str | None:
    value = payload.get(key)
    if value is None:
        return None
    if not isinstance(value, str):
        raise TypeError(f"field {key!r} must be a string or null")
    return value


def _require_datetime(payload: dict[str, object], key: str) -> datetime:
    raw = _require_str(payload, key)
    return datetime.fromisoformat(raw)


def _require_optional_datetime(payload: dict[str, object], key: str) -> datetime | None:
    raw = _require_optional_str(payload, key)
    return datetime.fromisoformat(raw) if raw is not None else None


def _require_int(payload: dict[str, object], key: str) -> int:
    value = payload.get(key)
    if not isinstance(value, int) or isinstance(value, bool):
        raise TypeError(f"field {key!r} must be an integer")
    return value


@dataclass(frozen=True)
class SourceItem:
    """A parsed RansomLook API record (docs/source-spec-ransomlook.md)."""

    misp_uuid: str
    post_title: str
    group_name: str
    discovered_utc: datetime
    description: str
    link_url: str
    magnet: str | None
    screen_url: str
    private: bool

    def to_dict(self) -> dict[str, object]:
        return {
            "misp_uuid": self.misp_uuid,
            "post_title": self.post_title,
            "group_name": self.group_name,
            "discovered_utc": self.discovered_utc.isoformat(),
            "description": self.description,
            "link_url": self.link_url,
            "magnet": self.magnet,
            "screen_url": self.screen_url,
            "private": self.private,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> SourceItem:
        magnet = _require_optional_str(payload, "magnet")
        private = payload.get("private")
        if not isinstance(private, bool):
            raise TypeError("field 'private' must be a boolean")
        return cls(
            misp_uuid=_require_str(payload, "misp_uuid"),
            post_title=_require_str(payload, "post_title"),
            group_name=_require_str(payload, "group_name"),
            discovered_utc=_require_datetime(payload, "discovered_utc"),
            description=_require_str(payload, "description"),
            link_url=_require_str(payload, "link_url"),
            magnet=magnet,
            screen_url=_require_str(payload, "screen_url"),
            private=private,
        )


@dataclass(frozen=True)
class Observation:
    """One source's claim, seen once. Immutable (ADR 0001)."""

    id: str
    source_name: str
    source_item_key: str
    claim_type: str
    subject_raw: str
    observed_at: datetime
    source_claimed_at: datetime | None
    raw_payload: dict[str, object]
    pipeline_version: str
    evidence_hashes: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "source_name": self.source_name,
            "source_item_key": self.source_item_key,
            "claim_type": self.claim_type,
            "subject_raw": self.subject_raw,
            "observed_at": self.observed_at.isoformat(),
            "source_claimed_at": (
                self.source_claimed_at.isoformat() if self.source_claimed_at else None
            ),
            "raw_payload": self.raw_payload,
            "pipeline_version": self.pipeline_version,
            "evidence_hashes": list(self.evidence_hashes),
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> Observation:
        raw_payload = payload.get("raw_payload")
        if not isinstance(raw_payload, dict):
            raise TypeError("field 'raw_payload' must be an object")
        hashes = payload.get("evidence_hashes", [])
        if not isinstance(hashes, list) or not all(isinstance(h, str) for h in hashes):
            raise TypeError("field 'evidence_hashes' must be a list of strings")
        return cls(
            id=_require_str(payload, "id"),
            source_name=_require_str(payload, "source_name"),
            source_item_key=_require_str(payload, "source_item_key"),
            claim_type=_require_str(payload, "claim_type"),
            subject_raw=_require_str(payload, "subject_raw"),
            observed_at=_require_datetime(payload, "observed_at"),
            source_claimed_at=_require_optional_datetime(payload, "source_claimed_at"),
            raw_payload=raw_payload,
            pipeline_version=_require_str(payload, "pipeline_version"),
            evidence_hashes=tuple(hashes),
        )


@dataclass(frozen=True)
class EvidenceArtifact:
    """A stored evidence blob, addressed by SHA-256 (ADR 0003)."""

    sha256: str
    kind: str
    captured_at: datetime
    byte_size: int
    redaction_note: str | None

    def to_dict(self) -> dict[str, object]:
        return {
            "sha256": self.sha256,
            "kind": self.kind,
            "captured_at": self.captured_at.isoformat(),
            "byte_size": self.byte_size,
            "redaction_note": self.redaction_note,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> EvidenceArtifact:
        return cls(
            sha256=_require_str(payload, "sha256"),
            kind=_require_str(payload, "kind"),
            captured_at=_require_datetime(payload, "captured_at"),
            byte_size=_require_int(payload, "byte_size"),
            redaction_note=_require_optional_str(payload, "redaction_note"),
        )


@dataclass(frozen=True)
class PollRun:
    """Run-level audit record for one ingest execution (data-model.md)."""

    id: str
    source_name: str
    started_at: datetime
    finished_at: datetime | None
    status: str
    items_seen: int
    items_new: int
    items_filtered: int
    items_errored: int
    poller_version: str
    error_log: str | None
    evidence_bytes: int

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "source_name": self.source_name,
            "started_at": self.started_at.isoformat(),
            "finished_at": self.finished_at.isoformat() if self.finished_at else None,
            "status": self.status,
            "items_seen": self.items_seen,
            "items_new": self.items_new,
            "items_filtered": self.items_filtered,
            "items_errored": self.items_errored,
            "poller_version": self.poller_version,
            "error_log": self.error_log,
            "evidence_bytes": self.evidence_bytes,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, object]) -> PollRun:
        return cls(
            id=_require_str(payload, "id"),
            source_name=_require_str(payload, "source_name"),
            started_at=_require_datetime(payload, "started_at"),
            finished_at=_require_optional_datetime(payload, "finished_at"),
            status=_require_str(payload, "status"),
            items_seen=_require_int(payload, "items_seen"),
            items_new=_require_int(payload, "items_new"),
            items_filtered=_require_int(payload, "items_filtered"),
            items_errored=_require_int(payload, "items_errored"),
            poller_version=_require_str(payload, "poller_version"),
            error_log=_require_optional_str(payload, "error_log"),
            evidence_bytes=_require_int(payload, "evidence_bytes"),
        )
