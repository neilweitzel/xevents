"""xevents CLI: poll, backfill, render-site."""

from __future__ import annotations

from datetime import date
from pathlib import Path

import httpx
import typer

from xevents import config
from xevents.pipeline import run_backfill, run_poll
from xevents.site import render_site

app = typer.Typer(help="xevents pipeline: ingest RansomLook, render the static site.")


def _root() -> str:
    return str(Path.cwd())


@app.command()
def poll(
    force: bool = typer.Option(False, help="Bypass the cadence guard."),
    days: int = typer.Option(config.POLL_WINDOW_DAYS, help="Poll window in days."),
    screenshots: bool = typer.Option(True, help="Fetch source screenshots as evidence."),
) -> None:
    """Run one scheduled poll cycle."""
    with httpx.Client() as client:
        run = run_poll(
            _root(), client, force=force, window_days=days, fetch_screenshots=screenshots
        )
    typer.echo(
        f"poll {run.status}: seen={run.items_seen} new={run.items_new} "
        f"filtered={run.items_filtered} errored={run.items_errored}"
    )
    if run.status == "error":
        raise typer.Exit(code=1)


@app.command()
def backfill(
    start: str = typer.Option(..., help="Start date YYYY-MM-DD."),
    end: str = typer.Option(..., help="End date YYYY-MM-DD."),
    screenshots: bool = typer.Option(False, help="Fetch historical screenshots (slow)."),
) -> None:
    """First-run historical ingest over a bounded window."""
    start_date = date.fromisoformat(start)
    end_date = date.fromisoformat(end)
    with httpx.Client() as client:
        run = run_backfill(_root(), client, start_date, end_date, fetch_screenshots=screenshots)
    typer.echo(
        f"backfill {run.status}: seen={run.items_seen} new={run.items_new} "
        f"filtered={run.items_filtered} errored={run.items_errored}"
    )
    if run.status == "error":
        raise typer.Exit(code=1)


@app.command(name="render-site")
def render_site_cmd() -> None:
    """Regenerate site/ from data/."""
    site_dir = render_site(_root())
    typer.echo(f"site rendered to {site_dir}")
