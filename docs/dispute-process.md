# xevents — Dispute and correction process

**Status:** draft, 2026-09-21. Implements ADR 0004 and open-decisions.md
#4 (SLA) as narrowed by #8 (sector-aggregated public surface). The
published process ships before the public surface serves data (ADR 0004);
handling is manual in MVP.

## Scope of disputes in a sector-aggregated product

Because the public surface names no organizations and no actor brands,
wrongful-listing disputes — the hard case in the original design — largely
dissolve: there is no public entry naming the disputant to contest. What
remains, and what this process covers:

1. **Sector/vertical classification corrections** ("you placed this
   incident in healthcare; it was a manufacturing firm").
2. **Internal-record inquiries** ("do you hold a record about us, and what
   does it say?"). The internal store keeps names as claimed by sources;
   an organization may ask what we hold.
3. **Provenance/manifest challenges** ("your manifest entry does not match
   the source record").
4. **Method/vector/malware-class corrections** from researchers.

Legal demands (takedown, defamation) enter through this same channel and
receive the same process — there is no separate suppression path. The
lawful-basis memo (docs/lawful-basis-memo-template.md) is the companion
document; the two must agree.

## Intake

- **Channel:** a dedicated email address, published on the site and in
  this document. Private intake, no new infrastructure, no public thread
  that exposes the disputant.
- **A complete submission contains:** who you are, your relationship to
  the subject (for classes 2–4: evidence of standing, e.g. writing from
  the organization's domain), the specific aggregate/manifest entry (IDs,
  URLs, dates), what you assert is wrong, and supporting evidence. The SLA
  clock starts on **complete** submission, not first contact; incomplete
  submissions get one request for the missing pieces.
- **Unverifiable or anonymous submissions** are treated as tips: still
  read, still investigated at the reviewer's discretion, but no SLA
  attaches and no standing is presumed.

## SLA mechanics (open-decisions.md #4)

- Acknowledge within **two business days** (US Eastern); **one business
  day** for claims of wrongful or harmful inclusion.
- Initial assessment within **ten business days**.
- The clock pauses while awaiting evidence from the submitter, and the
  pause is communicated, not silent.

## Handling

1. **Triage.** The reviewer classifies the submission (classes 1–4 above,
   or out of scope) and opens a review task. Vexatious or duplicate
   submissions are logged and closed with a one-line rationale.
2. **Investigation.** Against internal records and the source material.
   The reviewer never discloses internal holdings beyond what is needed
   to resolve the submission — in particular, evidence holdings are not
   enumerated to third parties.
3. **Resolution taxonomy**, each recorded as a correction-ledger event:
   - `correction` — the aggregate or classification is amended;
     aggregates are recomputed and the ledger shows the change.
   - `denial` — the submitter's assertion is recorded and investigated;
     published only if it changes the record.
   - `dispute_opened` / `dispute_resolved` — the procedural envelope.
   - **No suppression on allegation alone.** An aggregate is annotated
     while under review; it is altered only on evidence. (Under the
     sector-aggregated design there is no named entry to suppress, which
     is precisely why the design was chosen.)
4. **Response.** The submitter gets the outcome and the reasoning in
   writing. Outcomes that change public data are visible in the
   correction ledger; the submission itself stays private.

## Appeals

One reconsideration, new evidence only, within 30 days of the outcome.
The appeal is reviewed under the two-person rule (ADR 0010). After that,
the decision stands and is recorded as final.

## Internal-record inquiries (class 2)

On a verified request from the organization itself, xevents confirms
whether it holds records about them and summarizes what was claimed, by
whom, and when — without disclosing other organizations' records, reviewer
identities, or internal methodology beyond what is already public. This is
a transparency commitment, not a deletion mechanism: internal records are
the audit trail. Erasure requests are handled under the retention policy
and the lawful-basis memo, case by case.

## Adversarial posture

The dispute channel is observable, and threat actors read. Controls:
standing verification before any substantive response, no enumeration of
evidence holdings, rate limiting on intake, pattern logging across
submissions. **Risk acceptance:** dispute *outcomes* are public (the
ledger), dispute *contents* are not. We accept that the existence and
timing of corrections is visible; the mitigations above are the answer,
not secrecy about the process itself.

## Operational commitment

A published channel nobody monitors is worse than none (ADR 0004). The
intake mailbox is checked on every business day; the SLA is tracked in the
review queue; a missed SLA is itself a recorded incident with a
root-cause note. If the project cannot staff the channel, the public
surface is paused until it can.
