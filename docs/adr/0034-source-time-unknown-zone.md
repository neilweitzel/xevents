# ADR 0034: RansomLook discovery times are local times in an unknown zone

Status: accepted

Date: 2026-10-09

Approval: operator approved on 2026-10-09 by choosing "Unknown-zone ADR",
and approved it by merging this ADR.

## Context

`source_claimed_at` is taken from RansomLook's `discovered` field, written as
`YYYY-MM-DD HH:MM:SS.ffffff` with no zone. The collector reads it as UTC.
RansomLook's own code writes this field with `str(datetime.today())`, which is
the server's local time with no zone attached.

Eligibility screened any observation whose source time was later than our
retrieval time as `future_source_claim`, which permanently withholds it. Across
all retained captures, 127 of 611 observations (20.8%) carried that flag. None
was more than 120 minutes ahead; the largest was 115 minutes. That ceiling is
what a source writing UTC+2 local time would produce, but the zone is an
inference, not a documented fact, and a server's zone or daylight-saving rule
can change.

Withholding about one in five listings, mostly those captured soon after
posting, biases the published counts. Subtracting a guessed offset would make
an undocumented claim about the source.

## Decision

- RansomLook `discovered` values are treated as local times in an unknown
  zone. The raw value, `source_claimed_at` and `source_time_normalization`
  are stored exactly as before; nothing is shifted.
- `future_source_claim` now applies only when the source time is more than
  14 hours after retrieval, the largest offset of any real time zone. Such a
  value cannot be explained by the source's zone and is still withheld.
- The public `time_basis` remains `retrieved_at`. Source times are not used to
  place claims in weeks or months.

## Consequences

Observations previously withheld only because their source time was up to two
hours ahead become eligible on the next release, subject to every other gate.
Recent weekly and monthly counts may rise; no month has been frozen yet, so no
frozen count changes. If RansomLook documents a zone, a new ADR can record the
offset explicitly while keeping the raw values unchanged.
