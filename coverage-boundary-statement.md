# Coverage-boundary statement

**xevents is pre-launch. No coverage claims are made yet.**

This page will carry the weekly public coverage-boundary statement
once M2 lands. Its role in the doctrine (per
`docs/adr/0011-two-view-public-surface.md` and
`docs/adr/0012-aggregation-boundary-transport.md`) is to state, in
plain terms:

- Which source(s) the current publish covers.
- What the per-gate accounting numbers were on this publish (rows
  in, rows through each gate, rows quarantined by G5, rows
  published).
- The boundary write set's file counts as of this publish.
- Any coverage exclusions or known gaps.

The operator writes the statement; the `xevents-boundary[bot]`
GitHub App copies it across from `xevents-internal` on every
publish per ADR 0014.

## Related

- [ADR 0011 — Two-view public surface](docs/adr/0011-two-view-public-surface.md)
- [ADR 0012 — Aggregation-boundary transport](docs/adr/0012-aggregation-boundary-transport.md)
- [ADR 0014 — App-opened-PR transport](docs/adr/0014-app-opened-pr-transport.md)
- `docs/mvp-scope.md` — the M2 scope this page starts serving.
