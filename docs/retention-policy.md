# xevents — Retention Policy

> **Superseded for private records by [ADR 0029](adr/0029-rolling-private-retention.md)**
> (2026-09-25): detailed private records are kept for at least twelve weeks,
> then each whole month is frozen as its published counts and its records are
> removed from the working tree. Screenshots are no longer collected
> ([ADR 0028](adr/0028-no-screenshot-collection.md)). The text below is the
> earlier draft, kept for history.

**Status:** draft, 2026-09-21. Rewritten for the static-first, two-repo
architecture (open-decisions.md #11, ADR 0009); supersedes the 2026-09-20
version, which described database servers and object storage this project
does not have. Required by ADR 0003 ("the retention policy is a documented,
public artifact"). Timeframes are tunable parameters for the user's
redline. Nothing is deleted silently — every lifecycle transition is
itself a recorded event.

## Principles

1. **The ledger is forever.** Observations, correction events, confidence
   assessments, `poll_run` rows, review-task outcomes, and the public
   evidence manifest are never deleted. They are the audit trail the
   project exists to keep (ADR 0001, ADR 0004).
2. **Retention is git history.** There is no database, no object store, no
   backup system to describe. "Retained" means "present in the repo's git
   history"; "deleted" means "removed from the working tree at HEAD, with
   an `administrative_note` correction event recording what, when, and by
   whose decision." Hashes and ledger rows are never removed, so a deleted
   artifact remains verifiable-by-hash and its absence remains explained.
3. **Removal ≠ retraction, and neither means deletion.** Evidence for
   retracted or false claims is retained alongside its correction events —
   silent deletion would destroy exactly the history the correction ledger
   exists to keep (ADR 0003).
4. **Personal data is minimized at capture, not at deletion time.**
   The automated screen (ADR 0010, G2) and the naming policy
   (docs/naming-policy.md) are the primary controls; this policy does not
   retroactively fix a capture failure. A capture failure is a severity-1
   incident (ADR 0010 §3), not a retention event.
5. **The private repo is held to the same policy.** `xevents-internal`
   contents follow the same tiers; the difference is visibility, not
   rigor. Private does not mean disposable.

## Tiers (PROPOSAL — tune in redline)

| tier | contents | retention | physical form |
|---|---|---|---|
| hot | artifacts < 90 days old; all artifacts backing `active`/`contested` incidents | 90 days from capture | `evidence/` at HEAD, private repo |
| warm | artifacts 90 days–2 years old for resolved incidents | 2 years from capture | git history, private repo |
| cold | artifacts > 2 years old | 7 years from capture, then human review | git history, private repo |
| ledger | all JSONL rows (observations, corrections, assessments, poll runs, review tasks) + artifact hashes + the public evidence manifest | indefinite | git history, both repos |

**End of cold retention** does not mean automatic deletion: artifacts
reaching the 7-year mark are flagged for human review via a review task.
Deletion, if approved, removes bytes from the working tree only — hashes
and ledger rows remain, and the deletion is recorded as an
`administrative_note` correction event (what was deleted, when, by whose
decision). Git history is not rewritten for retention deletions; the
severity-1 history-rewrite policy (ADR 0010 §3) applies **only** to
personal data, credentials, and secrets — never to routine retention.

## Lawful-basis notes

- The naming policy (no org/actor names on the public surface) is this
  policy's strongest minimization measure: the public corpus contains no
  personal data by construction, which the name-scan gate (ADR 0010, G5)
  enforces mechanically.
- Residual personal-data risk lives in the private repo (incidental PII in
  screenshots and descriptions, caught by the G2 screen). The cold-tier
  review gate is the point where a data-subject request would be
  actioned; the lawful-basis memo (docs/lawful-basis-memo-template.md)
  specifies the handling.
- The pre-public-surface gate (ADR 0003: written lawful-basis /
  public-interest research memo) must exist before any of this data is
  served publicly.

## Operational requirements

- **Clone-integrity replaces backup/restore.** Because git is the system
  of record, "backup" means: more than one full clone exists, and a
  scheduled check verifies a fresh clone's hashes against the manifest.
  A clone whose hashes do not verify is a failed backup. Tested restores
  (fresh clone + hash verification) are part of the MVP-done checklist.
- Every tier transition is logged (artifact id, from→to, timestamp);
  transitions are reversible until the cold-review gate.
- The scheduled pipeline logs `evidence/` size in every run manifest so
  growth is observed, not discovered.
