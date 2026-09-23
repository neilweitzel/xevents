# xevents — Lawful-basis / public-interest research memo

**Status:** template, 2026-09-21. **This memo is unwritten.** It is a
launch gate (ADR 0003, ADR 0009, mvp-scope.md item 7): the public surface
serves no data until this memo exists and is reviewed. No memo, no public
surface. This template specifies what the completed memo must contain;
filling it is tracked work, not a decision. The counts-only RC assessment is
now [research-privacy-memo.md](research-privacy-memo.md); the operator approved
that limited RC assessment on 2026-09-23. This historical template is guidance,
not evidence of general legal clearance.

## Why this memo is simpler than originally scoped

The 2026-09-21 pivot (open-decisions.md #8) removed the memo's hardest
exposures: the public surface is designed to omit organization and actor names
and publish no breach contents. Aggregation and the name scan reduce risk but
do not prove anonymity or guarantee the absence of personal data. Residual questions
concern the *private* holdings (incidental PII in raw evidence) and the
general publication of claims about incidents. The memo must still be
written — "simpler" is not "unnecessary."

## Required contents

1. **Jurisdictions.** Where xevents publishes (GitHub Pages, US
   infrastructure) and which jurisdictions' law is considered: US
   (primary), EU/UK (GDPR extraterritoriality analysis for the private
   holdings), and any other jurisdiction where the project lead operates.
2. **What is published vs. what is held.** The two-repo split stated
   plainly: public = sector aggregates, manifest hashes, methodology
   (with documented correlation and re-identification risks); private = raw observations and
   evidence (may incidentally contain personal data from source
   material). The analysis differs per repo; the memo covers both.
3. **Lawful basis per jurisdiction.** For the public corpus: the research
   and public-interest basis for publishing aggregated claims about cyber
   incidents. For the private holdings: the basis for retaining
   incidentally-collected personal data (legitimate interest in audit and
   re-derivation, with minimization and the retention policy as
   safeguards).
4. **Data minimization.** What is collected (listing metadata, screenshots,
   raw payloads), why each category is necessary, what is *not* collected
   (breach contents — explicit non-goal; credentials — screened at
   capture), and the pre-storage screen (ADR 0010 G2).
5. **Pseudonymization and naming.** The naming policy
   (docs/naming-policy.md) as a technical measure; the re-identification
   caveat stated honestly (sector + time + method can re-identify a
   motivated reader — harm reduction, not anonymity).
6. **Retention and deletion.** Summary of docs/retention-policy.md with
   the data-subject request handling: where requests are actioned
   (cold-review gate), what "erasure" means against an append-only ledger
   (working-tree suppression alone is not erasure; assess history, copies,
   artifacts, backups and residual linkability),
   and response timeframes.
7. **Risk assessment (DPIA-style).** Foreseeable harms: misclassification
   causing sector-level reputational effects; re-identification;
   compromise of the private repo; threat-actor interaction with the
   dispute channel. For each: likelihood, severity, and the mitigating
   control (with the ADR/doc reference).
8. **Dispute-channel consistency.** Confirmation that the published
   dispute process (docs/dispute-process.md) and this memo agree on
   standing, verification, evidence-led correction and precautionary safety
   withholding during review.
9. **Review cadence and sign-off.** Who wrote it, who reviewed it, when it
   is re-reviewed (at minimum: annually, on any new source, on any
   architectural change touching the trust boundary). **Open question for
   the project lead:** external counsel review before launch, or
   lead sign-off sufficient? Record the answer here when given.
10. **Limitations.** What this memo is not: not legal advice, not a
    substitute for counsel where the risk assessment says counsel is
    needed, and a snapshot — source terms and the law change, so the
    re-verification discipline (AGENTS.md) applies to the memo's premises
    too.

## Acceptance

The memo is complete when every section above is filled with specifics
(no "TBD"), the project lead has recorded review, the counsel question
(§9) is answered, and the dispute process cross-check (§8) is signed off.
Until then the launch gate holds.
