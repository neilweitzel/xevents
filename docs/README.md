# xevents documentation

Start with the [main README](../README.md) for the product and the
[research guide](research-guide.md) for interpreting results. These pages provide
the detail behind the public app without making the homepage an operations manual.

## For researchers

- [Research guide](research-guide.md): coverage, counts, withheld cells and exports.
- [Source specification](source-spec-ransomlook.md): collection contract and limits.
- [Glossary](glossary.md): observations, claims, evidence and incident terminology.
- [Naming policy](naming-policy.md): information excluded from public output.
- [Dispute process](dispute-process.md): correction and sensitive-report handling.
- [Research/privacy memo](research-privacy-memo.md): RC scope and activation review.

## For implementers and reviewers

- [Automated RC contract](adr/0022-unattended-research-rc.md): the bounded
  counts-only release profile and its activation conditions.
- [Architecture decisions](adr/): historical decisions and their status.
- [Data model](data-model.md): the broader model, including planned capabilities.
- [MVP scope](mvp-scope.md) and [dashboard specification](dashboard-spec.md):
  target capabilities, not a declaration that all are implemented.
- [Evidence storage](evidence-storage.md) and [retention policy](retention-policy.md):
  handling design and review obligations.
- [App development](../app/README.md): local reader and synthetic-demo tests.
- [Contributor rules](../AGENTS.md): repository and publication boundaries.

## Reading decision history

Older design documents can describe capabilities beyond the first RC or gates
superseded for its narrowly defined profile. Follow explicit decision status
and the RC contract rather than assuming that every planned view, enrichment,
manual review queue or confidence calculation is live. The public app should
describe only what a released dataset can actually support.
