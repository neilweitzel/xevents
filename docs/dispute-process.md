# xevents — Dispute and correction process

**Status:** limited-RC process approved, 2026-09-23. Implements ADR 0004 and open-decisions.md
#4 (SLA) as narrowed by #8 (sector-aggregated public surface). The
published process ships before the public surface serves data (ADR 0004);
handling is manual in MVP.

**Counts-only RC update (2026-09-23):** routine eligible records do not enter a
manual approval queue. Exceptional correction/privacy review remains manual.
The RC supports private candidate suppression and recomputation, not the
complete public correction ledger described below. GitHub issues/PRs are the
ordinary public channel; GitHub private reporting is required for sensitive
evidence, privacy concerns or identities. The companion is
the [RC research/privacy memo](research-privacy-memo.md).

## Scope of disputes in a sector-aggregated product

Because the public surface names no organizations and no actor brands,
there is no public named entry to contest. That reduces direct exposure but
does not eliminate correlation, misclassification or private-holdings risks. What
remains, and what this process covers:

1. **Sector/vertical classification corrections** ("you placed this
   incident in healthcare; it was a manufacturing firm").
2. **Internal-record inquiries** ("do you hold a record about us, and what
   does it say?"). The internal store keeps names as claimed by sources;
   an organization may ask what we hold.
3. **Provenance/manifest challenges** ("your manifest entry does not match
   the source record").
4. **Method/vector/malware-class corrections** from researchers.

Legal demands, privacy reports and sensitive takedown requests enter through
GitHub private reporting.
Urgent privacy or safety concerns may require precautionary withholding while
review continues. The [RC research/privacy memo](research-privacy-memo.md)
is the companion assessment; statutory obligations are not displaced by this
project's ordinary response targets.

## Intake

- **Public channel:** the
  [research correction form](https://github.com/neilweitzel/xevents/issues/new?template=correction.yml)
  or a pull request for non-sensitive aggregate, export, app or methodology
  corrections.
- **Sensitive channel:** [GitHub private reporting](https://github.com/neilweitzel/xevents/security/advisories/new)
  for security flaws, privacy concerns, personal information, credentials,
  affected-party identities or sensitive evidence. Never place those in a
  public issue or pull request.
- **A complete submission contains:** the specific aggregate/manifest entry (IDs,
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
3. **Resolution taxonomy**, recorded privately for the RC; the public
   correction-ledger design below is not yet implemented:
   - `correction` — the aggregate or classification is amended;
     aggregates are recomputed and the ledger shows the change.
   - `denial` — the submitter's assertion is recorded and investigated;
     published only if it changes the record.
   - `dispute_opened` / `dispute_resolved` — the procedural envelope.
   - **Evidence-led correction, precautionary safety withholding.** An
     unsupported assertion does not establish a corrected fact. Credible
     privacy, legal or safety concerns may nevertheless justify withholding
     while reviewed; preserving an audit trail does not require continuing
     public exposure. The RC records that decision privately and recomputes
     aggregates without publishing the disputant's identity.
4. **Response.** The submitter gets the outcome and the reasoning in
   writing. In the RC, a suppression changes the next recomputed aggregate
   without publishing the disputant's identity. A public correction ledger is
   future work; the submission and audit record stay private.

## Appeals

One reconsideration, new evidence only, within 30 days of the outcome.
Under solo operation (ADR 0010 §2, machinery-first doctrine;
open-decisions.md #18), the appeal is reviewed by the operator with a
mandatory 72-hour cooling-off period between submission and decision, unless
an urgent safety or statutory response requires earlier action. The reviewer
records the outcome and reasoning privately for the RC. After that, the
ordinary project appeal is final, without limiting legal rights. If
a second named reviewer is ever added to the project, this reverts to
the standard two-person rule with no policy amendment required.

## Internal-record inquiries (class 2)

On a verified request from the organization itself, xevents confirms
whether it holds records about them and summarizes what was claimed, by
whom, and when — without disclosing other organizations' records, reviewer
identities, or internal methodology beyond what is already public. This is
a transparency commitment, not a reason to refuse deletion automatically.
Erasure requests are assessed under applicable obligations, retention limits
and the research/privacy memo, including historical copies rather than only
the working tree.

## Adversarial posture

The dispute channel is observable, and threat actors read. Controls:
standing verification before any substantive response, no enumeration of
evidence holdings, rate limiting on intake, pattern logging across
submissions. RC dispute outcomes and contents stay private. Changes to public
aggregate releases may still reveal the timing of a correction; that residual
correlation risk must be considered before publishing a corrected release.

## Operational commitment

A published channel nobody monitors is worse than none (ADR 0004). GitHub
notifications and private reports are checked on business days; the response
targets are tracked in the review queue. If the project cannot monitor these
channels, public releases are paused.
