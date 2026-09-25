/** Closed RC display reader. Not a signing verifier or publication authority. */
export const SCHEMA = "xevents-view1-display/v1";
export const ACTIVITY_SCHEMA = "xevents-view1-display/v2";
export const RUN_SCHEMA = "xevents-view1-display/v3";
export const ROLLUP_SCHEMA = "xevents-view1-display/v4";
export const MAX_WEEKS = 104, MAX_MONTHS = 25;
export const MAX_BYTES = 1024 * 1024;
export const LABELS = Object.freeze({
  "11": "Agriculture, forestry and fishing", "21": "Mining and extraction",
  "22": "Utilities", "23": "Construction", "31-33": "Manufacturing",
  "42": "Wholesale trade", "44-45": "Retail trade",
  "48-49": "Transportation and warehousing", "51": "Information",
  "52": "Finance and insurance", "53": "Real estate and leasing",
  "54": "Professional and technical services", "55": "Company management",
  "56": "Administrative support and waste services", "61": "Educational services",
  "62": "Healthcare and social assistance", "71": "Arts and recreation",
  "72": "Accommodation and food services", "81": "Other services",
  "92": "Public administration", "unclassified": "Unclassified",
});
export const CODES = Object.freeze([
  "11", "21", "22", "23", "31-33", "42", "44-45", "48-49", "51", "52",
  "53", "54", "55", "56", "61", "62", "71", "72", "81", "92", "unclassified",
]);
const require = condition => { if (!condition) throw new Error("Invalid aggregate"); };
const keys = (value, expected) => require(value && !Array.isArray(value) &&
  typeof value === "object" && Object.keys(value).sort().join() === [...expected].sort().join());
const canonical = value => value && typeof value === "object" ?
  `{${Object.keys(value).sort().map(k => `${JSON.stringify(k)}:${canonical(value[k])}`).join(",")}}` :
  JSON.stringify(value);
const DAY = 86400000;
function monday(value) {
  require(typeof value === "string" && /^\d{4}-\d{2}-\d{2}$/.test(value));
  const date = new Date(`${value}T00:00:00Z`);
  require(Number.isFinite(+date) && date.toISOString().slice(0, 10) === value &&
    date.getUTCDay() === 1);
  return +date;
}
function monthOf(value) {
  require(typeof value === "string" && /^\d{4}-(?:0[1-9]|1[0-2])$/.test(value));
  return value;
}
function clock(value) {
  require(typeof value === "string" && /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(?:\.\d{1,6})?Z$/.test(value));
  const date = new Date(value);
  require(Number.isFinite(+date) && date.toISOString().slice(0, 19) === value.slice(0, 19));
  return +date;
}
export function parseAggregate(text, now = Date.now()) {
  require(typeof text === "string" && new TextEncoder().encode(text).length <= MAX_BYTES &&
    text.endsWith("\n") && Number.isFinite(now));
  const lines = text.slice(0, -1).split("\n");
  require(lines.length <= 1 + (MAX_WEEKS + MAX_MONTHS) * CODES.length);
  const values = lines.map(line => {
    const value = JSON.parse(line);
    // Canonical spelling rejects duplicate keys, escapes and nonfinite forms.
    require(canonical(value) === line);
    return value;
  });
  const header = values[0], rows = values.slice(1);
  const rollup = header?.schema_version === ROLLUP_SCHEMA;
  const run = rollup || header?.schema_version === RUN_SCHEMA;
  const activity = run || header?.schema_version === ACTIVITY_SCHEMA;
  keys(header, ["file_purpose", "schema_version", "release_state", "generated_at",
    "coverage", "time_basis", "privacy_floor", ...(activity ? ["assessed_claims_floor"] : []),
    ...(run ? ["evaluated_at"] : [])]);
  require(header.file_purpose === "sector_aggregate" &&
    [SCHEMA, ACTIVITY_SCHEMA, RUN_SCHEMA, ROLLUP_SCHEMA].includes(header.schema_version) &&
    header.release_state === "released" && header.coverage === "recent_only" &&
    header.time_basis === "retrieved_at" && header.privacy_floor === 5);
  if (activity) require(Number.isSafeInteger(header.assessed_claims_floor) &&
    header.assessed_claims_floor >= 0 && header.assessed_claims_floor <= 10000 &&
    header.assessed_claims_floor % 25 === 0);
  const generated = clock(header.generated_at);
  require(generated <= now + 5 * 60000);
  if (run) {
    // Whole-second completion of the release run; never earlier than its capture.
    require(typeof header.evaluated_at === "string" &&
      /^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$/.test(header.evaluated_at));
    const evaluated = clock(header.evaluated_at);
    require(evaluated >= generated && evaluated <= now + 5 * 60000);
  }
  const seen = new Set(), weeks = new Set(), monthSet = new Set();
  const weekRows = [], monthRows = [];
  const count = value => require(value === null ||
    (Number.isSafeInteger(value) && value >= 5 && value <= 1000000));
  for (const row of rows) {
    // v4 adds closed sector-month rows (ADR 0026); earlier versions stay weekly only.
    const monthly = rollup && row && typeof row === "object" && "month" in row;
    keys(row, ["sector", monthly ? "month" : "week_start", "claim_count"]);
    require(CODES.includes(row.sector));
    count(row.claim_count);
    if (monthly) {
      monthOf(row.month);
      const key = `${row.sector}/${row.month}`;
      require(!seen.has(key)); seen.add(key); monthSet.add(row.month); monthRows.push(row);
    } else {
      require(monday(row.week_start) <= generated);
      const key = `${row.sector}/${row.week_start}`;
      require(!seen.has(key)); seen.add(key); weeks.add(row.week_start); weekRows.push(row);
    }
  }
  const ordered = [...weeks].sort();
  const sum = list => list.reduce((n, row) => n + (row.claim_count ?? 0), 0);
  if (activity) require(sum(weekRows) < header.assessed_claims_floor + 25 &&
    sum(monthRows) < header.assessed_claims_floor + 25);
  require(weekRows.length === ordered.length * CODES.length && ordered.length <= MAX_WEEKS);
  ordered.forEach((w, i) => require(!i || monday(w) - monday(ordered[i - 1]) === 7 * DAY));
  // A month holds exactly the weeks whose Monday falls in it, so the two views nest.
  const months = [...new Set(ordered.map(w => w.slice(0, 7)))];
  if (rollup) {
    require(months.join() === [...monthSet].sort().join() &&
      monthRows.length === months.length * CODES.length && months.length <= MAX_MONTHS);
    const cell = new Map(weekRows.map(r => [`${r.sector}/${r.week_start}`, r.claim_count]));
    for (const row of monthRows) {
      const inner = ordered.filter(w => w.startsWith(row.month)).map(w => cell.get(`${row.sector}/${w}`));
      const shown = inner.reduce((n, v) => n + (v ?? 0), 0), hidden = inner.filter(v => v === null).length;
      // Complementary suppression: no month may expose withheld weekly cells.
      if (!hidden) require(row.claim_count === shown);
      else require(row.claim_count === null || row.claim_count - shown >= 5);
    }
  } else require(!monthSet.size);
  const frozenRows = Object.freeze(weekRows.map(row => Object.freeze({...row})));
  const frozenMonths = Object.freeze(monthRows.map(row => Object.freeze({...row})));
  const shownMonths = rollup ? months : [];
  return Object.freeze({
    header: Object.freeze({...header}), rows: frozenRows, weeks: Object.freeze(ordered),
    monthRows: frozenMonths, months: Object.freeze(shownMonths),
    stale: now - generated > 14 * DAY,
    sectors: Object.freeze(CODES.map(code => Object.freeze({id: code, name: LABELS[code],
      counts: Object.freeze(ordered.map(w => weekRows.find(r => r.sector === code && r.week_start === w).claim_count)),
      monthCounts: Object.freeze(shownMonths.map(m => monthRows.find(r => r.sector === code && r.month === m).claim_count)),
    }))),
  });
}
export function activitySummary(dataset) {
  if (!dataset) return null;
  const floor = dataset.header.assessed_claims_floor;
  return Object.freeze({
    assessed: floor === undefined ? "Not reported" : floor === 0 ? "Fewer than 25" :
      `${floor.toLocaleString("en-US")}–${(floor + 24).toLocaleString("en-US")}`,
    published: dataset.rows.reduce((n, row) => n + (row.claim_count ?? 0), 0),
    cells: dataset.rows.filter(row => row.claim_count !== null).length,
    monthCells: dataset.months.length ?
      dataset.monthRows.filter(row => row.claim_count !== null).length : null,
    captured: dataset.header.generated_at, lastRun: dataset.header.evaluated_at ?? null,
    stale: dataset.stale,
  });
}
export async function loadAggregate(fetcher = fetch, now = Date.now()) {
  try {
    const response = await fetcher("./data/aggregates/view1.jsonl", {
      credentials: "omit", mode: "same-origin", redirect: "error", cache: "no-store",
      signal: AbortSignal.timeout(10000),
    });
    if (response.status === 404) return {state: "waiting"};
    require(response.ok && !response.redirected && response.body);
    const reader = response.body.getReader(), chunks = [];
    let size = 0;
    try {
      while (true) {
        const {done, value} = await reader.read();
        if (done) break;
        size += value.byteLength;
        require(size <= MAX_BYTES);
        chunks.push(value);
      }
    } finally { await reader.cancel(); }
    const raw = new Uint8Array(size);
    let offset = 0;
    for (const chunk of chunks) { raw.set(chunk, offset); offset += chunk.byteLength; }
    const dataset = parseAggregate(new TextDecoder("utf-8", {fatal: true}).decode(raw), now);
    return {state: dataset.rows.length ? "ready" : "empty", dataset};
  } catch { return {state: "unavailable"}; }
}
export const WINDOWS = Object.freeze({week: Object.freeze([1, 4, 12]), month: Object.freeze([1, 3, 12])});
export function selection(dataset, query, end, length = 12, sort = "name", period = "week") {
  require(Object.hasOwn(WINDOWS, period));
  const periods = period === "month" ? dataset.months : dataset.weeks;
  const field = period === "month" ? "month" : "week_start";
  const source = period === "month" ? dataset.monthRows : dataset.rows;
  require(typeof query === "string" && Number.isInteger(end) && end >= 0 &&
    end < periods.length && WINDOWS[period].includes(length) &&
    ["name", "latest-desc", "latest-asc"].includes(sort));
  const chosen = periods.slice(Math.max(0, end - length + 1), end + 1);
  const term = query.trim().toLowerCase();
  const counts = s => period === "month" ? s.monthCounts : s.counts;
  const sectors = dataset.sectors.filter(s => `${s.id} ${s.name}`.toLowerCase().includes(term));
  sectors.sort((a, b) => {
    if (sort === "name") return a.name.localeCompare(b.name, "en");
    const x = counts(a)[end], y = counts(b)[end];
    return x === null ? y === null ? a.name.localeCompare(b.name, "en") : 1 :
      y === null ? -1 : (sort === "latest-desc" ? y - x : x - y);
  });
  const ids = new Set(sectors.map(s => s.id));
  const rows = source.filter(row => ids.has(row.sector) && chosen.includes(row[field]));
  return {sectors, period, periods: chosen, weeks: period === "week" ? chosen : [], rows};
}
export function exportSelection(dataset, selected) {
  const monthly = selected.period === "month";
  require(selected.rows.every(row => (monthly ? dataset.monthRows : dataset.rows).includes(row)));
  return {
    contract_version: dataset.header.schema_version, dataset: "xevents", synthetic: false,
    framing: "Public claims about cyber incidents, not verified breaches. Names are excluded.",
    license: "CC BY 4.0", attribution: "RansomLook, CC BY 4.0; https://www.ransomlook.io/",
    generated_at: dataset.header.generated_at, coverage: dataset.header.coverage,
    time_basis: dataset.header.time_basis, privacy_floor: 5,
    ...(monthly ? {period: "month"} : {}), stale: dataset.stale, rows: selected.rows,
  };
}
