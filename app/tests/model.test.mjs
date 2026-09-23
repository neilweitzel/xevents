import test from "node:test";
import assert from "node:assert/strict";
import {
  SECTORS, WEEKS, validateFixture, selectWeeks, filterSectors,
  totalFor, weeklySeries, activity, changeFor, makeExport, dateLabel, totalLabel,
} from "../model.mjs";

test("fixture is explicit, deterministic, closed and immutable", () => {
  assert.equal(validateFixture(), true);
  assert.equal(SECTORS.length, 6);
  assert.equal(WEEKS.length, 12);
  assert.throws(() => SECTORS[0].counts.push(7));
});
test("malformed fixtures and raw subthreshold counts are rejected", () => {
  for (const count of [0, 1, 4, -1, 5.1, NaN, Infinity, "5", true]) {
    assert.throws(() => validateFixture([{...SECTORS[0], counts: [count, ...SECTORS[0].counts.slice(1)]}]));
  }
  assert.throws(() => validateFixture([{...SECTORS[0], victim: "not permitted"}]));
  assert.throws(() => validateFixture([SECTORS[0], SECTORS[0]]));
  assert.throws(() => validateFixture([]));
});
test("date windows are inclusive and clamp at available history", () => {
  assert.deepEqual(selectWeeks(11, 4), [8, 9, 10, 11]);
  assert.deepEqual(selectWeeks(1, 12), [0, 1]);
  assert.deepEqual(selectWeeks(11, 1), [11]);
  for (const [end, n] of [[-1, 4], [12, 4], [1.1, 4], [11, 2]]) assert.throws(() => selectWeeks(end, n));
});
test("search matches labels and codes without interpreting markup", () => {
  assert.equal(filterSectors("MANUF")[0].id, "31-33");
  assert.equal(filterSectors(" 62 ")[0].name, "Healthcare and social assistance");
  assert.deepEqual(filterSectors("<script>"), []);
  assert.deepEqual(filterSectors("no-such-sector"), []);
});
test("numeric sorting keeps withheld cells last in either direction", () => {
  assert.equal(filterSectors("", "latest-desc")[0].id, "31-33");
  assert.equal(filterSectors("", "latest-asc")[0].id, "61");
  assert.equal(filterSectors("", "latest-asc").at(-1).id, "48-49");
  assert.equal(filterSectors("", "name")[0].id, "61");
  assert.throws(() => filterSectors("", "invalid"));
});
test("partial totals preserve missing cells instead of manufacturing zeros", () => {
  assert.deepEqual(totalFor(SECTORS, [11]), {visible: 128, suppressed: 1});
  assert.deepEqual(totalFor([SECTORS.at(-1)], [11]), {visible: 0, suppressed: 1});
  assert.deepEqual(totalFor([], [11]), {visible: 0, suppressed: 0});
  assert.deepEqual(weeklySeries(SECTORS, [11]), [{week: "2026-09-14", visible: 128, suppressed: 1}]);
});
test("illustrative activity does not invent a baseline", () => {
  assert.equal(activity(SECTORS[0], 11).key, "high");
  assert.equal(activity(SECTORS[1], 11).key, "elevated");
  assert.equal(activity(SECTORS[4], 11).key, "low");
  assert.equal(activity(SECTORS[0], 0).key, "insufficient");
  assert.equal(activity(SECTORS.at(-1), 11).key, "insufficient");
  assert.equal(activity(SECTORS[4], 4).key, "insufficient");
});
test("all-withheld totals are never presented as zero activity", () => {
  assert.equal(totalLabel({visible: 0, suppressed: 1}), "Withheld");
  assert.equal(totalLabel({visible: 128, suppressed: 1}), "≥ 128");
  assert.equal(totalLabel({visible: 0, suppressed: 0}), "0");
  assert.equal(totalLabel({visible: 1114, suppressed: 0}), "1,114");
});
test("week change requires both observed fixture cells", () => {
  assert.equal(changeFor(SECTORS[0], 11), 4);
  assert.equal(changeFor(SECTORS.at(-1), 11), null);
  assert.equal(changeFor(SECTORS[0], 0), null);
});
test("export exactly matches selection and retains synthetic labeling", () => {
  const value = makeExport([SECTORS[0]], [8, 9, 10, 11]);
  assert.equal(value.synthetic, true);
  assert.equal(value.publication_authorized, false);
  assert.equal(value.sectors.length, 1);
  assert.equal(value.sectors[0].weekly_claims.length, 4);
  assert.equal(value.sectors[0].weekly_claims.at(-1).count, 42);
  assert.equal(value.window.start, "2026-08-24");
  assert.match(value.disclaimer, /Synthetic/);
});
test("withheld and empty exports never expose hidden raw counts", () => {
  assert.equal(makeExport([SECTORS.at(-1)], [11]).sectors[0].weekly_claims[0].count, null);
  assert.deepEqual(makeExport([], [11]).sectors, []);
  assert.throws(() => makeExport([{...SECTORS[0]}], [11]));
  assert.throws(() => makeExport(SECTORS, []));
  assert.throws(() => makeExport(SECTORS, [2, 1]));
  assert.throws(() => makeExport(SECTORS, [1, 3]));
  assert.throws(() => makeExport(SECTORS, [12]));
});
test("labels use UTC so browser locale does not shift reporting dates", () => {
  assert.equal(dateLabel("2026-09-14"), "Sep 14");
  assert.equal(dateLabel("2026-09-14", true), "September 14, 2026");
});
