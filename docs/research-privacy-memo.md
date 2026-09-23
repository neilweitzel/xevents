# Counts-only RC research and privacy memo

Status: operator-reviewed and approved for the limited RC on 2026-09-23. This
records the bounded RC design, not legal advice or general legal clearance.
Neil Weitzel confirmed this is a personal research project operated from
Indiana, USA, accepted the residual risks described here, and approved lead
sign-off without requiring counsel before this limited RC.

## Purpose and scope

xevents studies how publicly reported incident claims appear across sectors
over time. The first RC uses one source, a bounded recent-record window and
description-based classification. It does not verify breaches, identify
affected parties publicly, collect breach dumps or make decisions about people.

RansomLook states that its website, API and datasets use CC BY 4.0. The app
credits RansomLook and identifies its own aggregation rather than presenting
source claims as established facts ([RansomLook licensing](https://www.ransomlook.io/about)).
That permission does not by itself settle privacy, confidentiality or
third-party rights.

## What is collected and what is published

The private repository holds retrieved listing metadata, exact source evidence,
optional supplementary screenshots, immutable observations and derivative
eligibility receipts. It may contain incidental personal or sensitive
information. Screenshots are not classification inputs and a missing screenshot
is not an automatic publication blocker. No breach contents or credentials are
intentionally sought.

The public output is a fixed weekly sector-count matrix, a coverage statement
and hashes of the public export bytes. Original descriptions, names, source
URLs, private record identifiers and private evidence hashes are excluded.
Cells below five, including zero, are withheld. Those measures reduce risk;
they do not prove anonymity against correlation or release-to-release inference.

## Jurisdiction and basis for review

The accountable operator is Neil Weitzel, operating this personal research
project from Indiana, USA.
Hosting on GitHub Pages does not alone determine all applicable law. Where
EU GDPR applies, its territorial scope includes the criteria in Article 3;
legitimate interests under Article 6(1)(f) require a necessity and rights
balancing analysis, and research safeguards under Article 89 are not a blanket
exemption ([GDPR text](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)).

The proposed research interest is evidence-backed understanding of public
incident claims. Minimal private evidence supports audit, deduplication,
correction and accurate re-derivation. Aggregation instead of named public
records, bounded collection, restricted access and withholding are less
intrusive measures. They do not automatically outweigh an affected person's
interests, particularly if an artifact includes credentials, sensitive personal
data or material unrelated to that research.

For a UK assessment, the ICO describes the purpose, necessity and balancing
tests; all must be satisfied rather than simply labeling the work “research”
([ICO legitimate-interests guidance](https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/lawful-basis/legitimate-interests/what-is-the-legitimate-interests-basis/)).
No general US or EU/UK legal clearance is asserted here. The lead's review
must determine whether the limited design is appropriate or requires counsel.

## Risk and operational safeguards

- **False interpretation:** the site labels results as claims, identifies the
  source window and retrieval-time basis, and does not publish risk scores or
  infer independent corroboration from repetition.
- **Identity disclosure:** fixed output vocabulary, small-cell withholding,
  conservative metadata eligibility, exact-output name scanning and a strict
  three-location write set prevent source prose from reaching the site.
  External correlation remains a residual risk.
- **Private-store compromise:** raw evidence never enters the public build;
  collection and signing use separate jobs; the short-lived transport token
  is limited to the public repository and separate from the attestation key.
  Authorized private maintainers and GitHub remain trust dependencies.
- **Unsafe source material:** the RC screen is metadata-only, not comprehensive
  PII detection or image OCR. Suspected sensitive content requires restricted
  handling and may require deletion, not merely continued private retention.
- **Misclassification and disputes:** a private correction record can suppress
  a candidate. Routine publication remains automatic; exceptional review must
  not expose a disputant or become a public evidence exchange.

## Retention, correction and deletion

The immutable audit design is not an authorization to retain every raw artifact
forever. During RC burn-in, the operator reviews retained raw material and its
necessity at the 30-day review, on any privacy report, and before expanding
sources or capacity. A longer-term retention policy requires an explicit decision.

Removing a working-tree file does not erase Git history, clones or backups.
A valid erasure or security need requires a scoped administrative response
covering those copies and downstream public artifacts where applicable.
Any retained audit note must itself be minimized. GDPR Article 17 contains
grounds and exceptions for erasure; research alone is not a universal retention
exception ([GDPR text](https://eur-lex.europa.eu/eli/reg/2016/679/oj/eng)).

The [dispute process](dispute-process.md) governs private intake and operational
response targets. Those targets do not replace statutory duties. The RC
suppression mechanism is a research correction, not proof that personal data
has been erased. Credible safety or legal concerns may justify precautionary
withholding while investigated.

## Activation review and reassessment

The operator approved the limited research use, residual risks, RC contract,
dedicated key and enforced deployment path on 2026-09-23. Public GitHub issues
and pull requests are the ordinary project channel. GitHub private reporting is
the channel for sensitive evidence, privacy concerns and affected-party
identities; those must not be posted publicly. Operator approval does not
prevent later counsel review or change legal obligations.

Reassess at the 30-day burn-in review, at least annually thereafter, and before
adding sources, broader coverage, new fields or a changed privacy boundary.
Stop publication if a privacy issue or an unstaffed GitHub reporting channel
makes the accepted operating conditions untrue.
