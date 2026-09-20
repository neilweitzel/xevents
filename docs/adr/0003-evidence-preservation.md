# ADR 0003: Capture-at-ingest evidence preservation

- Status: proposed (pending user redline)
- Date: 2026-09-18
- Deciders: project lead

## Context

Leak sites die. Groups rebrand, get seized (LockBit/Cronos, Feb 2024), or
exit-scam (ALPHV/BlackCat, Mar 2024); aggregators go stale (ransomwatch froze
June 2025). If xevents only stores links to source pages, its evidence rots —
and the whole "evidence-first" claim collapses. The landscape survey found **no
existing tool that archives claim-level proof as a first-class record**
(§3.2a, §7.4): RansomLook retains per-post screenshots/HTML, MISP can attach
files only if the operator configures it, and everyone else links out and lets
the Wayback Machine do the actual preservation without integrating archiving
into the data model.

The demonstrated standard in the wild is the timestamped screenshot — every
ransomware.live entry carries an archived "Leak Screenshot." WARC is the
established web-archive format, but no public source confirms major DLS
trackers use it (UNVERIFIED).

Separately, preservation must not become redistribution of stolen data: the
observed safe posture (ransomware.live, GalaxyWarden) is to index only publicly
visible listing metadata and screenshots — no acquisition, hosting, or
redistribution of stolen content or personal data.

## Decision

1. **Capture at ingest, every observation.** Minimum per observation:
   timestamped screenshot + raw HTML/metadata of the source as seen. WARC
   capture as an enhancement where feasible, not a requirement.
   **API-source adaptation:** where the source is a JSON API (RansomLook in
   the MVP), the raw API response body plus fetch metadata *is* what the
   source showed — it satisfies the minimum alongside the source-provided
   screenshot (`screen` field, fetched and archived). No synthetic screenshot
   of our own rendering is required; screenshots remain mandatory where the
   source itself is an HTML page.
2. **Content-addressed storage.** Evidence artifacts are stored keyed by
   SHA-256; the hash is recorded on the observation, so any consumer can verify
   the artifact matches what was captured.
3. **Redact before storage.** No stolen content, no personal data. Names,
   emails, phone numbers, and other personal data visible in screenshots or
   HTML are redacted or excluded before the artifact is stored. Index metadata,
   not payloads. **Pre-public-surface gate:** a written lawful-basis /
   public-interest research justification (GDPR posture per landscape §6.3),
   with pseudonymization and minimization applied throughout, must exist and
   be reviewed before the operational surface serves data publicly. No memo,
   no public surface.
4. **Retention preserves the audit trail.** Evidence for retracted or false
   claims is retained alongside its correction events — silent deletion would
   destroy exactly the history the correction ledger exists to keep. The
   retention policy is a documented, public artifact.
5. **ToS-constrained sources.** If a source's terms forbid archival copying, do
   not archive it. Record the ToS constraint itself as an observation and fall
   back to linking with a fetched-at timestamp.

## Consequences

- Storage grows with screenshot volume; the retention policy must be real
  (tiering, lifecycle) rather than aspirational.
- A redaction step sits between capture and storage — it is part of the
  pipeline, versioned like everything else, and its failures are a data-quality
  issue, not a silent skip.
- Evidence artifacts are immutable: a re-capture is a new artifact linked to
  a new observation, never an overwrite.

## Research basis

- Landscape §3.2(a) (evidence-preservation gap), §7.4 ("no off-the-shelf
  solution").
- Landscape §6.1 (evidence archiving: screenshot standard; WARC UNVERIFIED;
  ransomware.live "Duplicate Entry" dedup handling).
- Landscape §6.3 (GDPR posture; ransomware.live/GalaxyWarden
  metadata-and-screenshots-only model; no known lawsuits against trackers —
  UNVERIFIED, absence of search results, not proof).
