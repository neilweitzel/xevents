"""Pipeline-wide constants. Tunables that are user decisions live in
docs/open-decisions.md; the values here are the current defaults."""

from __future__ import annotations

# MVP source (ADR 0002, docs/source-spec-ransomlook.md).
SOURCE_NAME = "ransomlook_api"
API_BASE = "https://www.ransomlook.io/api"
REQUEST_TIMEOUT_SECONDS = 30.0

# Versioned component identifiers, registered in data/model_versions.jsonl
# (docs/data-model.md: model_version registry).
POLLER_VERSION = "ingest-ransomlook/v0.1.0"
RESOLUTION_MODEL_VERSION = "incident-resolution/v0.1.0"

# Attribution rendered wherever CC BY 4.0-derived content appears (ADR 0002).
ATTRIBUTION_TEXT = (
    "Victim listing data by RansomLook (https://www.ransomlook.io), licensed CC BY 4.0."
)

# Scheduler: cron fires this often; the guard holds the *effective* poll
# cadence. GitHub's scheduler drops slots, so the cron is more frequent than
# the guard (xfeeds pattern). The guard value is open-decisions.md #5;
# 6 hours is the decision-brief recommendation until the user rules.
CRON_INTERVAL_HOURS = 2.0
GUARD_INTERVAL_HOURS = 6.0

# Steady-state poll window: wide enough to survive a dropped slot or two.
POLL_WINDOW_DAYS = 2

# Non-victim entries the poller filters at ingest
# (docs/source-spec-ransomlook.md).
AUDIT_GROUP_NAMES = frozenset({"audit team"})

# Split trigger for the evidence store (docs/evidence-storage.md).
EVIDENCE_SPLIT_TRIGGER_BYTES = 2 * 1024 * 1024 * 1024

# Published coverage-boundary statement (data-model.md). Shown on the site.
COVERAGE_STATEMENT = (
    "xevents currently ingests one source: the RansomLook API "
    "(ransomlook.io, CC BY 4.0), polled on a schedule. RansomLook sees only "
    "what its scrapers reach: data-leak-site churn and Tor volatility mean "
    "silent coverage gaps. It carries no country or sector fields. "
    "Operational notices and private entries are filtered at ingest. "
    "Every observation below preserves what the source claimed and when we "
    "saw it; nothing here asserts a breach occurred."
)
