# ADR 0004: Corrections, denials, removals, retractions as first-class history

- Status: proposed (pending user redline)
- Date: 2026-09-18
- Deciders: project lead

## Context

False and poisoned claims are not hypothetical — they are the operating
environment:

- Clop listed "Thames Water"; the actual victim was South Staffs Water
  (later corrected).
- In June 2026, fabricated breach filings impersonating VRChat (2.4M claimed
  victims) and Discord (10M claimed) were submitted to Maine's AG register,
  which was taken offline on June 12, 2026. **Hoax injection into public
  registers is a demonstrated, current threat.**
- No surveyed tool maintains a public, queryable retraction ledger
  (landscape §3.2b). The closest fragments — MISP field-level edit history,
  DataBreaches.net informal "Update:" notes, HIBP's `IsFabricated`/`IsRetired`
  flags (no public change log, UNVERIFIED), VCDB's analyst pipeline — all
  track something other than *source-claim retraction*.

Industry practice for managing this risk is claim-framing plus a correction
channel, not verification: GalaxyWarden labels every page "a public listing …
the attacker's claim … we have not independently verified"; ransomware.live's
T&C disclaims confirmation (§7) and provides a formal removal/dispute process
(§9); Undercode News (Sep 2026): "a public ransomware listing … does not by
itself establish … whether the organization was actually compromised."

## Decision

1. **Correction events are first-class, append-only records.** Types:
   `correction`, `denial`, `removal` (a de-listing observed in the wild),
   `retraction`, `dispute_opened`, `dispute_resolved`. Each carries: target
   (observation, incident, entity, or alias), asserted-by, source, timestamps,
   evidence, and a note.
2. **Corrections attach; they never edit.** A correction event links to its
   target and to any superseding information. History is never rewritten —
   consistent with ADR 0001 (observations immutable) and ADR 0006
   (assessments superseded, not edited).
3. **Incident status transitions are explicit.** An incident may move
   `candidate` → `active` → `contested` → `retracted`, each transition carrying
   a rationale and the correction events that caused it.
4. **Claim-framing language is mandatory on the public surface.** Every
   public-facing incident/observation rendering states whose claim it is.
   Never present an attacker's listing as an established breach.
5. **The dispute/correction channel ships from day one**, before the public
   research surface. Published process, documented handling, named contact.
   This is a credibility prerequisite, not a post-launch feature. Handling is
   manual in MVP (docs/mvp-scope.md, non-goal 8). **UNDECIDED
   (open-decisions.md #4):** whether v1 docs state a response-time SLA.

## Consequences

- The correction ledger is itself a public output and a credibility asset —
  a queryable history of what was claimed, what was wrong, and what changed.
- Dispute handling is an operational commitment. Document response
  expectations; a published channel nobody monitors is worse than none.
- The confidence model must consume correction events as negative or
  revising inputs (ADR 0006); removal observations are ambiguous signal
  (payment, false claim, or takedown — ADR 0007), not automatic retractions.

## Research basis

- Landscape §3.2(b) (correction/retraction gap analysis).
- Landscape §6.3 (defamation risk; Clop/Thames Water; GalaxyWarden and
  ransomware.live claim-framing and dispute practices; no known lawsuits
  against trackers — UNVERIFIED).
- Landscape §2.2 (Maine AG offline June 12, 2026 after hoax filings) and §7.5
  (false claims and hoax injection as a load-bearing design driver).

## Pivot note, 2026-09-21 (user decisions #8–#11)

The append-only correction doctrine is unchanged. Two additions:

- **New event type:** `administrative_note` (deletions, retention
  transitions, rollbacks, name-bearing-ref omissions). The ledger stays
  the credibility asset; the public correction-ledger page shows these
  entries alongside corrections.
- **Propagation semantics under aggregation:** a correction, denial,
  removal, retraction, or dispute resolution that affects observations
  propagates to the public surface as **aggregate recomputation** (the
  aggregate's confidence/acknowledged breakdowns change) **plus** a ledger
  entry on the sector detail page. The correction is visible where the
  numbers are, not buried. (data-model.md, docs/dashboard-spec.md)
- The slim dispute process (docs/dispute-process.md) now covers
  sector-classification errors, internal-record inquiries, and provenance
  challenges — the sector-appropriate replacement for named-victim
  takedown disputes.

Status remains `proposed (pending user redline)`.
