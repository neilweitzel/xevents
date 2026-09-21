# xevents — Naming policy

**Status:** draft, 2026-09-21. Implements open-decisions.md #8. This is a
load-bearing policy: it is what keeps the public surface a research product
instead of a shaming amplifier.

## The rule

The public xevents surface **names no victim organizations and no
threat-actor brands.** Not in text, not in URLs, not in image alt-text, not
in JSON keys, not in filenames. What the public surface publishes:

- **Sector / vertical** (NAICS 2-digit spine, versioned taxonomy;
  `unclassified` when the evidence does not support a classification —
  never a guess).
- **Attack vector / method** (versioned enum: phishing/social engineering,
  exploitation of public-facing application, credential stuffing or brute
  force, USB/removable media, supply chain, insider, ransomware deployment
  as method, cryptomining as payload, other, unknown).
- **Malware class** (generic capability classes: ransomware, cryptominer,
  wiper, stealer/exfiltrator, RAT/backdoor, rootkit/bootkit, unknown).
  Never brand-like names.
- **Breach data classes** (open-decisions.md #10), **confidence band**,
  **victim-acknowledged status**, **time windows**, **counts**.

## Why

Ransomware is a shaming business. A named-victim ledger is free advertising
for the extortion — it does the attacker's publicity work for them. Naming
threat-actor brands is the same gift in the other direction. xevents is a
research project about *which verticals are hit, how, and with what means*;
neither victim names nor actor brands are required to answer those
questions, so neither is published. Victim-level detail remains one click
away via links back to the sources, which is where it already lives.

## The brand-blur rule

In ransomware, malware family names and actor brand names are often the
same string. The publication test is not the string — it is the function:
**publish capabilities and methods; do not publish brands.** "Ransomware
deployed via exploited public-facing application" is publishable. A name
whose primary function is identifying a criminal enterprise is not.
Genuinely ambiguous cases (dual-use tools, commercial tooling abused by
actors) go to the human review queue under the two-person rule (ADR 0010);
the reviewer records the call and the reasoning, which becomes precedent.

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
- ADR 0010 docs QA: the decision-consistency check flags naming-policy
  violations in documentation the same way it flags stale decision
  language.
- Review queue: naming edge cases are a standing 100%-review class.
