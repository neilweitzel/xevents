# ADR 0042: Private SEC EDGAR cybersecurity-disclosure pilot

Status: proposed (pending operator review)

Date: 2026-10-10

## Context

The active RansomLook stream describes source claims, not independent incident
confirmation. Company-authored SEC filings offer a different evidence role.
They must not be treated as a second copy of the same leak-site claim or as
automatic evidence of ransomware.

SEC describes daily filing indexes, declared User-Agent headers and a maximum
request rate of ten per second. Daily indexes are updated nightly, beginning
around 10 PM Eastern; this is a batch source, not an instantaneous feed:
https://www.sec.gov/search-filings/edgar-search-assistance/accessing-edgar-data

Item 1.05 disclosures generally follow a materiality determination by four
business days. That clock does not start at incident discovery. Material
cybersecurity incidents are not necessarily ransomware or confirmed data theft:
https://www.sec.gov/newsroom/press-releases/2023-139

## Proposed decision

### Evidence role

Start with a private, non-publishing pilot. An explicit Item 1.05 in an 8-K or
8-K/A is a cybersecurity-disclosure candidate, not a classified incident or
a matched victim. Company-authored filings are issuer disclosures hosted by a
regulator. Independence follows the evidence's origin and content, not merely
the website hosting it.

No regex on a company name or keyword automatically creates an incident match.
Unmatched filings remain unmatched. Nonmaterial voluntary disclosures under
other items and foreign-issuer reports are outside the initial pilot; record
that coverage limitation instead of implying coverage of all companies.

### Bounded collection design

Use official daily master indexes to discover candidate 8-K/8-K/A accessions,
then inspect bounded filing metadata/header evidence for the exact item.
Carry a date-based cursor, lookback and unresolved backlog; lack of a weekend
index is not proof of source failure.

Proposed initial bounds: no more than one SEC request per second, no more than
fifty filing requests per acquisition job, explicit time/body/decompression
limits, and no silent discard of excess candidates. An unfinished backlog
remains explicit. Stop on access denial or malformed evidence; do not rotate
identities, increase concurrency or switch to unofficial endpoints.

Before any network pilot, configure a declared User-Agent with an approved
application/contact identity, verify source access and preservation terms,
review new private write paths and approve the exact request envelope.
The offline parser and synthetic tests do not establish deployed access.

Preserve exact index/filing bytes, SHA-256, retrieval time, source URI, CIK,
accession, filing date, form, amendment relationships and parser version
privately. Do not manufacture incident dates from filing dates. Apply the
twelve-week detailed-retention contract and carry late-match/correction state
under its own reviewed policy.

### Rights and public publication

Recheck the source registry's blanket federal-work interpretation before
activation. SEC-hosted company filings are not necessarily government-authored
works; hosting alone does not establish a republication grant. Distinguish
official index metadata, issuer text, exhibits and third-party material.

Public activation requires an independently tested adapter, replayable evidence,
licence disposition, conservative matching, suppression and exact-output G5.
Do not mix SEC disclosures into the existing single-source aggregate schema
without an approved change to the methodology, consumer and privacy contract.

## Verification and rollout

The first change is offline only: strict master-index parsing, origin/path
restrictions, schema/date/identity validation, explicit item recognition,
amendments, and privacy-safe candidate receipts. No schedule, network,
production intake integration or publication is enabled.

Then validate an approved bounded live capture, measure missed/unresolved
candidates and assess matching on a reviewed corpus. Only after those checks
may the registry move from candidate to active for its reviewed role.

This proposed ADR does not change production publication authority. Existing
claim intake remains operational while the independent source is qualified.
