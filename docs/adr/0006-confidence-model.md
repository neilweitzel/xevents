# ADR 0006: Explainable, independence-aware confidence model

- Status: accepted (2026-09-21, user redline on PR #8)
- Date: 2026-09-18
- Deciders: project lead

## Context

Nothing in the landscape assembles a per-record, machine-readable
"evidence → conclusion" explanation (landscape §3.2d). The fragments —
STIX confidence scores + `created_by` (OpenCTI), taxonomies/sightings/decay
(MISP), investigative prose (DataBreaches.net — strongest human-readable
provenance, but unstructured), VCDB's "Encoded by AI + skill version" tagging —
never combine into a queryable rationale for *why this incident record says
what it says*.

The xfeeds precedent is direct: score corroboration by **independence class**,
not raw source count. In xevents' domain this matters more, because ransomware
claims are routinely echoed: the same attacker listing re-aggregated across
trackers looks like three independent rows but is one claim with three
mirrors. Counting it three times manufactures confidence out of repetition.

A related trap: compromise-to-disclosure lag is a headline analytic goal, but
no open, incident-level dataset links per-incident compromise date to
disclosure date (landscape §5.1, §5.5). Every published lag figure is an
aggregate over a private vendor caseload. EDGAR's 4-day clock runs from the
unobservable internal materiality determination, so lag cannot be computed
from EDGAR alone.

## Decision

1. **Confidence is a band with a rationale, not a bare number.**
   Bands (DECIDED open-decisions.md #1, 2026-09-20):
   `unverified` / `low` / `moderate` / `high` / `disputed`.
   (Avoids the xfeeds-era ambiguity between band labels and numeric scores:
   the band *is* the output; the rationale is the explanation.) Model
   weights are internal inputs; they are never published and never shown
   to consumers.
2. **Independence classes (initial set):**
   `tor_primary` (own crawler captures), `aggregator_ransomlook`,
   `aggregator_ransomfeed`, `regulatory_filing` (EDGAR / AG / HHS OCR),
   `company_statement`, `breach_catalog` (HIBP), `analyst_journalism`
   (DataBreaches.net and equivalents), `vuln_feed` (KEV).
   Classes are versioned; adding one is a model change, recorded in the
   `model_version` registry. **MVP note:** with a single source, the active
   class set is `aggregator_ransomlook` alone — most incidents will honestly
   assess `unverified`/`low`. Enrichment observations do not contribute a
   class; they feed entity-resolution confidence, which caps the incident
   band (item 4).
3. **Weight counts once per independence class.** Echoed claims collapse to a
   single vote. Two aggregators mirroring the same leak-site listing
   contribute one class of evidence, not two.
4. **Inputs to an assessment:**
   - supporting observations, weighted by source tier and class;
   - refuting/correction events (ADR 0004), which reduce or revise confidence;
   - removal observations (ADR 0007): ambiguous signal — may indicate payment,
     false claim, or takedown — flagged in the rationale, never an automatic
     negative;
   - entity-resolution confidence from ADR 0005 (a shaky entity match caps
     the incident band).
5. **Every assessment records:** model version, inputs hash (what went in),
   contributing independence classes, supporting vs refuting weight, and a
   human-readable rationale. Assessments are **superseded, never edited**.
6. **Lag is an analytic output, not a confidence input.** Record compromise,
   listing, notification, and disclosure dates as separate observations with
   their own provenance; compute compromise-to-disclosure lag only where both
   endpoints are evidenced, and label the rest as unknown rather than
   imputing.

## Consequences

- Initial class weights and tier rankings are judgment calls. They are
  documented in the model version record and revisited empirically as the
  correction ledger accumulates ground truth (retractions are the training
  signal).
- Explainability is structural: any consumer can query an incident's
  assessment and see exactly which observations, classes, and corrections
  produced the band.
- Assessments must be re-run when new observations or corrections land on an
  incident; the superseded chain is the audit trail.
- **Reassessment mechanism (MVP).** The incident-resolution pipeline run is
  the trigger: every pipeline run that adds observations, memberships, or
  correction events to an incident emits a new assessment that supersedes
  the prior one (new row, `superseded_by` linked). No separate scheduler in
  MVP — assessment freshness follows pipeline activity. Dispute-driven
  reassessment is manual via the review queue (ADR 0005 item 4).

## Research basis

- Landscape §3.2(d) (explainable-confidence gap).
- Landscape §5.1, §5.5 (compromise-to-disclosure lag: no open incident-level
  dataset; all figures are vendor aggregates over private caseloads).
- Landscape §1.8.2 (ransomware.live `attackdate` frequently empty;
  `discovered` = listing-seen date, not intrusion date).
- Landscape §2.1 (EDGAR: 4-day clock from unobservable materiality
  determination).
- xfeeds project precedent: independence-class corroboration scoring.

## Pivot note, 2026-09-21 (user decisions #8–#11)

The band model is unchanged (`unverified` / `low` / `moderate` / `high` /
`disputed`; one independence class caps at `low`; no percentages). Additions:

- **Victim-acknowledged status** is a separate axis alongside the band
  (open-decisions.md #9, amended binary 2026-09-21): `acknowledged` /
  `unacknowledged` — unacknowledged until a cited victim disclosure
  confirms the incident; no intermediate states.
- **What the bands describe:** internal incidents (private). The public
  aggregates publish the *breakdown* (counts per band), never a
  per-incident band that could function as a pseudonymous pointer.
- Assessments are still superseded, never edited; weights stay internal.
- The honest single-source behavior (§4 above) is unchanged — and is now
  also visible to readers as aggregate-level band distributions.

Status: accepted (2026-09-21, user redline on PR #8).
