"""Tests for the static site generator."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path

import httpx

from xevents import config
from xevents.pipeline import run_poll
from xevents.site import render_site

NOW = datetime(2026, 9, 20, 18, 0, 0, tzinfo=UTC)


def raw_item(uuid: str, title: str) -> dict[str, object]:
    return {
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


def seed(tmp_path: Path) -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.startswith("/api/"):
            return httpx.Response(200, json=[raw_item("uuid-1", "ACME <CORP>")])
        return httpx.Response(200, content=b"\x89PNG\r\n\x1a\n" + b"\x00")

    from xevents.site import render_site as _render

    run_poll(
        str(tmp_path),
        httpx.Client(transport=httpx.MockTransport(handler)),
        now=NOW,
    )
    _render(str(tmp_path))


def test_renders_empty_state(tmp_path: Path) -> None:
    site_dir = render_site(str(tmp_path))
    page = (site_dir / "index.html").read_text(encoding="utf-8")
    assert "Observations: 0" in page
    assert "No observations yet." in page
    assert (site_dir / "data" / "observations.json").exists()


def test_renders_observations_escaped(tmp_path: Path) -> None:
    seed(tmp_path)
    page = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    assert "ACME &lt;CORP&gt;" in page  # HTML-escaped
    assert "ACME <CORP>" not in page
    assert "Observations: 1" in page


def test_attribution_and_coverage_present(tmp_path: Path) -> None:
    seed(tmp_path)
    page = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    assert "RansomLook" in page
    assert "CC BY 4.0" in page
    assert "Coverage boundary" in page
    assert "not an assertion that a breach occurred" in page


def test_json_snapshots_match_data(tmp_path: Path) -> None:
    import json

    seed(tmp_path)
    observations = json.loads((tmp_path / "site" / "data" / "observations.json").read_text())
    assert len(observations) == 1
    assert observations[0]["subject_raw"] == "ACME <CORP>"
    runs = json.loads((tmp_path / "site" / "data" / "poll_runs.json").read_text())
    assert len(runs) == 1
    assert runs[0]["status"] == "ok"


def test_site_mentions_config_attribution(tmp_path: Path) -> None:
    render_site(str(tmp_path))
    page = (tmp_path / "site" / "index.html").read_text(encoding="utf-8")
    assert config.ATTRIBUTION_TEXT.split(",")[0] in page
