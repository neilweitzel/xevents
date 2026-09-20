# xevents — Retention Policy

**Status:** PROPOSAL, 2026-09-20. Required by ADR 0003 ("the retention
policy is a documented, public artifact") and referenced by ADR 0007; the
timeframes below are tunable parameters for the user's redline. Nothing is
deleted silently — every lifecycle transition is itself a recorded event.

## Principles

1. **The ledger is forever.** Observations, correction events, confidence
   assessments, `poll_run` rows, and review-task outcomes are never deleted.
   They are the audit trail the project exists to keep (ADR 0001, ADR 0004).
2. **Evidence is tiered, not purged.** Evidence artifacts (screenshots, raw
   payloads, fetch metadata) move to cheaper storage as they age; their
   SHA-256 hashes stay in the database permanently, so a tiered artifact is
   still verifiable on retrieval.
3. **Removal ≠ retraction, and neither means deletion.** Evidence for
   retracted or false claims is retained alongside its correction events —
   silent deletion would destroy exactly the history the correction ledger
   exists to keep (ADR 0003).
4. **Personal data is minimized at capture, not at deletion time.**
   Redaction happens before storage (ADR 0003); retention policy does not
   retroactively fix a capture failure.

## Tiers (PROPOSAL — tune in redline)

| tier | contents | retention | storage |
|---|---|---|---|
| hot | artifacts < 90 days old; all artifacts for `active`/`contested` incidents | 90 days from capture | primary disk |
| warm | artifacts 90 days–2 years old for resolved incidents | 2 years from capture | cheaper object storage |
| cold | artifacts > 2 years old | 7 years from capture, then review | archival storage |
| ledger | all DB rows (observations, corrections, assessments, poll_runs, review tasks) + artifact hashes | indefinite | database backups |

**End of cold retention** does not mean automatic deletion: artifacts
reaching the 7-year mark are flagged for human review. Deletion, if
approved, removes bytes only — hashes and ledger rows remain, and the
deletion itself is recorded as a `correction_event`-style administrative
note (what was deleted, when, by whose decision).

## Lawful-basis notes

- Victim organizations are legal entities in the ransomware-listing corpus,
  but screenshots and descriptions can incidentally contain personal data
  (names, emails). The pre-storage redaction step (ADR 0003) is the primary
  control; this policy's minimization contribution is the cold-tier review
  gate, which is also the point where a data-subject request would be
  actioned.
- The pre-public-surface gate (ADR 0003: written lawful-basis /
  public-interest research memo) must exist before any of this data is
  served publicly — retention tiers are an internal operations matter until
  then.

## Operational requirements

- Backup/restore covers the database **and** the artifact store together; a
  restore that recovers hashes without bytes (or vice versa) is a failed
  restore. Tested restores are part of the MVP-done checklist.
- Every tier transition is logged (artifact id, from→to, timestamp);
  transitions are reversible until the cold-review gate.
