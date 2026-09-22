# ADR template

Copy this file to `NNNN-short-title.md` for each new decision.

Scope rule (AGENTS.md: Scope discipline): an ADR that lifts an MVP non-goal,
adds a source, or supersedes an `accepted` ADR requires the user's explicit
approval. New ADRs land as `proposed (pending user redline)` and remain
there until the user redlines them; once accepted, per Nygard convention
an ADR's body is not edited — decisions that change are superseded by a
new ADR.

```markdown
# ADR NNNN: Title

- Status: proposed | accepted | superseded by NNNN
- Date: YYYY-MM-DD
- Deciders: <who made the call>

## Context

What problem are we solving, and what constraints shape it?

## Decision

What we decided, stated plainly enough to be wrong.

## Consequences

What this costs, what it rules out, what becomes someone's job.

## Research basis

Landscape-report sections this rests on. Mark anything the research left
unsettled as UNVERIFIED and name what would settle it.
```
