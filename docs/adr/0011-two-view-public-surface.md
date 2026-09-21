# ADR 0011: Two-view public surface — sector exposure and exploitation detail

- Status: proposed (pending user redline)
- Date: 2026-09-21
- Deciders: project lead

## Context

The original dashboard-spec described a single public surface: sector-week
aggregates on the NAICS 2-digit spine, with a correction ledger and an
evidence-manifest browser. That surface is a *research surface* — it answers
"which verticals are being hit and how often." It does not directly answer
the operational question a defender asks on a Friday afternoon: "what
should I patch or harden this week."

User ruling (2026-09-21): the public xevents surface exists to help
defenders reduce risk, not to catalog history. Two questions matter to two
audiences:

1. **How big of a target am I, and how am I being attacked?** — sector
   exposure, coarse attack class. Board-level and CISO-level language.
2. **What are attackers actually exploiting?** — specific CVEs, misconfigured
   classes of appliance, published mitigations. Operational engineer's
   language.

A single surface conflating both audiences either dilutes the operational
signal (view 2 material buried inside sector cells) or muddies the sector
picture (technical detail on every row obscures the trend). Two views,
share the same corpus, publish two lenses.

The naming policy (docs/naming-policy.md) remains unchanged: no organization
names, no threat-actor brand names, in either view.

## Decision

The public surface is two views, both rendered from the same
`data/aggregates/*.jsonl` corpus, both static HTML on GitHub Pages, both
regenerated on the weekly public-publication cadence (open-decisions.md
#12).

### View 1 — Sector exposure

**Question answered:** how big of a target is my vertical, and what shape
are the attacks taking?

**Audience:** CISOs, board briefings, defender teams orienting to their
industry's threat landscape.

**Unit:** sector-week cell (NAICS 2-digit × ISO-week).

**Vocabulary:** coarse, human — the words a CISO uses. Recorded in
`docs/attack-class-vocabulary.md`. A single primary `attack_class` per
observation, chosen from a controlled enum (see that file).

**Cells display:**
- Sector label
- Count of observations in the cell (subject to small-cell rule,
  open-decisions.md #13)
- Attack-class breakdown (e.g. "3 ransomware, 1 phishing_compromise")
- Confidence-band summary
- Link to view 2 for the same period (not cross-indexed by sector)

**Cells never display:** organization names, threat-actor names, malware
brand names, CVE identifiers, vendor advisory URLs. View 1 is deliberately
coarse.

### View 2 — Exploitation detail

**Question answered:** what specifically should my team fix or harden this
week?

**Audience:** operational engineers, patch-management owners, threat
hunters.

**Unit:** technique or vulnerability, ranked by prevalence across the
corpus for the reporting window.

**Vocabulary:** specific, operational. Recorded in
`docs/exploitation-vocabulary.md`. Includes: CVE identifiers,
CISA KEV presence flag, vendor advisory URLs, mitigation reference URLs,
appliance class (SSL VPN, edge firewall, MFT server — as *classes*, not
product names), misconfiguration class (exposed RDP, unauthenticated API,
weak MFA).

**Entries display:**
- Technique or CVE
- Count of observations referencing it in the reporting window
- CISA KEV flag if applicable
- Links to vendor advisories, patches, and published mitigations
- Sector distribution ONLY IF the count exceeds the small-cell floor
  (open-decisions.md #13) on the technique axis

**Entries never display:** which specific victim was hit by which CVE, which
group used which technique, which sector-week cell any single observation
came from.

### Deliberate non-cross-indexing

View 1 and view 2 are the same corpus sliced two ways. They do not
cross-reference. Specifically:

- A view 1 sector cell does not link to the CVEs relevant to *that cell*.
  It links to view 2 for the same period, unfiltered by sector.
- A view 2 technique entry does not link to the sector cells where it
  appeared, unless the technique's total count exceeds the small-cell floor
  by a wide margin (defined in dashboard-spec.md).

**Why:** a reader who can cross-index "Healthcare, 1 listing this week,
ransomware" (view 1) with "CVE-2026-XXXX seen this week" (view 2) can
re-identify the victim with precision neither view alone allows. The
non-cross-indexing rule is the mechanical control that prevents this.
Convenience of navigation is deliberately traded for the boundary.

### G5 name-scan applies to both views

The pre-publish name-scan gate (ADR 0010 §1 G5) runs on the rendered output
of both views. A vendor advisory URL is publishable; a URL whose destination
names a victim is not. G5 is specified in a separate ADR (0013).

## Consequences

- The dashboard-spec is split into two view specs. Each view has its own
  layout, its own extraction requirements, and its own review discipline.
- The observation record gains two independent vocabulary fields:
  `attack_class` (view 1) and the exploitation-detail bundle (view 2).
  Extraction from RansomLook's free-text `description` field is
  best-effort; both fields carry `unspecified` as a legitimate value.
- The technique vocabularies are load-bearing controlled enums. Free-text
  is not permitted in either. Additions to either enum require an ADR
  amendment.
- Cross-indexing between views is a *design constraint*, not an
  implementation convenience. The static-site generator MUST NOT emit
  links or filters that cross the boundary.
- Re-identification risk is now bounded on two independent axes rather
  than one. The residual risk (a reader manually cross-referencing the
  two views over multiple weeks) is documented in the coverage-boundary
  statement.

## Non-goals

- Named-victim disclosure links (SEC 8-K, HHS OCR entries). View 2 links
  only to vendor and sector disclosures that don't name specific
  organizations. Revisiting this is post-MVP.
- Threat-actor attribution. View 2 does not name groups; the corpus records
  them privately in `xevents-internal`.
- Real-time views. Both views regenerate on the weekly public-publication
  cadence.

## Research basis

- Landscape report §1.1 (RansomLook `description` field carries technique
  hints in free text — extraction is heuristic).
- Landscape report §5.4 (existing sector/breach analytics generally
  conflate the two audiences this ADR separates).

## Related

- Supersedes the single-surface framing in `docs/dashboard-spec.md`
  (2026-09-20 version). The dashboard-spec is amended in the same PR.
- Requires ADR 0012 (aggregation-boundary transport) and ADR 0013 (G5
  name-scan gate specification).
- Extends `docs/naming-policy.md` — see the "actionable-information
  principle" section added in the same PR.
