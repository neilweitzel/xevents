"""Static site generator: renders data/ into site/ for GitHub Pages
(ADR 0009). No JavaScript framework — plain HTML generated per run."""

from __future__ import annotations

import html
import json
from pathlib import Path

from xevents import config
from xevents.models import Observation, PollRun
from xevents.storage import DataStore


def _load_observations(store: DataStore) -> list[Observation]:
    observations: list[Observation] = []
    for record in store.read_jsonl("observations.jsonl"):
        observations.append(Observation.from_dict(record))
    observations.sort(key=lambda o: o.observed_at, reverse=True)
    return observations


def _load_runs(store: DataStore) -> list[PollRun]:
    runs: list[PollRun] = []
    for record in store.read_jsonl("poll_runs.jsonl"):
        runs.append(PollRun.from_dict(record))
    runs.sort(key=lambda r: r.started_at, reverse=True)
    return runs


def render_site(root_path: str) -> Path:
    """Regenerate site/ from data/. Returns the site directory."""
    root = Path(root_path)
    store = DataStore(root)
    site_dir = root / "site"
    data_out = site_dir / "data"
    data_out.mkdir(parents=True, exist_ok=True)

    observations = _load_observations(store)
    runs = _load_runs(store)
    last_run = runs[0] if runs else None

    # JSON snapshots: the export contract (docs/data-model.md) is the
    # published data format — the site is rendered from it.
    obs_payload = [o.to_dict() for o in observations]
    (data_out / "observations.json").write_text(
        json.dumps(obs_payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    (data_out / "poll_runs.json").write_text(
        json.dumps([r.to_dict() for r in runs], ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    rows = []
    for obs in observations[:500]:
        claimed = obs.source_claimed_at.isoformat() if obs.source_claimed_at else "unknown"
        rows.append(
            "<tr>"
            f"<td>{html.escape(obs.subject_raw)}</td>"
            f"<td>{html.escape(claimed)}</td>"
            f"<td>{html.escape(obs.observed_at.isoformat())}</td>"
            f"<td>{len(obs.evidence_hashes)}</td>"
            "</tr>"
        )
    table_body = "\n".join(rows) if rows else ('<tr><td colspan="4">No observations yet.</td></tr>')

    last_poll = last_run.started_at.isoformat() if last_run else "never"
    page = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>xevents — evidence-first incident intelligence</title>
<style>
body {{ font-family: system-ui, sans-serif; max-width: 72rem; margin: 2rem auto;
       padding: 0 1rem; color: #1a1a1a; }}
table {{ border-collapse: collapse; width: 100%; }}
th, td {{ border: 1px solid #ccc; padding: 0.4rem 0.6rem; text-align: left; }}
th {{ background: #f4f4f4; }}
.notice {{ background: #fff8e1; border: 1px solid #e6c200; padding: 1rem; }}
footer {{ margin-top: 2rem; font-size: 0.85rem; color: #555; }}
</style>
</head>
<body>
<h1>xevents</h1>
<p>Evidence-first incident intelligence. Every entry below is a preserved
claim from a public source — not an assertion that a breach occurred.</p>

<div class="notice">
<strong>Coverage boundary.</strong> {html.escape(config.COVERAGE_STATEMENT)}
</div>

<h2>Status</h2>
<ul>
<li>Observations: {len(observations)}</li>
<li>Poll runs: {len(runs)}</li>
<li>Last poll: {html.escape(last_poll)}</li>
</ul>

<h2>Recent observations</h2>
<table>
<thead><tr><th>Victim (as claimed)</th><th>Source claimed at</th>
<th>Observed at</th><th>Evidence artifacts</th></tr></thead>
<tbody>
{table_body}
</tbody>
</table>
<p>Machine-readable: <a href="data/observations.json">observations.json</a>,
<a href="data/poll_runs.json">poll_runs.json</a></p>

<footer>{html.escape(config.ATTRIBUTION_TEXT)}</footer>
</body>
</html>
"""
    (site_dir / "index.html").write_text(page, encoding="utf-8")
    return site_dir
