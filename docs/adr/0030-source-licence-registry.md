# ADR 0030: Source licences are read as written and enforced from one registry

Status: accepted

Date: 2026-09-26

Approval: on 2026-09-26 the operator directed that xevents handle source
licensing the way xfeeds does, and approved this ADR by merging it.

Extends ADR 0002. It adds no source: every entry other than RansomLook is
`candidate` and still needs its own source ADR and approval before intake.

## Context

ADR 0002 set the doctrine: use only licensing-clean sources, exclude
ransomware.live, credit CC BY sources, and treat any new source as restricted
until a human clears it. It did not say how clearance is recorded, what a
source with silent or unclear terms may do, or where a publisher can object.
The only source's licence text is hard-coded in three places.

The September 2026 source discovery found about thirty candidates.

- **Named licences:** some carry a named licence (CC0, CC BY 4.0, Unlicense),
  or are US federal works.
- **No licence stated:** most state attorney-general breach lists say nothing
  about reuse.
- **Conflicting statements:** ransomfeed.it invites commercial integration of
  its feeds, while marking its reports CC BY-NC.
- **Share-alike:** VCDB is CC BY-SA 4.0, which cannot flow into a CC BY 4.0
  output.
- **Re-published rows:** most ThreatCluster victim rows come from other
  aggregators.

xfeeds solved the same problem (xfeeds ADR-060 and its `sources.yaml`). The
approach: read each licence as written, record the reading in one registry,
and enforce what a source may do in code. Publish on that reading, and make
objection and removal easy. Do not queue work on email confirmations that may
never come.

## Decision

1. **One registry.** `config/source-registry.json` is the only place a
   source's terms and rights are recorded. For each source it records:
   - licence, terms URL and reading;
   - `explicit_grant`, `noncommercial`, `sharealike`;
   - the credit line;
   - the date the reading was taken.

   Verbatim quotes behind each reading live in
   `research/licence-research-2026-09.md`. A source that is not in the
   registry, or is `excluded`, is not used at all.
2. **Read as written. No confirmation needed first.** Silence is recorded as
   silence, and permissive prose is recorded as prose. Neither is treated as a
   licence. xevents publishes on the reading and does not wait on
   correspondence. This replaces the "confirm in writing" items in the source
   discovery report.
3. **Four rights**, enforced from the registry:
   - `publish`: may contribute to released aggregates and is credited.
     Requires terms compatible with the CC BY 4.0 public dataset: not
     non-commercial, not share-alike, and not a re-publication of another
     source's rows.
   - `corroborate`: may strengthen a claim that a `publish` source already
     admitted. Never admits a claim on its own, is never identified per
     record, and adds nothing to a count by itself. Non-commercial,
     share-alike and unclear-terms material goes here at best.
   - `enrich`: may inform a derived label, such as sector. The registry's own
     values are never published. Used for classifier grounding and
     evaluation.
   - `excluded`: not fetched, stored or queried.
4. **A permissive licence on re-published data does not launder it.** A
   dataset that repeats other aggregators' rows takes the independence class
   and restrictions of the original. Only rows the publisher collected
   first-hand can have their own class. For ThreatCluster, that means only
   `first_party=yes` rows.
5. **Explicit grant is tracked separately.** `explicit_grant` is true only for
   a named, citable licence (CC0, CC BY 4.0, Unlicense, MIT, BSD) or a
   written public-domain status such as 17 U.S.C. 105. A `publish` source
   without an explicit grant is allowed, as in the xfeeds primary tier. But
   before the first such source contributes to a release, the export must say
   which counts rest on explicit grants and which rest on a reading, in the
   same way as the xfeeds clean tier.
6. **Attribution comes from the registry.** Every active `publish` source's
   credit line must appear in the site's attribution section and in the
   export's `attribution` field. A test checks that the app text matches the
   registry.
7. **Stated plainly.** xevents follows every licence as we read it, and takes
   real care to do so. Mistakes can still happen. When one is reported,
   through a bug report or a pull request, it is corrected immediately. The
   site's attribution section and the README say this to publishers in those
   words. A request to remove or restrict a source is carried out, not argued.
   Carrying it out means a registry change, which takes priority over other
   work.

## Consequences

- Candidate sources are no longer blocked on licence email. Each new source
  ADR cites its registry entry, and its right follows from the recorded
  reading.
- The following are limited to `corroborate`, `enrich` or `excluded` unless a
  later ADR adds a separately licensed output tier:
  - VCDB (share-alike);
  - the Privacy Rights Clearinghouse chronology (non-commercial site, paid
    database);
  - ThreatCluster's re-published rows;
  - ransomware.live.
- The first disclosure sources in view (Washington, California and Delaware
  AGs) state no licence. They can be `publish` on a reading, which triggers
  item 5 before their first release.
- Private intake still hard-codes RansomLook's attribution. Before a second
  source is ingested, the private side must read this registry from the
  pinned public checkout instead.

## Research basis

- `research/licence-research-2026-09.md` (verbatim terms, fetched
  2026-09-25 to 2026-09-26).
- xfeeds ADR-060 and the `SourceConfig` licence fields in
  `src/xfeeds/models.py` (github.com/neilweitzel/xfeeds).
- ADR 0002 (licensing-clean ingestion), ADR 0006 (independence classes).
