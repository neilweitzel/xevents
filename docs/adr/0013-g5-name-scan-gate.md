# ADR 0013: G5 name-scan gate specification

- Status: proposed (pending user redline)
- Date: 2026-09-21
- Deciders: project lead

## Context

Every ADR since 0010 has referenced "G5" — the pre-publish name-scan gate
that asserts no organization or threat-actor name has leaked into an
outgoing public batch. ADR 0010 §1 introduced G5 as one of seven gates
but did not specify its mechanics. ADR 0011 (two-view surface) and ADR
0012 (boundary transport) both depend on G5 as the single gate that
decides whether the boundary workflow uses its credential to push.

G5 is the load-bearing mechanical control of the whole design. If G5 is
right, the naming policy is enforced regardless of reviewer fatigue, tool
bugs, or upstream schema drift. If G5 is under-specified, the entire
two-repo architecture is decorative.

This ADR specifies G5 at the level of detail the doctrine requires:
what the denylist is, how the scan is performed, what counts as a
match, what happens on a match, and what G5 does not defend against.

## Decision

### 1. What G5 scans

G5 scans the **rendered public output** of a batch, immediately before
the boundary workflow pushes to the public repo. Specifically:

- Every value in every JSONL row of the batch's view 1 and view 2
  aggregate files
- Every value in every JSONL row of the batch's evidence-manifest
  entries
- Every value in the coverage-boundary statement file, if updated in
  this batch
- URL destinations for every URL in `vendor_advisories` and
  `mitigation_refs` (fetched at scan time; see §5)

G5 does not scan documentation, ADRs, or any other repo content. Those
paths are outside the boundary write set (ADR 0012) and cannot be
modified by the boundary workflow.

### 2. The denylist

G5 uses a denylist built from the private corpus at scan time. The
denylist is not stored; it is regenerated each run from the current
private-repo state.

Denylist entries are drawn from:

- **`subject_raw` values** of every observation in the batch's source
  window (the observations that produced the aggregates being pushed)
- **All aliases** of every entity resolved from those observations
  (entity table's `alias` records; ADR 0005)
- **Threat-actor names and aliases** from every group observation in
  the source window (entity_kind = `threat_group`)
- **Malware-family names** from the internal malware taxonomy
- A **static supplementary denylist** committed to
  `xevents-internal/denylist/static.jsonl`, containing names that must
  never appear regardless of whether they have been observed
  (e.g., common victim organizations, well-known threat brands that
  might not be in the current source window)

Every entry is stored with its raw form and a normalized form (see §3).
Both forms are added to the denylist. Case-insensitive matching is
applied against the normalized form.

### 3. Normalization

Both denylist entries and scan targets are normalized before comparison,
so that "Acme Corp," "acme corp," "acme  corp" (double space), and
"АСМЕ Corp" (Cyrillic homoglyphs) all match the same denylist entry.

Normalization steps, in order:

1. **Unicode normalization** — apply NFKC to fold compatibility
   variants and canonicalize composed forms.
2. **Homoglyph folding** — apply a documented homoglyph table
   (`xevents-internal/denylist/homoglyphs.jsonl`, versioned) that maps
   Cyrillic, Greek, and other visually confusable characters to their
   Latin equivalents. The homoglyph table is treated as data, not code:
   additions are reviewed like any other data change.
3. **Case folding** — Unicode-aware lower-casing (not ASCII
   `lower()`).
4. **Whitespace collapse** — runs of whitespace collapsed to single
   space; leading/trailing whitespace stripped.
5. **Punctuation stripping for name tokens** — trailing corporate
   suffixes (Inc, LLC, Ltd, Corp, GmbH, PLC, Pty, etc.) and their
   punctuation are stripped for a *secondary* comparison; the *primary*
   comparison keeps them.

Both primary and secondary comparisons run; either match is a G5 fail.

### 4. Match rules

G5 emits a match when a normalized denylist entry appears in a
normalized scan target under any of the following conditions:

1. **Substring match** — the denylist entry appears as a contiguous
   substring of the scan value, at word boundaries. "acme" matches
   "acme corp"; "acme" does not match "acmedns" (no word boundary).
2. **Token match** — the scan value, tokenized on whitespace and
   common punctuation, contains a token equal to a denylist entry.
   Catches names embedded in structured strings.
3. **Domain-form match** — the denylist entry appears as any label of
   a hostname in the scan value. "acme" matches "acme.com" and
   "portal.acme.co.uk"; "acme" does not match "acmewidgets.com" (label
   boundary).
4. **Slug match** — the denylist entry, lowercased and hyphen-joined,
   appears as a contiguous substring of the scan value. "Acme Corp"
   generates the slug candidate "acme-corp"; a match on this form
   catches URL slugs.

An observation whose `subject_raw` contains a person's name (an
employee named in the source, an executive named in a linked
disclosure) also contributes tokens of that name to the denylist,
subject to a minimum length of 3 characters per token to avoid matching
common English words.

### 5. URL destination scanning

For every URL in `vendor_advisories` and `mitigation_refs` on any
observation in the batch:

- The URL is fetched at scan time from a network egress point that
  does not carry any operator credentials.
- The response's HTML `<title>`, `<meta name="description">`,
  first-heading text, and canonical URL are extracted.
- The extracted text is normalized and scanned against the denylist
  under the same match rules as JSONL values.
- A match quarantines the URL: the URL is dropped from the outgoing
  batch, the observation is flagged for human review, and G5 records
  the URL and its match reason.
- A URL that fails to fetch (network error, 4xx, 5xx) is treated as
  a match: the batch is quarantined until a reviewer confirms the URL
  is safe. Better a false quarantine than a URL that resolves to a
  named-victim page.

### 6. What G5 does on a match

Any match (JSONL value or URL destination) is a **hard fail**:

- The boundary workflow does not push the batch.
- The batch is written to a quarantine directory in `xevents-internal`
  with a G5 report listing every match, the matching denylist entry,
  and the file/row/field where it appeared.
- A severity-1 incident is opened per ADR 0010 §3.
- The public surface is not affected — the previous week's aggregates
  remain live; the freshness SLO clock starts ticking as normal.
- The reviewer investigates the match, determines whether it is a true
  positive (a real name leak) or a false positive (a coincidental
  substring), and either:
  - **True positive:** the batch is discarded, the upstream extraction
    is corrected, the affected observations are re-processed. The
    matching denylist entry is added to the static supplementary
    denylist so it is caught even outside its source window.
  - **False positive:** *the allowlist path does not exist in v1*
    (open-decisions.md #18, machinery-first doctrine). The fix is
    upstream: refine the denylist entry (add a distinguishing token
    or alias), correct the extraction that produced the ambiguous
    string, or narrow the match rule if the false positive class is
    common enough to warrant it. Upstream fixes enter the private
    corpus, propagate to the next batch's denylist, and are recorded
    on the correction ledger with the specific fix applied.

### 7. What G5 does not defend against

Documented explicitly so the control's limits are honest:

- **Names that have never been observed and are not on the static
  supplementary denylist.** G5 catches what it knows. A new victim
  whose name has not yet entered the private corpus is not in the
  denylist and will not trigger a match. Mitigation: extraction discipline
  keeps `subject_raw` fields populated at ingest, so every observation
  contributes its name to future batches' denylists. The first-seen
  taxonomy review (ADR 0010 §5) catches novel names in inbound
  extraction.
- **Names in image content.** G5 scans text, not image OCR. The
  screenshot artifacts stored under `evidence/<sha256>` in the private
  repo never cross the boundary (ADR 0011 write set); the manifest
  carries only hashes. If a screenshot's rendered text ever crosses to
  public, it would need its own OCR-based gate — not a v1 concern.
- **Semantic re-identification.** G5 catches names, not inferences.
  A sector-week cell of "Healthcare, 1 listing, ransomware" plus a
  regional context clue in a URL slug (e.g. a vendor advisory URL
  whose destination page mentions a hospital in a specific city)
  may re-identify the victim without any name appearing in the
  aggregate itself. The URL destination scan (§5) is the mitigation;
  the residual risk is documented in the coverage-boundary statement.
- **Collusion via allowlist.** *No longer applicable in v1*
  (open-decisions.md #18). The G5 allowlist is immutable under solo
  operation — no entries can be added — so there is no allowlist to
  collude via. The trade is stricter than a reviewer-gated allowlist:
  genuine false positives cost operator work to fix upstream rather
  than being resolvable by a review sign-off. This is the intended
  posture; it preserves G5's guarantee under single-operator
  conditions rather than reducing it to "the operator's judgment on
  any given day."
- **Denylist regeneration failure.** If the denylist regeneration
  step fails (private-repo read error, corrupt data file), G5 fails
  closed: the batch is quarantined, no push. G5 does not fall back to
  a cached or empty denylist under any condition.

### 8. Test corpus

G5 is testable in isolation. The test corpus lives at
`xevents-internal/tests/g5/` and contains:

- **Positive cases** — synthetic aggregates and URLs seeded with
  denylist entries in every match position (substring, token, domain,
  slug, URL destination), each of which must fail G5.
- **Negative cases** — aggregates constructed from real ingested
  observations with names replaced by controlled non-names, which must
  pass G5.
- **Homoglyph cases** — a positive set with Cyrillic and Greek
  substitutions, which must fail G5 under the homoglyph-folding rule.
- **Boundary cases** — near-misses (a name that shares a substring
  with a common English word, a name whose corporate suffix has been
  stripped) that document the expected G5 behavior at the edges.

The test corpus is versioned. CI runs G5 against the corpus on every
change to the G5 code, the homoglyph table, or the normalization
rules; a corpus mismatch fails the build.

### 9. What G5 emits

Every G5 run, pass or fail, produces a **G5 report** written to
`xevents-internal/g5-reports/<batch-id>.json`:

- Batch identifier, scan timestamp, denylist size and version,
  homoglyph table version
- Number of scan targets by type (aggregate rows, manifest rows, URLs)
- Number of URL destinations fetched, failed to fetch, matched
- Every match: matching denylist entry (redacted in the private repo
  copy — replaced with a hash), match rule (substring/token/domain/slug),
  scan target (file, row, field), and match position

The report is retained per the retention policy.

**Public per-gate accounting on the coverage-boundary statement.**
Every weekly publish reports, on the public coverage-boundary
statement: total G5 matches this batch, last-match date, and the
per-gate counts for every publication gate (G2, G3, G5, G6, G7) —
specifically batches quarantined per gate, batches dropped, and
correction-ledger entries filed. Silence on any of these would be
less credible than the counts (open-decisions.md #18, machinery-first
doctrine).

## Consequences

- G5 is now specifiable in code. The name-scan gate stops being a
  design constraint and starts being a testable component with a fixed
  contract.
- The private repo grows two new small files: `denylist/static.jsonl`
  and `denylist/homoglyphs.jsonl`. Structure and initial content
  documented in `xevents-internal` (see private repo AGENTS work,
  TBD). No allowlist file is created in v1 (open-decisions.md #18).
- URL destination scanning introduces a runtime cost — every advisory
  URL in a batch is fetched at scan time. For view 2's expected URL
  volume (a few dozen unique URLs per weekly batch) this is
  negligible; if it grows past a few hundred, cache the destination
  hashes and re-verify on a longer cadence.
- The false-positive allowlist does not exist in v1
  (open-decisions.md #18, machinery-first doctrine). False positives
  are fixed upstream (denylist refinement, aliasing, extraction
  correction); the fix is recorded on the correction ledger.
- G5 fails closed on any operational error (denylist read failure,
  URL fetch failure, corpus mismatch). The default is "no push,"
  which is consistent with the doctrine's asymmetry — a delayed
  publish is a small harm; a name leak is a large one.
- The static supplementary denylist becomes a maintained artifact.
  Additions after true-positive matches accumulate over time; periodic
  review of the static denylist for staleness is documented in
  ADR 0010's docs QA section.

## Alternatives considered

- **Match on raw `subject_raw` only** (the pre-ADR baseline). Rejected:
  misses aliases, misses domain forms, misses homoglyphs, misses names
  embedded in URL slugs. The doctrine's requirement that the boundary
  be mechanical is violated by a match rule that trivially misses.
- **Match on full-string equality after normalization.** Rejected:
  misses names embedded in structured strings. Substring + token +
  domain + slug match is the minimum that catches realistic leakage
  patterns.
- **Human review as the primary gate, G5 as a backstop.** Rejected:
  inverts the doctrine. Human review is a supplement to mechanical
  controls, not a substitute.

## Non-goals

- OCR of screenshot content. Screenshots do not cross the boundary in
  v1.
- Named-entity recognition to catch names not in the denylist. NER is
  brittle and would generate false positives that erode operator trust
  in the gate. G5 is a *known-names* control; unknown names are the
  responsibility of extraction discipline and first-seen review.
- Real-time G5 monitoring. G5 runs at boundary time (weekly), not
  continuously.

## Research basis

- Landscape §1.1 (RansomLook's `subject_raw` field is the ground truth
  for names; extraction accuracy directly bounds denylist coverage).
- Landscape §6.3 (re-identification via context; motivates the
  URL destination scan and the semantic-re-identification caveat).

## Related

- Depends on ADR 0011 (defines what crosses the boundary and therefore
  what G5 scans).
- Depends on ADR 0012 (defines the boundary transport; G5 is the gate
  that decides whether the boundary workflow uses its credential).
- Amends ADR 0010 §1 G5 (replaces the one-sentence gate description
  with this specification).
- (Removed.) The two-person-rule interaction is resolved by
  open-decisions.md #18 — the allowlist is immutable in v1, so no
  approval-gate interaction remains.
