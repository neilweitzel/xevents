# xevents — Attack-class vocabulary (view 1)

**Status:** proposed, 2026-09-21. The controlled vocabulary for view 1
(sector exposure) of the public surface. See ADR 0011.

## Purpose

View 1 answers "how big of a target is my vertical, and what shape are the
attacks taking?" for a CISO or board audience. That question is answered
badly by specific technical terms and answered well by a short list of
recognizable categories.

This file is the authoritative list of those categories. Additions require
an ADR amendment. Free text is not permitted in this field.

## The field

Each observation carries one primary `attack_class`, chosen from the enum
below. A single observation cannot carry multiple classes; ambiguous or
uninformative listings receive `unspecified`.

## Enum

- `ransomware` — encryption-based extortion. Includes double-extortion
  listings (encryption + data theft) where encryption is the primary
  leverage mechanism. The RansomLook listing itself is prima facie
  evidence.

- `data_extortion` — data-theft extortion without encryption. Group
  threatens to publish stolen data; no encryption is claimed. Distinguished
  from `ransomware` because the defensive posture (encryption at rest,
  backup restore) differs.

- `phishing_compromise` — access gained through phishing, per the
  listing's own text or a linked disclosure. Not inferred.

- `social_engineering` — non-phishing human-layer attack: pretexting,
  vishing, business email compromise, help-desk impersonation. Used when
  the source explicitly says so; not a default for "unknown human factor."

- `credential_abuse` — valid accounts used, no exploit named, no
  human-factor named. Includes password spraying and credential stuffing
  where the source says so.

- `supply_chain` — third-party vendor, MSP, software update, or shared
  service is implicated. Used when the source explicitly names a supply-
  chain vector, not when a vendor is merely mentioned.

- `exploitation_public_facing` — exploitation of an internet-facing
  application or appliance. When this class is used, view 2's
  `cve_ids` or `appliance_class` will typically be populated too.

- `insider` — insider threat, per the listing or a linked disclosure.

- `unspecified` — the listing gives no informative signal about the
  attack class. Legitimate value; the default when free-text `description`
  is empty or non-informative.

## Extraction discipline

- View 1 extraction reads only the RansomLook fields committed at ingest:
  `post_title`, `group_name`, `description`, `link`, plus any linked
  disclosure the ingest fetched.
- Extraction is heuristic (regex + short controlled-vocabulary matcher);
  the extractor version is recorded on every observation.
- When two classes could apply, `ransomware` takes precedence over
  `data_extortion` (encryption is the higher-severity claim);
  `supply_chain` takes precedence over the specific vector it flows
  through; otherwise the first match wins and the extractor logs the
  ambiguity for human review.
- Human review of first-seen extraction patterns is 100%; steady-state
  review is sampled per ADR 0010 §5.

## What this vocabulary does not include

- Malware family names (LockBit, BlackCat, etc.). These are threat-actor
  brand names by another name and are excluded by the naming policy.
- CVE identifiers. Those live in view 2's exploitation vocabulary. View 1
  says "exploitation_public_facing"; view 2 says which CVE.
- Vendor names. `supply_chain` is the class; a specific vendor never
  appears on view 1.
- Malware capability classes (wiper, stealer, RAT). These describe
  payload behavior; view 1 is about attack initiation. Payload behavior
  is a view 2 concern if it becomes relevant.

## G5 interaction

The name-scan gate (ADR 0013) runs on the rendered view 1 output. This
vocabulary is denylist-safe by construction: no value in the enum is a
name.
