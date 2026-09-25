import test from "node:test";
import assert from "node:assert/strict";
import {CODES, SCHEMA, ACTIVITY_SCHEMA, RUN_SCHEMA, ROLLUP_SCHEMA, MAX_BYTES, parseAggregate, loadAggregate, selection, exportSelection, activitySummary} from "../aggregate.mjs";

export const NOW = Date.parse("2026-09-23T15:00:00Z");
export const header = () => ({
  file_purpose: "sector_aggregate", schema_version: SCHEMA, release_state: "released",
  generated_at: "2026-09-23T14:00:00Z", coverage: "recent_only", time_basis: "retrieved_at", privacy_floor: 5,
});
export const rows = () => ["2026-09-14", "2026-09-21"].flatMap(week_start =>
  CODES.map(sector => ({sector, week_start, claim_count: sector === "31-33" ? 7 : null})));
export const jsonl = (h = header(), r = rows()) =>
  [h, ...r].map(v => JSON.stringify(v, Object.keys(v).sort())).join("\n") + "\n";
test("closed rectangular dataset roundtrips with nulls and fixed sector labels", () => {
  const d = parseAggregate(jsonl(), NOW);
  assert.equal(d.sectors.length, 21); assert.equal(d.rows.length, 42);
  assert.deepEqual(d.sectors.find(s => s.id === "31-33").counts, [7, 7]);
  assert.deepEqual(d.sectors.find(s => s.id === "62").counts, [null, null]);
  assert.equal(d.stale, false);
  assert.throws(() => d.rows[0].claim_count = 15);
});
test("activity bands are strict, compatible and never pretend missing data is zero", () => {
  assert.equal(activitySummary(null), null);
  assert.equal(activitySummary(parseAggregate(jsonl(), NOW)).assessed, "Not reported");
  for (const [floor, label] of [[0, "Fewer than 25"], [25, "25–49"], [50, "50–74"], [10000, "10,000–10,024"], [1000000, "1,000,000–1,000,024"]]) {
    const d = parseAggregate(jsonl({...header(), schema_version: ACTIVITY_SCHEMA,
      assessed_claims_floor: floor}), NOW);
    assert.equal(activitySummary(d).assessed, label);
    assert.equal(activitySummary(d).published, 14);
    assert.equal(activitySummary(d).cells, 2);
    assert.equal(exportSelection(d, selection(d, "", 1)).contract_version, ACTIVITY_SCHEMA);
  }
  for (const value of [-25, 1, 24, 26, 25.1, 1000025, true, "25", null])
    assert.throws(() => parseAggregate(jsonl({...header(), schema_version: ACTIVITY_SCHEMA,
      assessed_claims_floor: value}), NOW));
  assert.throws(() => parseAggregate(jsonl({...header(), schema_version: ACTIVITY_SCHEMA}), NOW));
  assert.throws(() => parseAggregate(jsonl({...header(), assessed_claims_floor: 0}), NOW));
  const excessive = rows().map(r => ({...r, claim_count: 25}));
  assert.throws(() => parseAggregate(jsonl({...header(), schema_version: ACTIVITY_SCHEMA,
    assessed_claims_floor: 0}, excessive), NOW));
  const empty = activitySummary(parseAggregate(jsonl({...header(),
    schema_version: ACTIVITY_SCHEMA, assessed_claims_floor: 0}, []), NOW));
  assert.equal(empty.published, 0); assert.equal(empty.cells, 0);
  const held = activitySummary(parseAggregate(jsonl(header(), rows().map(r =>
    ({...r, claim_count: null}))), NOW));
  assert.equal(held.published, 0); assert.equal(held.cells, 0);
});
test("draft state, extra names, arbitrary sectors and small counts are rejected", () => {
  for (const change of [{release_state: "blocked"}, {privacy_floor: 1}, {actor: "forbidden"},
    {schema_version: "other"}, {coverage: "complete"}, {time_basis: "attack_date"}])
    assert.throws(() => parseAggregate(jsonl({...header(), ...change}), NOW));
  for (const n of [0, 1, 4, -1, 5.1, 1000001, "5", true]) {
    const r = rows(); r[0].claim_count = n;
    assert.throws(() => parseAggregate(jsonl(header(), r), NOW));
  }
  for (const change of [{victim: "forbidden"}, {sector: "__proto__"}, {sector: "99"}]) {
    const r = rows(); Object.assign(r[0], change);
    assert.throws(() => parseAggregate(jsonl(header(), r), NOW));
  }
});
test("duplicate keys and duplicate/missing cells fail, never silently repaired", () => {
  const text = jsonl();
  assert.throws(() => parseAggregate(text.replace('"privacy_floor":5', '"privacy_floor":1,"privacy_floor":5'), NOW));
  assert.throws(() => parseAggregate(jsonl(header(), [...rows(), rows()[0]]), NOW));
  assert.throws(() => parseAggregate(jsonl(header(), rows().slice(1)), NOW));
  assert.throws(() => parseAggregate(text.trimEnd(), NOW));
  assert.throws(() => parseAggregate(text + "\n", NOW));
});
test("real dates, Monday boundaries, contiguous weeks and generation time are enforced", () => {
  for (const date of ["2026-02-30", "2026-09-22", "9999-99-99", "2026-9-21", "2026-09-28"]) {
    const r = rows().map(row => ({...row, week_start: date}));
    assert.throws(() => parseAggregate(jsonl(header(), r), NOW));
  }
  const gaps = rows().map(row => row.week_start === "2026-09-14" ? {...row, week_start: "2026-09-07"} : row);
  assert.throws(() => parseAggregate(jsonl(header(), gaps), NOW));
  for (const generated_at of ["2026-02-30T14:00:00Z", "2026-09-23T15:06:00Z", "bad"])
    assert.throws(() => parseAggregate(jsonl({...header(), generated_at}), NOW));
});
test("staleness and an empty release are explicit states", () => {
  assert.equal(parseAggregate(jsonl(), NOW + 15 * 86400000).stale, true);
  assert.deepEqual(parseAggregate(jsonl(header(), []), NOW).weeks, []);
});
test("filter, sort, window and export contain only selected approved cells", () => {
  const d = parseAggregate(jsonl(), NOW), s = selection(d, "manufact", 1, 1, "latest-desc");
  assert.equal(s.sectors.length, 1); assert.equal(s.rows.length, 1);
  const e = exportSelection(d, s);
  assert.equal(e.synthetic, false); assert.equal(e.rows[0].claim_count, 7);
  assert.equal(selection(d, "", 1, 4, "latest-asc").sectors[0].id, "31-33");
  assert.equal(selection(d, "<script>", 1).rows.length, 0);
  assert.throws(() => selection(d, "", -1));
  assert.throws(() => exportSelection(d, {rows: [{sector: "31-33", claim_count: 99}]}));
});
test("loader requests only the fixed same-origin resource, without credentials", async () => {
  let options;
  const loaded = await loadAggregate(async (url, opts) => {
    assert.equal(url, "./data/aggregates/view1.jsonl"); options = opts;
    return new Response(jsonl());
  }, NOW);
  assert.equal(loaded.state, "ready"); assert.equal(options.credentials, "omit");
  assert.equal(options.mode, "same-origin"); assert.equal(options.redirect, "error");
});
test("missing is waiting; corrupt, private drafts, large and failed responses are unavailable", async () => {
  assert.equal((await loadAggregate(async () => new Response("", {status: 404}), NOW)).state, "waiting");
  assert.equal((await loadAggregate(async () => new Response(jsonl(header(), [])), NOW)).state, "empty");
  for (const body of ["<html>error</html>", jsonl({...header(), release_state: "blocked"}), " ".repeat(MAX_BYTES + 1)])
    assert.equal((await loadAggregate(async () => new Response(body), NOW)).state, "unavailable");
  assert.equal((await loadAggregate(async () => { throw new Error("network"); }, NOW)).state, "unavailable");
  assert.equal((await loadAggregate(async () => new Response("{}", {status: 500}), NOW)).state, "unavailable");
});
test("v3 carries a whole-second run completion that is never before its capture", () => {
  const v3 = (extra = {}) => ({...header(), schema_version: RUN_SCHEMA, assessed_claims_floor: 25,
    generated_at: "2026-09-23T14:00:00.672575Z", evaluated_at: "2026-09-23T14:00:01Z", ...extra});
  const d = parseAggregate(jsonl(v3()), NOW);
  assert.equal(activitySummary(d).lastRun, "2026-09-23T14:00:01Z");
  assert.equal(activitySummary(d).captured, "2026-09-23T14:00:00.672575Z");
  assert.equal(activitySummary(d).assessed, "25–49");
  assert.equal(exportSelection(d, selection(d, "", 1)).contract_version, RUN_SCHEMA);
  // A guarded run: capture unchanged, completion hours later.
  assert.equal(activitySummary(parseAggregate(jsonl(v3({evaluated_at: "2026-09-23T14:59:00Z"})), NOW)).lastRun,
    "2026-09-23T14:59:00Z");
  // Equal to a whole-second capture is accepted.
  parseAggregate(jsonl(v3({generated_at: "2026-09-23T14:00:01Z"})), NOW);
  for (const evaluated_at of ["2026-09-23T14:00:00Z", "2026-09-23T13:00:00Z", "2026-09-23T15:06:00Z",
    "2026-09-23T14:00:01.5Z", "2026-02-30T14:00:01Z", "bad", 1790000000, null])
    assert.throws(() => parseAggregate(jsonl(v3({evaluated_at})), NOW));
  const missing = v3(); delete missing.evaluated_at;
  assert.throws(() => parseAggregate(jsonl(missing), NOW));
  const unbanded = v3(); delete unbanded.assessed_claims_floor;
  assert.throws(() => parseAggregate(jsonl(unbanded), NOW));
  assert.throws(() => parseAggregate(jsonl({...header(), schema_version: ACTIVITY_SCHEMA,
    assessed_claims_floor: 25, evaluated_at: "2026-09-23T14:00:01Z"}), NOW));
  assert.equal(activitySummary(parseAggregate(jsonl({...header(), schema_version: ACTIVITY_SCHEMA,
    assessed_claims_floor: 25}), NOW)).lastRun, null);
});
test("v4 monthly rollups nest weeks and never expose a withheld weekly cell", () => {
  const h = {...header(), schema_version: ROLLUP_SCHEMA, assessed_claims_floor: 50,
    generated_at: "2026-10-06T14:00:00Z", evaluated_at: "2026-10-06T14:00:01Z"};
  const now = Date.parse("2026-10-06T15:00:00Z");
  const weeks = ["2026-09-21", "2026-09-28", "2026-10-05"];
  // Weekly: 31-33 = 7, 7, 7; 62 = withheld x3 (totals 2+3 -> month 5); 54 = 6, withheld(2), -.
  const weekly = {"31-33": [7, 7, 7], "62": [null, null, null], "54": [6, null, null]};
  const w = weeks.flatMap(week_start => CODES.map(sector => ({sector, week_start,
    claim_count: weekly[sector]?.[weeks.indexOf(week_start)] ?? null})));
  const monthly = {"2026-09": {"31-33": 14, "62": 5, "54": null}, "2026-10": {"31-33": 7}};
  const m = ["2026-09", "2026-10"].flatMap(month => CODES.map(sector => ({sector, month,
    claim_count: monthly[month][sector] ?? null})));
  const d = parseAggregate(jsonl(h, [...w, ...m]), now);
  assert.deepEqual(d.months, ["2026-09", "2026-10"]);
  assert.deepEqual(d.sectors.find(s => s.id === "31-33").monthCounts, [14, 7]);
  assert.deepEqual(d.sectors.find(s => s.id === "62").monthCounts, [5, null]);
  assert.equal(activitySummary(d).published, 27);
  assert.equal(activitySummary(d).cells, 4);
  assert.equal(activitySummary(d).monthCells, 3);
  const s = selection(d, "", 1, 3, "latest-desc", "month");
  assert.deepEqual(s.periods, ["2026-09", "2026-10"]);
  assert.equal(s.sectors[0].id, "31-33");
  const e = exportSelection(d, s);
  assert.equal(e.period, "month"); assert.equal(e.contract_version, ROLLUP_SCHEMA);
  assert.ok(e.rows.every(r => "month" in r));
  assert.equal(exportSelection(d, selection(d, "", 2)).period, undefined);
  assert.throws(() => selection(d, "", 1, 4, "name", "month"));
  assert.throws(() => selection(d, "", 2, 3, "name", "month"));
  assert.throws(() => selection(d, "", 0, 1, "name", "year"));
  assert.throws(() => exportSelection(d, {period: "month", rows: d.rows.slice(0, 1)}));
  const bad = (month, sector, claim_count) => m.map(r => r.month === month && r.sector === sector ?
    {...r, claim_count} : r);
  // A month that would reveal a withheld week (6 shown + 2 hidden = 8 exposes 2).
  assert.throws(() => parseAggregate(jsonl(h, [...w, ...bad("2026-09", "54", 8)]), now));
  // A fully published month must equal its weeks and may not be withheld.
  assert.throws(() => parseAggregate(jsonl(h, [...w, ...bad("2026-09", "31-33", 15)]), now));
  assert.throws(() => parseAggregate(jsonl(h, [...w, ...bad("2026-09", "31-33", null)]), now));
  assert.throws(() => parseAggregate(jsonl(h, [...w, ...bad("2026-09", "62", 4)]), now));
  // Months must cover exactly the weeks' months, rectangular and closed.
  assert.throws(() => parseAggregate(jsonl(h, w), now));
  assert.throws(() => parseAggregate(jsonl(h, [...w, ...m.filter(r => r.month === "2026-09")]), now));
  assert.throws(() => parseAggregate(jsonl(h, [...w, ...m, {sector: "11", month: "2026-11", claim_count: null}]), now));
  assert.throws(() => parseAggregate(jsonl(h, [...w, ...m.slice(1)]), now));
  assert.throws(() => parseAggregate(jsonl(h, [...w, ...m, m[0]]), now));
  for (const month of ["2026-13", "2026-9", "2026-09-01", 202609])
    assert.throws(() => parseAggregate(jsonl(h, [...w, ...m.map((r, i) => i ? r : {...r, month})]), now));
  assert.throws(() => parseAggregate(jsonl(h, [...w, ...m.map((r, i) => i ? r :
    {...r, week_start: "2026-09-21"})]), now));
  // Month sums are also bounded by the assessment band.
  assert.throws(() => parseAggregate(jsonl({...h, assessed_claims_floor: 0}, [...w, ...m]), now));
  // Earlier schemas may not carry month rows; v4 without evaluated_at is refused.
  assert.throws(() => parseAggregate(jsonl({...h, schema_version: RUN_SCHEMA}, [...w, ...m]), now));
  const missing = {...h}; delete missing.evaluated_at;
  assert.throws(() => parseAggregate(jsonl(missing, [...w, ...m]), now));
  const empty = parseAggregate(jsonl(h, []), now);
  assert.deepEqual(empty.months, []); assert.equal(activitySummary(empty).monthCells, null);
  assert.equal(activitySummary(parseAggregate(jsonl(), NOW)).monthCells, null);
});
