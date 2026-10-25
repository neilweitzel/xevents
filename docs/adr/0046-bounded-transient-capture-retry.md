# ADR 0046: Bounded retry for transient capture failures

Status: accepted

Date: 2026-10-25

Approval: operator authorized this change on 2026-10-25 after reviewing two
source timeouts, by requesting a retry and failure-code change through merge
and verified run.

## Context

Each due research cycle makes one source request with a 15-second transport
deadline. On 2026-10-24 19:00 UTC and 2026-10-25 05:19 UTC, scheduled cycles
failed with the capture stage at 15.1 seconds. Independent probes at the time
of the first failure found the source's HTTPS endpoint unresponsive while its
plain-HTTP redirect answered. The intervening and following cycles captured
normally, and a manual dispatch at 11:04 UTC completed in 1.6 seconds.

One brief network stall therefore fails a whole cycle and emits a failure
notification, while the private run summary reports only `failed`: the
sanitized boundary hides whether the source timed out, refused a connection,
or returned a response that failed a policy check.

## Decision

- A capture request makes at most three attempts per invocation. Each attempt
  keeps the existing 15-second transport deadline, credential-free headers,
  fixed origin, media, size, redirect and encoding policies unchanged.
  Attempts are separated by a fixed 5-second pause. Worst case is about
  55 seconds, inside the existing 60-second capture stage budget; no job
  limit, budget or workflow changes.
- Only transient transport failures are retried: a timeout (including the
  bounded DNS wait and the transport's overall deadline) or a connection-level
  failure (refused, reset, closed before a complete response, DNS failure).
- Everything else fails on the first attempt exactly as before: any non-200
  status, TLS or certificate errors, redirects, compression, unexpected media,
  oversize or unsafe addresses. Non-200 statuses are deliberately not retried,
  so a block or rate limit never receives extra requests.
- Refusal codes become specific: `source_timeout` and `source_unreachable`
  for exhausted transient failures, and `source_fetch_failed` for all other
  transport refusals. Only these fixed codes appear, in the private run
  summary and an Actions error annotation. Exception text, URLs and source
  bodies are still never logged.
- Persistence semantics are unchanged. A retried success records exactly one
  capture event with the successful attempt's retrieval time. An exhausted
  failure records only the existing private `capture_failed` receipt and does
  not advance the capture clock, so the next two-hour opportunity (ADR 0035)
  remains the recovery path. The private receipt schema is unchanged.

## Source load

A healthy source still receives one request per due capture. During a
sustained outage each due opportunity sends at most three requests instead of
one: no more than 36 per UTC day across twelve opportunities, versus 12 today.
No external recovery service, extra trigger or retry across invocations is
introduced.

## Verification

Private tests use a real loopback HTTP boundary: a source that stalls past the
deadline twice then answers is captured on the third attempt as one capture
event with no failure receipt; a source that always stalls yields
`source_timeout` after exactly three attempts; a closed port yields
`source_unreachable` after three; redirect, compression, wrong media, oversize
and non-200 responses each receive exactly one request. Private CI pins this
public decision. After merge, report a real cycle's outcome separately; a
manual dispatch does not demonstrate behavior during an outage.
