# xevents — Naming policy

**Status:** draft, 2026-09-21. Implements open-decisions.md #8 and ADR 0011.
This is a load-bearing policy: it is what keeps the public surface a
defender's tool instead of a shaming amplifier.

## The two principles

The policy has two principles, both load-bearing:

1. **No identity information on the public surface.** No victim
   organizations, no threat-actor brands, no malware family names, no
   employee names. Not in text, not in URLs, not in image alt-text, not
   in JSON keys, not in filenames.

2. **Actionable information belongs on the public surface.** When a
   defender can reduce risk today because of a piece of information —
   a CVE, a vendor advisory, a published mitigation, a sector-wide
   alert — that information is published, specifically and
   prominently, even though it is detailed. The public surface exists
   to help defenders, not to catalog history.

## The blue-team-on-Friday test

The divider between principle 1 and principle 2 is this test:

> Would a blue-team engineer at 4pm on a Friday do something different if
> they saw this?

If yes, the information is publishable (principle 2 applies). If it only
lets a reader identify a victim or admire an attacker, it is not
(principle 1 applies).

A CVE number passes the test — the engineer patches. A vendor advisory URL
passes — the engineer reads the mitigation. A victim's 8-K URL fails — the
engineer learns who was hit, but does nothing different about their own
infrastructure. A threat-actor brand name fails — it does the attacker's
publicity work.

## What the public surface publishes

View 1 (sector exposure, ADR 0011):

- **Sector / vertical** (NAICS 2-digit spine, versioned taxonomy;
  `unclassified` when the evidence does not support a classification —
  never a guess).
- **Attack class** (coarse, human — the words a CISO uses). Controlled
  vocabulary in `docs/attack-class-vocabulary.md`.
- **Confidence band**, **victim-acknowledged status**, **time windows**,
  **counts**.

View 2 (exploitation detail, ADR 0011):

- **CVE identifiers**, **CISA KEV presence**, **vendor advisory URLs**,
  **mitigation reference URLs**, **appliance class**,
  **misconfiguration class**. Controlled vocabulary in
  `docs/exploitation-vocabulary.md`.

Both views:

- No organization names in any field.
- No threat-actor or malware-family names in any field.
- No vendor names in view 1; vendor names appear in view 2 only via
  advisory URLs (the URL points to a fix, not a victim).

## Why

Ransomware is a shaming business. A named-victim ledger is free
advertising for the extortion — it does the attacker's publicity work for
them. Naming threat-actor brands is the same gift in the other direction.

But a page that says only "Healthcare — 4 ransomware listings this week"
and nothing else fails the second principle: the defender learns nothing
actionable. xevents publishes actionable technical detail (view 2) because
the purpose of the surface is to help defenders, not to be neutral about
harm reduction. What we withhold is identity; what we publish is
defense-relevant technique.

## The brand-blur rule

In ransomware, malware family names and actor brand names are often the
same string. The publication test is not the string — it is the function:
**publish capabilities and methods; do not publish brands.** "Ransomware
deployed via exploited public-facing application" is publishable. A name
whose primary function is identifying a criminal enterprise is not.
Genuinely ambiguous cases (dual-use tools, commercial tooling abused by
actors) go to the human review queue under the two-person rule (ADR 0010);
the reviewer records the call and the reasoning, which becomes precedent.
ADR 0010 §2 additionally classifies naming-policy edge cases — including
any addition to the G5 allowlist (ADR 0013 §2) — as **hard-blocked under
the solo-operator interim**: until a second named reviewer exists, the
allowlist stays empty and quarantined batches wait rather than be
resolved single-handedly (open-decisions.md #18).

## What this does not hide

- **Internally**, observations record names exactly as claimed
  (`subject_raw`, actor strings verbatim) in the private
  `xevents-internal` repository. Auditability requires fidelity; the harm
  is in *publication*, not retention. The aggregation boundary plus the
  name-scan gate (ADR 0010 §1, G5) is what keeps the two apart.
- **Re-identification caveat.** Sector + time window + method can
  re-identify a victim to a motivated reader. This policy is harm
  *reduction* — no names, no search-engine blast radius, no casual
  shaming — not a mathematical anonymity guarantee. The docs say this
  plainly wherever the limitation matters; we do not oversell it.
- **Source links.** The public surface links to source records for
  drill-down. Those sources name victims; that is their editorial choice,
  not ours, and linking is not republication. Where a source reference
  (URL, slug) would itself carry a name into our pages, it is withheld and
  the manifest notes why.

## Enforcement

- ADR 0010 G5 (name-scan gate): mechanical, per batch, pre-push.
  Specification lives in ADR 0013 (TBD).
- ADR 0010 docs QA: the decision-consistency check flags naming-policy
  violations in documentation the same way it flags stale decision
  language.
- Review queue: naming edge cases are a standing 100%-review class.
- **View 2 URL destination check** (ADR 0011): every URL emitted on view 2
  is fetched at publish time and its rendered page title scanned against
  the denylist. A URL whose destination names a victim is quarantined
  and does not publish, even if the URL itself is clean.
