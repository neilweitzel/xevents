import test from "node:test";
import assert from "node:assert/strict";
import {CODES, SCHEMA, ACTIVITY_SCHEMA, MAX_BYTES, parseAggregate, loadAggregate, selection, exportSelection, activitySummary} from "../aggregate.mjs";

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
  for (const [floor, label] of [[0, "Fewer than 25"], [25, "25–49"], [50, "50–74"], [10000, "10,000–10,024"]]) {
    const d = parseAggregate(jsonl({...header(), schema_version: ACTIVITY_SCHEMA,
      assessed_claims_floor: floor}), NOW);
    assert.equal(activitySummary(d).assessed, label);
    assert.equal(activitySummary(d).published, 14);
    assert.equal(activitySummary(d).cells, 2);
    assert.equal(exportSelection(d, selection(d, "", 1)).contract_version, ACTIVITY_SCHEMA);
  }
  for (const value of [-25, 1, 24, 26, 25.1, 10025, true, "25", null])
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
