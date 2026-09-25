# ADR 0025: Private Gemini sector evaluation on minimized excerpts

Status: accepted

Date: 2026-09-25

Approval: operator requested this evaluation on 2026-09-25 and approved it by
merging this ADR. Each run additionally requires the operator's approval of
the exact excerpt set before dispatch.

## Context

ADR 0022 classifies sectors only from explicit description terms. In the
current private store, 27 of 32 grouped claims are unclassified. A private
review found that about half carry usable business context the rules miss;
the rest have no description or no business context. A manual synthetic
Gemini probe proved connectivity and response handling only. Real accuracy
and abstention behavior are unknown.

## Decision

Allow one bounded, manual, private measurement of Gemini sector
classification on human-reviewed, minimized excerpts of real descriptions.

- **Inputs.** Only the committed private evaluation file. Each excerpt keeps
  the business-activity text and replaces or removes names, brands, people,
  links, contacts, identifiers, tickers, amounts, precise dates and places,
  extortion text and stolen-data listings. Placeholders are limited to
  `[SUBJECT]`, `[COUNTRY]` and `[DATE]`. Candidates with no description or no
  business context are excluded and never sent.
- **Binding.** Each case records its private candidate ID and a digest of the
  source description. An offline check verifies these against intake-data,
  exact coverage of the rule-unclassified set, and the absence of name, actor,
  title and link tokens in excerpts. It is not a guarantee of anonymity.
- **Request.** One excerpt per request, serially, from the private
  repository's `main` branch by manual dispatch only. The model receives the
  excerpt and the same sector policy as the synthetic probe. It never receives
  candidate IDs, digests, labels, source links, images or full descriptions.
  No tools, grounding, browsing, retries or redirects.
- **Provider.** The Gemini Developer API under Paid Services terms, which
  apply only through a Cloud project with an active billing account. Google
  does not use paid prompts or responses to improve its products but logs
  them for a limited period for abuse monitoring. The operator confirms
  active billing before dispatch.
- **Outputs.** Per-case outcome codes (correct, defensible, acceptable
  abstention, missed abstention, wrong sector, invalid, unavailable),
  aggregate counts and token usage in private workflow logs. No excerpts,
  model quotes or provider bodies are logged.

## Not decided

This is measurement, not activation. It does not change the scheduled
pipeline, sector derivation, eligibility, the privacy floor, the public
schema or published counts. Production model-assisted classification requires
a separate ADR covering automatic minimization, persisted assessments,
replay, failure modes and acceptance criteria. Wrong-sector assignments on
this set weigh more heavily than missed recoveries.

## Limitations

Sixteen cases cannot establish production accuracy. Labels are one
reviewer's reading of NAICS 2022, and ambiguous cases accept more than one
answer. Minimized excerpts reduce but do not eliminate re-identification
through distinctive descriptions sent to the provider.
