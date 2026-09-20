"""RansomLook API client (docs/source-spec-ransomlook.md).

All network I/O goes through an injected httpx.Client so tests can use a
mock transport. Field semantics were verified live 2026-09-20.
"""

from __future__ import annotations

from datetime import UTC, date, datetime

import httpx

from xevents import config
from xevents.models import SourceItem

# Fields every item must carry (verified against the live API).
_REQUIRED_FIELDS = (
    "post_title",
    "group_name",
    "discovered",
    "description",
    "link",
    "magnet",
    "screen",
    "private",
    "misp_uuid",
)


class RansomLookError(RuntimeError):
    """The API call failed or the response was not usable."""


def _fetch(client: httpx.Client, path: str) -> list[dict[str, object]]:
    url = f"{config.API_BASE}{path}"
    try:
        response = client.get(url, timeout=config.REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
    except httpx.HTTPError as exc:
        raise RansomLookError(f"GET {url} failed: {exc}") from exc
    try:
        payload: object = response.json()
    except ValueError as exc:
        raise RansomLookError(f"GET {url} returned invalid JSON") from exc
    if not isinstance(payload, list):
        raise RansomLookError(f"GET {url} returned {type(payload).__name__}, expected list")
    items: list[dict[str, object]] = []
    for entry in payload:
        if not isinstance(entry, dict):
            raise RansomLookError(f"GET {url} returned a non-object list entry")
        items.append(entry)
    return items


def fetch_recent(client: httpx.Client, n: int) -> list[dict[str, object]]:
    """Latest n posts."""
    return _fetch(client, f"/recent/{n}")


def fetch_last(client: httpx.Client, days: int) -> list[dict[str, object]]:
    """Posts from the last N days."""
    return _fetch(client, f"/last/{days}")


def fetch_period(client: httpx.Client, start: date, end: date) -> list[dict[str, object]]:
    """Posts in a bounded window (backfill). Dates are YYYY-MM-DD."""
    return _fetch(client, f"/posts/period/{start.isoformat()}/{end.isoformat()}")


def _parse_bool_flag(raw: object, field: str) -> bool:
    # The API returns the string "True"/"False", not JSON booleans.
    if isinstance(raw, bool):
        return raw
    if isinstance(raw, str):
        lowered = raw.strip().lower()
        if lowered == "true":
            return True
        if lowered == "false":
            return False
    raise ValueError(f"field {field!r} must be a boolean or 'True'/'False' string")


def parse_item(raw: dict[str, object]) -> SourceItem:
    """Parse one raw API record into a SourceItem. Raises ValueError naming
    the offending field; raises for blank identity fields."""
    for field_name in _REQUIRED_FIELDS:
        if field_name not in raw:
            raise ValueError(f"missing required field {field_name!r}")

    def req(key: str) -> str:
        value = raw[key]
        if not isinstance(value, str):
            raise TypeError(f"field {key!r} must be a string")
        return value

    misp_uuid = req("misp_uuid")
    if not misp_uuid.strip():
        raise ValueError("field 'misp_uuid' must not be blank")
    post_title = req("post_title")
    if not post_title.strip():
        raise ValueError("field 'post_title' must not be blank")
    group_name = req("group_name")
    if not group_name.strip():
        raise ValueError("field 'group_name' must not be blank")

    # `discovered` is UTC with no timezone marker (source convention).
    discovered_raw = req("discovered")
    try:
        discovered = datetime.fromisoformat(discovered_raw)
    except ValueError as exc:
        raise ValueError(f"field 'discovered' is not a valid datetime: {discovered_raw!r}") from exc
    if discovered.tzinfo is None:
        discovered = discovered.replace(tzinfo=UTC)

    magnet_raw = req("magnet")
    magnet = None if magnet_raw.strip().lower() == "none" else magnet_raw

    link = req("link")
    screen = req("screen")
    return SourceItem(
        misp_uuid=misp_uuid,
        post_title=post_title,
        group_name=group_name,
        discovered_utc=discovered,
        description=req("description"),
        link_url=link if link.startswith("http") else f"https://www.ransomlook.io{link}",
        magnet=magnet,
        screen_url=screen if screen.startswith("http") else f"https://www.ransomlook.io/{screen}",
        private=_parse_bool_flag(raw["private"], "private"),
    )


def is_noise(item: SourceItem) -> bool:
    """True for entries that are not victim listings: operational notices
    (e.g. group_name 'audit team') and private-flagged items."""
    return item.group_name.strip().lower() in config.AUDIT_GROUP_NAMES or item.private
