# ADR 0001: Immutable observations, cautiously-resolved incident records

- Status: proposed (pending user redline)
- Date: 2026-09-18
- Deciders: project lead

## Context

Public claims about incidents arrive as single-source assertions: a ransomware
group lists a victim on a leak site; a company files an 8-K; a state AG publishes
a notice; a journalist writes it up. These claims conflict (Clop listed "Thames
Water" when the victim was South Staffs Water), get quietly removed when victims
pay, and are sometimes outright hoaxes (fabricated VRChat/Discord filings took
Maine's AG register offline in June 2026). No existing tool maintains
claim-level provenance with a correction history — MISP tracks indicator
correlation, not incident claims; VCDB's analyst encoding is the closest
conceptual match but is manual and tracks analyst work, not source-claim
retraction (landscape §3.2).

The xfeeds precedent applies: do not treat copied feeds as independent votes.
Here: do not treat echoed or repeated claims as established fact.

## Decision

Two layers, with a hard boundary between them:

1. **Observation layer (immutable, append-only).** One record per
   (source, claim, observation-time). An observation stores the source, the
   timestamp, the entity details as the source gave them, the raw payload, the
   evidence artifacts captured at ingest, and a pipeline version. Once written,
   an observation is never edited. If it was wrong, a correction event is
   appended (ADR 0004).
2. **Incident layer (mutable, resolved, explainable).** An incident record
   groups related observations about the same real-world event. Membership is
   explicit via typed links: `supports`, `duplicates`, `refutes`, `corrects`.
   Every incident carries a versioned confidence assessment (ADR 0006) and a
   resolution rationale naming the observations and model version that produced
   it. Incident IDs are stable across re-resolution.

Resolution — assigning observations to incidents — is itself recorded: what was
grouped, by which model/pipeline version, and why. Re-resolution creates a new
recorded state; it never rewrites the old one silently.

**Idempotency.** One observation per (source, item, first-seen). Re-polling a
source must not duplicate observations: each item carries a stable
`source_item_key`, and poll state lives in `listing_state` (data-model.md).
A re-observed item updates last-seen; only a genuinely new item, a changed
claim, or a removal creates a new observation.

## Consequences

- Storage grows monotonically. A retention policy is required (ADR 0003), and
  it must preserve the audit trail, not just current state.
- All derived analytics must tolerate incident records changing status
  (`candidate` → `active` → `contested` → `retracted`) over time. Trend queries
  must be reproducible as-of a timestamp.
- Rejected alternative: a single mutable incident table with source fields.
  It destroys provenance, makes corrections invisible, and conflates "what was
  claimed" with "what we believe" — the exact failure mode this project exists
  to avoid.

## Research basis

- Landscape §3.2: gaps (a)–(d) — no tool does evidence preservation,
  correction history, claim reconciliation, or explainable confidence well.
- Landscape §6.3: documented misidentification (Clop/Thames Water vs South
  Staffs Water) and industry claim-framing practice (GalaxyWarden,
  ransomware.live T&C §7).
- Landscape §3.1: VCDB analyst-encoding pipeline as closest conceptual match
  (manual; tracks analyst encoding, not source-claim retraction).
