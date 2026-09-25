/** Closed RC display reader. Not a signing verifier or publication authority. */
export const SCHEMA = "xevents-view1-display/v1";
export const ACTIVITY_SCHEMA = "xevents-view1-display/v2";
export const RUN_SCHEMA = "xevents-view1-display/v3";
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
  require(lines.length <= 1 + 104 * CODES.length);
  const values = lines.map(line => {
    const value = JSON.parse(line);
    // Canonical spelling rejects duplicate keys, escapes and nonfinite forms.
    require(canonical(value) === line);
    return value;
  });
  const header = values[0], rows = values.slice(1);
  const run = header?.schema_version === RUN_SCHEMA;
  const activity = run || header?.schema_version === ACTIVITY_SCHEMA;
  keys(header, ["file_purpose", "schema_version", "release_state", "generated_at",
    "coverage", "time_basis", "privacy_floor", ...(activity ? ["assessed_claims_floor"] : []),
    ...(run ? ["evaluated_at"] : [])]);
  require(header.file_purpose === "sector_aggregate" &&
    [SCHEMA, ACTIVITY_SCHEMA, RUN_SCHEMA].includes(header.schema_version) &&
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
  const seen = new Set(), weeks = new Set();
  for (const row of rows) {
    keys(row, ["sector", "week_start", "claim_count"]);
    require(CODES.includes(row.sector));
    require(monday(row.week_start) <= generated);
    require(row.claim_count === null ||
      (Number.isSafeInteger(row.claim_count) && row.claim_count >= 5 && row.claim_count <= 1000000));
    const key = `${row.sector}/${row.week_start}`;
    require(!seen.has(key));
    seen.add(key); weeks.add(row.week_start);
  }
  const ordered = [...weeks].sort();
  if (activity) require(rows.reduce((n, row) => n + (row.claim_count ?? 0), 0) <
    header.assessed_claims_floor + 25);
  require(rows.length === ordered.length * CODES.length);
  ordered.forEach((w, i) => require(!i || monday(w) - monday(ordered[i - 1]) === 7 * DAY));
  const frozenRows = Object.freeze(rows.map(row => Object.freeze({...row})));
  return Object.freeze({
    header: Object.freeze({...header}), rows: frozenRows, weeks: Object.freeze(ordered),
    stale: now - generated > 14 * DAY,
    sectors: Object.freeze(CODES.map(code => Object.freeze({id: code, name: LABELS[code],
      counts: Object.freeze(ordered.map(w => rows.find(r => r.sector === code && r.week_start === w).claim_count)),
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
export function selection(dataset, query, end, length = 12, sort = "name") {
  require(typeof query === "string" && Number.isInteger(end) && end >= 0 &&
    end < dataset.weeks.length && [1, 4, 12].includes(length) &&
    ["name", "latest-desc", "latest-asc"].includes(sort));
  const weeks = dataset.weeks.slice(Math.max(0, end - length + 1), end + 1);
  const term = query.trim().toLowerCase();
  const sectors = dataset.sectors.filter(s => `${s.id} ${s.name}`.toLowerCase().includes(term));
  sectors.sort((a, b) => {
    if (sort === "name") return a.name.localeCompare(b.name, "en");
    const x = a.counts[end], y = b.counts[end];
    return x === null ? y === null ? a.name.localeCompare(b.name, "en") : 1 :
      y === null ? -1 : (sort === "latest-desc" ? y - x : x - y);
  });
  const ids = new Set(sectors.map(s => s.id));
  const rows = dataset.rows.filter(row => ids.has(row.sector) && weeks.includes(row.week_start));
  return {sectors, weeks, rows};
}
export function exportSelection(dataset, selected) {
  require(selected.rows.every(row => dataset.rows.includes(row)));
  return {
    contract_version: dataset.header.schema_version, dataset: "xevents", synthetic: false,
    framing: "Public claims about cyber incidents, not verified breaches. Names are excluded.",
    license: "CC BY 4.0", attribution: "RansomLook, CC BY 4.0; https://www.ransomlook.io/",
    generated_at: dataset.header.generated_at, coverage: dataset.header.coverage,
    time_basis: dataset.header.time_basis, privacy_floor: 5,
    stale: dataset.stale, rows: selected.rows,
  };
}
