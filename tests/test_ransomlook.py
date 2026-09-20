"""Tests for the RansomLook client: parsing, filtering, HTTP behavior."""

from __future__ import annotations

from datetime import UTC, date

import httpx
import pytest

from xevents.ransomlook import (
    RansomLookError,
    fetch_last,
    fetch_period,
    fetch_recent,
    is_noise,
    parse_item,
)


def sample_raw(**overrides: object) -> dict[str, object]:
    raw: dict[str, object] = {
        "post_title": "ACME CORP",
        "group_name": "lockbit",
        "discovered": "2026-09-20 17:44:25.273479",
        "description": "Acme Corp description",
        "link": "/post/acme-corp-xyz",
        "magnet": "None",
        "screen": "screenshots/acme.png",
        "private": "False",
        "misp_uuid": "12345678-1234-1234-1234-123456789abc",
    }
    raw.update(overrides)
    return raw


def mock_client(handler: object) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))  # type: ignore[arg-type]


def test_parse_all_fields() -> None:
    item = parse_item(sample_raw())
    assert item.misp_uuid == "12345678-1234-1234-1234-123456789abc"
    assert item.post_title == "ACME CORP"
    assert item.group_name == "lockbit"
    assert item.description == "Acme Corp description"
    assert item.magnet is None
    assert not item.private


def test_parse_discovered_naive_assumed_utc() -> None:
    item = parse_item(sample_raw())
    assert item.discovered_utc.tzinfo == UTC
    assert item.discovered_utc.isoformat() == "2026-09-20T17:44:25.273479+00:00"


def test_parse_discovered_with_offset_kept() -> None:
    item = parse_item(sample_raw(discovered="2026-09-20T17:44:25+02:00"))
    assert item.discovered_utc.isoformat() == "2026-09-20T17:44:25+02:00"


def test_parse_discovered_invalid_raises() -> None:
    with pytest.raises(ValueError, match="discovered"):
        parse_item(sample_raw(discovered="not-a-date"))


@pytest.mark.parametrize("field", ["post_title", "group_name", "misp_uuid"])
def test_parse_blank_identity_field_raises(field: str) -> None:
    with pytest.raises(ValueError, match=field):
        parse_item(sample_raw(**{field: "   "}))


def test_parse_missing_field_names_it() -> None:
    raw = sample_raw()
    del raw["misp_uuid"]
    with pytest.raises(ValueError, match="misp_uuid"):
        parse_item(raw)


def test_parse_non_string_field_raises() -> None:
    with pytest.raises(TypeError, match="post_title"):
        parse_item(sample_raw(post_title=123))


@pytest.mark.parametrize("raw_flag, expected", [("True", True), ("False", False)])
def test_parse_private_string_flags(raw_flag: str, expected: bool) -> None:
    assert parse_item(sample_raw(private=raw_flag)).private is expected


def test_parse_private_garbage_raises() -> None:
    with pytest.raises(ValueError, match="private"):
        parse_item(sample_raw(private="maybe"))


def test_parse_real_magnet_preserved() -> None:
    item = parse_item(sample_raw(magnet="magnet:?xt=urn:btih:abc123"))
    assert item.magnet == "magnet:?xt=urn:btih:abc123"


def test_parse_relative_urls_joined() -> None:
    item = parse_item(sample_raw())
    assert item.link_url == "https://www.ransomlook.io/post/acme-corp-xyz"
    assert item.screen_url == "https://www.ransomlook.io/screenshots/acme.png"


def test_parse_absolute_urls_kept() -> None:
    item = parse_item(sample_raw(link="https://example.com/x", screen="https://example.com/y.png"))
    assert item.link_url == "https://example.com/x"
    assert item.screen_url == "https://example.com/y.png"


def test_is_noise_audit_team() -> None:
    assert is_noise(parse_item(sample_raw(group_name="audit team")))
    assert is_noise(parse_item(sample_raw(group_name="Audit Team")))


def test_is_noise_private() -> None:
    assert is_noise(parse_item(sample_raw(private="True")))


def test_is_not_noise_normal() -> None:
    assert not is_noise(parse_item(sample_raw()))


def _json_response(payload: object, status: int = 200) -> httpx.Response:
    return httpx.Response(status, json=payload)


def test_fetch_recent_hits_endpoint() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return _json_response([sample_raw()])

    items = fetch_recent(mock_client(handler), 5)
    assert seen == ["https://www.ransomlook.io/api/recent/5"]
    assert len(items) == 1


def test_fetch_last_hits_endpoint() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return _json_response([])

    assert fetch_last(mock_client(handler), 2) == []
    assert seen == ["https://www.ransomlook.io/api/last/2"]


def test_fetch_period_formats_dates() -> None:
    seen: list[str] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(str(request.url))
        return _json_response([])

    fetch_period(mock_client(handler), date(2026, 1, 1), date(2026, 1, 31))
    assert seen == ["https://www.ransomlook.io/api/posts/period/2026-01-01/2026-01-31"]


def test_fetch_empty_list_ok() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response([])

    assert fetch_recent(mock_client(handler), 3) == []


def test_fetch_http_error_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(500, text="boom")

    with pytest.raises(RansomLookError, match="recent/3"):
        fetch_recent(mock_client(handler), 3)


def test_fetch_invalid_json_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text="not json")

    with pytest.raises(RansomLookError, match="invalid JSON"):
        fetch_recent(mock_client(handler), 3)


def test_fetch_non_list_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response({"items": []})

    with pytest.raises(RansomLookError, match="expected list"):
        fetch_recent(mock_client(handler), 3)


def test_fetch_non_object_entry_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return _json_response(["nope"])

    with pytest.raises(RansomLookError, match="non-object"):
        fetch_recent(mock_client(handler), 3)


def test_fetch_network_failure_raises() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route")

    with pytest.raises(RansomLookError):
        fetch_recent(mock_client(handler), 3)
