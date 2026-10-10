# ADR 0040: Move research-cycle opportunities to minute 42

Status: accepted

Date: 2026-10-10

Approval: operator authorized this change on 2026-10-10 by requesting work on
the proposed minute-42 change before the acquisition and second-source work.

## Context

GitHub scheduled workflows are best effort. Its documentation describes
delays during high load, including the start of each hour, and possible dropped
jobs. It recommends choosing another minute:
https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule

Changing a minute does not establish a delivery improvement. Missing run
records cannot identify their originating cron slots or prove why they are absent.

## Decision

Change only the trigger minute from `59 */2 * * *` to `42 */2 * * *`.
Keep the two-hour opportunities, six-hour source-capture guard, 200-record
window, once-per-UTC-day publication gate and all integrity controls unchanged.
This supersedes earlier decisions fixing minute 59; their historical records
remain unchanged. Hourly triggers are not authorized by this decision.

UTC opportunities are 00:42, 02:42, and every two hours through 22:42.
During EDT these correspond to 8:42 PM the prior day, 10:42 PM, 12:42 AM,
and every two hours through 6:42 PM. UTC remains authoritative across DST.

## Verification

Test the exact new cron in both workflow contract tests, reseal the workflow,
and require private CI to pin the merged public authorization. After merge,
report configuration and an actual scheduled invocation separately. A manually
dispatched success does not verify delivery of the schedule.

Compare delivered scheduled starts and actual capture gaps across complete
UTC dates when asked to review performance. Do not promise a particular start
rate, attribute starts to guessed originating slots, or create a monitor
without separate approval.
