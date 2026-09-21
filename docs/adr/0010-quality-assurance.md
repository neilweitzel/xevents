# ADR 0010: Quality assurance, review, and testing controls

- Status: proposed (pending user redline)
- Date: 2026-09-21
- Deciders: project lead

## Context

xevents publishes claims about real organizations' worst weeks. A single
quality failure — a personal email address committed to a public git repo, a
wrongful listing presented as fact, a silently corrupted aggregate — does
lasting damage that no correction ledger fully undoes. Quality cannot be a
post-build aspiration; it has to be designed as gates the pipeline cannot
skip. This ADR specifies those gates, the human-review machinery, the
testing contract the build will be held to, and the failure-handling
procedures. It implements the "highest quality" bar the project lead set
for the MVP phase (2026-09-21).

Two-repo reality (open-decisions.md #11) shapes everything below. There are
two quality boundaries, not one:

1. **Ingest boundary** (source → `xevents-internal`): raw observations must
   be faithful, complete, and honestly timestamped.
2. **Publication boundary** (`xevents-internal` → public `xevents`): nothing
   name-bearing, nothing unverified-beyond-its-band, nothing unframed may
   cross. The public build never reads the private repo.

## Decision

### 1. Observation lifecycle gates

No observation reaches any persistent store without passing each gate in
order. No aggregate reaches the public repo without passing the publication
gates. Gates are pipeline code, not convention — a run that cannot complete
a gate quarantines the batch instead of publishing.

**Ingest gates** (per observation, before write to internal store):

- **G1 — schema validation.** The observation validates against the pinned
  schema version. Failure → quarantine queue with the validation errors
  attached. No coercion, no silent defaults, no partial writes.
- **G2 — automated PII screen.** A pattern library scans all free-text
  fields and evidence metadata: email addresses, phone numbers, national
  identifiers (SSN and equivalents), API keys / secrets / credentials,
  private keys, password-like strings. Any hit → quarantine; the item never
  auto-publishes. The pattern library is versioned; additions are recorded
  with the incident or review that motivated them.
- **G3 — confusable-character scan.** Victim and actor name strings are
  scanned for homoglyphs, zero-width characters, and mixed-script spoofing.
  A lookalike name is exactly how an innocent org gets wrongfully listed;
  any hit → human review, never auto-pass.
- **G4 — human review** (sampling regime below). Items in the 100% classes
  require a recorded reviewer decision before the batch is eligible for
  aggregation.

**Publication gates** (per aggregation batch, before push to public):

- **G5 — name-scan gate.** The mechanical enforcement of the naming
  policy (docs/naming-policy.md). Every organization, actor, malware
  family, and named-person string in the source window forms a denylist;
  every rendered public output is scanned against it (JSONL values and
  URL destinations) under normalized substring, token, domain-form, and
  slug match rules, including homoglyph folding. Failure → quarantine
  the batch as a severity-1 incident. Full specification in ADR 0013.
- **G6 — framing gate.** Every public text field is asserted to carry
  claim-framing ("claimed by", "listed by", band label, victim-acknowledged
  status). Unframed text fails the build.
- **G7 — manifest gate.** Every aggregate row links to evidence-manifest
  entries (hashes); every manifest entry resolves to a recorded retrieval.
  Dangling references fail the build.

### 2. Human-review sampling regime

100% human review for:

- all **forward-going observations** during burn-in (first 500 published
  observations produced by live ingest, or first 30 days of publication,
  whichever is longer). Burn-in counts forward-going observations only
  — backfilled observations do not contribute to the burn-in count and
  are not subject to 100% burn-in review (see backfill rule below);
- every item flagged by G2 or G3;
- every first-seen sector/vector/malware-class value (novel taxonomy
  assignments are where misclassification hides);
- every `victim_acknowledged` transition to `acknowledged` (the status is
  high-trust; its evidence bar must be).

**Backfill rule (open-decisions.md #17).** The RansomLook first-run
historical backfill enters `xevents-internal` under a `backfill_load`
provenance marker. Backfilled observations:

- Do not count toward the 500-observation burn-in threshold.
- Are not subject to 100% burn-in review.
- Are reviewed at the same 10% risk-stratified sampling rate as
  post-burn-in steady-state observations, with 100% review still
  applied to first-seen taxonomy values within the backfill.
- Are held internal-only until the forward-going burn-in completes.
  Public aggregates do not include backfilled observations until burn-in
  is signed off; whether backfilled aggregates publish in a second wave
  after burn-in is a separate downstream decision (see open-decisions.md
  #17).

After burn-in: **risk-stratified random sampling at 10%**, reviewed
quarterly for calibration (if the miss rate in the sample exceeds 2%, the
rate doubles until two consecutive clean quarters). Every review records
reviewer id, timestamp, decision, and sample class.

**Approval rule.** Single named-reviewer sign-off for routine items.
**Two-person rule** for: publishing anything G2/G3 flagged (redaction
override), any `disputed`-band aggregate, and any naming-policy edge case
(§4 of docs/naming-policy.md), *including any addition to the G5
allowlist (ADR 0013 §2).*

**Solo-operator interim (open-decisions.md #18).** While the project has
only one named reviewer, the two-person rule splits by case. Two of the
three cases fall back to disciplined single-reviewer review; the third
stays hard-blocked with no bypass.

- **G2/G3 flag override (redaction override) — single-reviewer with
  discipline.** Rationale: the harm mode is "published something we
  shouldn't have," which is recoverable via the correction ledger
  (§4). The interim controls:
  - A 24-hour cooling-off period between the flag timestamp and the
    override decision.
  - A written second-look note: the reviewer re-reads their own
    justification after the cooling-off period and either confirms or
    reverses. Both entries are recorded.
  - Automatically restores to two-person the moment a second reviewer
    is named in the reviewer registry.
- **`disputed`-band aggregate publication — single-reviewer with
  discipline.** Same controls as G2/G3 override. Same rationale: the
  correction path is well-defined.
- **Naming-policy edge cases, including G5 allowlist entries —
  hard-blocked, no bypass.** Rationale: an allowlist entry is a
  deliberate bypass of the load-bearing name-scan control (ADR 0013).
  A solo operator adding allowlist entries reduces G5's guarantee to
  "the operator's judgment on any given day," which is the exact
  collusion path ADR 0013 §7 named as an explicit non-defense.
  - Until a second named reviewer exists, the G5 allowlist stays
    empty.
  - Any false positive G5 fires on becomes a quarantined batch.
    Quarantined batches wait for a second reviewer to resolve or are
    dropped; there is no single-reviewer path.
  - When a second reviewer is named, this case reverts to the standard
    two-person rule with no ADR amendment required — the interim
    describes only the constrained state.

**Surface-pause tripwire.** If more than 3 single-reviewer G2/G3 or
`disputed`-band overrides occur in a rolling 7-day window, the public
surface pauses on the next scheduled publish. Resuming requires either
(a) a second named reviewer signing off on the accumulated overrides,
or (b) a new ADR amendment. Rationale: the interim is meant to unblock,
not to become the steady state; sustained reliance is the signal that a
second reviewer is now a hard requirement.

**Reviewer registry.** The list of named reviewers lives in
`xevents-internal` (path to be pinned in the private repo's file-layout
doc). Adding or removing a reviewer is itself a two-person action once a
second reviewer exists; while solo, adding the first additional reviewer
is single-reviewer with a written justification (bootstrapping
exception — the alternative is a permanent deadlock).

### 3. Failure handling

**Severity-1: personal data or credentials published.** (1) Remove from
public outputs immediately (site + export + manifest references). (2)
Record an `administrative_note` correction event: what, when found, by
whom, root-cause class (screen miss / review miss / novel pattern).
(3) Git-history policy: history rewrite **only** for personal data,
credentials, or secrets; otherwise suppress-forward with the correction
ledger as the record. Every rewrite is itself logged (what commits, why,
who authorized). (4) Feed the miss back: pattern-library update and/or
sampling-rate change, recorded with the incident.

**Severity-2: wrongful or materially wrong aggregate published**
(e.g. sector misclassification that changes the story, understated
band). Correct via the correction ledger; recompute the aggregate; the
wrong aggregate remains visible in history with its correction — the
ledger is the product.

**Severity-3: pipeline integrity failure** (integrity mismatch, partial
publish, stale output). Quarantine, roll back to the last good public
commit, diagnose from run manifests. See the runbook design
(docs/dashboard-spec.md, operations appendix).

### 4. Testing contract (specified now, enforced at build)

The build will be held to these; they are written here so there is no
argument later about what "tested" meant:

- **Schema tests:** golden fixtures per source; schema version pinned;
  a breaking change requires an ADR and a version bump.
- **Determinism:** the same source snapshot produces byte-identical
  observations and aggregates (golden-file tests).
- **Append-only enforcement:** CI asserts no pipeline run rewrites a line
  in an append-only file (observations, correction events, manifest).
  Removal is a correction event, never a delete — except the tested
  severity-1 emergency path, which is itself a tested, logged procedure.
- **Two-clock invariants:** every record carries `observed_at` (ours);
  source-asserted timestamps are preserved verbatim or null, never
  synthesized.
- **Adversarial inputs:** malformed HTML, encoding tricks, oversized
  fields, schema drift, upstream convention changes → quarantine, never
  crash, never silent-pass. Upstream convention changes (new fields,
  changed `private`/`audit team` semantics) trip a schema-fingerprint
  check: per-source field-name/type hash computed each poll; any change
  quarantines the source and requires human sign-off plus a poller-version
  bump before resuming.
- **Evidence integrity:** publish-time hash verification (bytes match the
  manifest); end-to-end retrieval test per the documented practitioner
  workflow (docs/dashboard-spec.md).
- **Site build checks:** link checks, JSON export schema validation,
  claim-framing assertions (G6), export-root framing fields present.
- **Docs QA (runnable now, no code):** cross-reference lint (every ADR/doc
  reference resolves), decision-consistency check (flags "proposed"/"undecided"
  language in decided docs — this automates detection of the drift the
  2026-09-20 review found), glossary-term usage.
- **Freshness SLOs (design; operative when execution is authorized):**
  public aggregates are stale if older than 2 weeks (2× the weekly
  publication cadence, open-decisions.md #12); internal daily rollups are
  stale if older than 2 days; per-source ingest staleness follows the
  poller rules (decision #5). A breach raises a review task, not a silent
  gap.

### 5. Human-review queue design

Entry criteria: G2/G3 flags, first-seen taxonomy values, schema-fingerprint
changes, sector-classification disputes, severity-2 corrections,
sampling-regime draws. Priority order: severity-1 → disputes/corrections →
novel taxonomy → schema drift → routine sample. Batching: the reviewer
works the queue in priority order, oldest-first within a class; no
cherry-picking. Capacity model: expected observations/day × measured
minutes/review, re-estimated monthly during burn-in. **MVP sign-off
threshold:** burn-in complete, queue age under 7 days, zero open
severity-1/2 items. Escalation: any item open longer than 14 days, or any
week where arrivals exceed 2× capacity, triggers a scope pause — the
pipeline stops publishing new aggregates until the queue is triaged. A
buried queue fails the MVP (docs/mvp-scope.md).

### 6. What this ADR does not do

It does not authorize execution. All of the above is design-for-later:
specified now, built when the project lead authorizes the build phase. No
schedules are created and no workflows are introduced by this ADR.

## Consequences

- The pipeline is slower than a naive scraper by design. Review latency is
  a feature: it is the mechanism by which "highest quality" is true rather
  than aspirational.
- The two-person rule and the scope-pause escalation put a hard ceiling on
  throughput. If the corpus grows past what one reviewer can hold, the
  answer is more reviewers or narrower scope — never silent auto-publish.
- The severity-1 history-rewrite policy is the single exception to
  "history is never rewritten" (ADR 0001). It is narrow, logged, and
  requires the rewrite itself to be recorded — immutability yields to
  privacy only for personal data and secrets, never for embarrassment.

## Research basis

- 2026-09-20 MVP gap analysis (build gaps #1 redaction QA, #6 convention
  detection, #7 queue capacity; practitioner gap #11 evidence retrieval).
- AGENTS.md "Scar tissue" (hoax injection, misnaming, PII in screenshots).
- xfeeds precedent: CI-enforced quality bars (pytest, ruff, mypy strict),
  human review via issues, append-only CI assertion.
