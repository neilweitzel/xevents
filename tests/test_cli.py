"""Tests for CLI wiring and pipeline tunables."""

from __future__ import annotations

from typer.testing import CliRunner

from xevents import config
from xevents.cli import app

runner = CliRunner()


def test_cli_help_lists_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    assert "poll" in result.output
    assert "backfill" in result.output
    assert "render-site" in result.output


def test_render_site_command(tmp_path: object) -> None:
    import os
    from pathlib import Path

    root = Path(str(tmp_path))
    old = os.getcwd()
    os.chdir(root)
    try:
        result = runner.invoke(app, ["render-site"])
    finally:
        os.chdir(old)
    assert result.exit_code == 0
    assert (root / "site" / "index.html").exists()


def test_tunable_defaults_are_documented() -> None:
    # Guard rails the cron; the cron fires more often (dropped-slot pattern).
    assert config.CRON_INTERVAL_HOURS < config.GUARD_INTERVAL_HOURS
    assert config.GUARD_INTERVAL_HOURS == 6.0
    assert config.POLL_WINDOW_DAYS >= 2
    assert config.EVIDENCE_SPLIT_TRIGGER_BYTES == 2 * 1024 * 1024 * 1024
    assert "audit team" in config.AUDIT_GROUP_NAMES
