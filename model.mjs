/**
 * Synthetic view-1 fixture and pure presentation logic.
 * Not an ingestion schema, production export contract, or privacy gate.
 * Every count is invented. Suppressed cells contain null, never hidden counts.
 */
export const FIXTURE_ID = "synthetic-sector-preview-v1";
export const DISCLAIMER = "Synthetic test data. No real incidents or live source data.";
export const WEEKS = Object.freeze([
  "2026-06-29", "2026-07-06", "2026-07-13", "2026-07-20",
  "2026-07-27", "2026-08-03", "2026-08-10", "2026-08-17",
  "2026-08-24", "2026-08-31", "2026-09-07", "2026-09-14",
]);
const samples = [
  ["31-33", "Manufacturing", [17, 20, 19, 24, 23, 28, 26, 31, 29, 35, 38, 42]],
  ["62", "Healthcare and social assistance", [22, 24, 21, 27, 24, 25, 29, 30, 31, 33, 29, 36]],
  ["54", "Professional and technical services", [10, 12, 11, 14, 12, 16, 15, 19, 18, 21, 23, 25]],
  ["44-45", "Retail trade", [8, 9, 7, 10, 9, 12, 11, 15, 13, 14, 13, 16]],
  ["61", "Educational services", [null, 5, null, 7, 6, 8, 5, 9, 7, 10, 8, 9]],
  ["48-49", "Transportation and warehousing", [5, null, null, 6, null, 7, null, 8, 6, 7, 5, null]],
];
export const SECTORS = Object.freeze(samples.map(([id, name, counts]) => Object.freeze({
  id, name, counts: Object.freeze(counts),
})));

export function validateFixture(sectors = SECTORS) {
  if (!Array.isArray(sectors) || !sectors.length) throw new Error("Invalid fixture");
  const ids = new Set();
  for (const sector of sectors) {
    if (Object.keys(sector).sort().join() !== "counts,id,name" ||
        typeof sector.id !== "string" || !/^\d{2}(-\d{2})?$/.test(sector.id) ||
        typeof sector.name !== "string" || !sector.name ||
        ids.has(sector.id) || !Array.isArray(sector.counts) ||
        sector.counts.length !== WEEKS.length ||
        sector.counts.some(n => n !== null && (!Number.isSafeInteger(n) || n < 5))) {
      throw new Error("Invalid fixture");
    }
    ids.add(sector.id);
  }
  return true;
}
validateFixture();

export function selectWeeks(end = WEEKS.length - 1, window = 12) {
  if (!Number.isInteger(end) || end < 0 || end >= WEEKS.length ||
      ![1, 4, 12].includes(window)) throw new Error("Invalid window");
  return Array.from({length: Math.min(window, end + 1)}, (_, i) =>
    Math.max(0, end - window + 1) + i);
}

export function filterSectors(query = "", sort = "latest-desc", end = WEEKS.length - 1) {
  if (typeof query !== "string" || !["latest-desc", "latest-asc", "name"].includes(sort)) {
    throw new Error("Invalid filter");
  }
  selectWeeks(end, 1);
  const term = query.trim().toLowerCase();
  return SECTORS.filter(s => `${s.name} ${s.id}`.toLowerCase().includes(term)).sort((a, b) => {
    if (sort === "name") return a.name.localeCompare(b.name, "en");
    const x = a.counts[end], y = b.counts[end];
    if (x === null) return y === null ? a.name.localeCompare(b.name, "en") : 1;
    if (y === null) return -1;
    return (sort === "latest-desc" ? y - x : x - y) || a.name.localeCompare(b.name, "en");
  });
}

export function totalFor(sectors, indices) {
  let visible = 0, suppressed = 0;
  for (const sector of sectors) for (const i of indices) {
    if (sector.counts[i] === null) suppressed++;
    else visible += sector.counts[i];
  }
  return {visible, suppressed};
}

export function weeklySeries(sectors, indices) {
  return indices.map(i => ({week: WEEKS[i], ...totalFor(sectors, [i])}));
}

export function activity(sector, end) {
  // Illustrative only: compare with the four preceding complete fixture cells.
  const baseline = sector.counts.slice(Math.max(0, end - 4), end);
  const latest = sector.counts[end];
  if (latest === null || baseline.length < 4 || baseline.some(n => n === null)) {
    return {label: "Insufficient data", key: "insufficient", ratio: null};
  }
  const ratio = latest / (baseline.reduce((a, b) => a + b, 0) / 4);
  return {
    label: ratio >= 1.25 ? "High" : ratio >= 1.1 ? "Elevated" : "Low",
    key: ratio >= 1.25 ? "high" : ratio >= 1.1 ? "elevated" : "low",
    ratio,
  };
}

export function changeFor(sector, end) {
  const current = sector.counts[end], prior = sector.counts[end - 1];
  return current === null || prior == null ? null : current - prior;
}

export function makeExport(sectors, indices) {
  if (!sectors.every(s => SECTORS.includes(s)) || !indices.length ||
      indices.some((i, n) => !Number.isInteger(i) || i < 0 || i >= WEEKS.length ||
        (n > 0 && i !== indices[n - 1] + 1))) throw new Error("Invalid export selection");
  return {
    schema: "xevents-synthetic-preview/v1",
    synthetic: true,
    publication_authorized: false,
    fixture_id: FIXTURE_ID,
    disclaimer: DISCLAIMER,
    view: "sector-exposure",
    window: {start: WEEKS[indices[0]], end: WEEKS[indices.at(-1)], unit: "week-start"},
    cell_policy: "null means insufficient data; never interpret as zero",
    activity_model: "illustrative-only-v1; not approved production scoring",
    sectors: sectors.map(s => ({
      sector_code: s.id,
      sector_label: s.name,
      weekly_claims: indices.map(i => ({week_start: WEEKS[i], count: s.counts[i]})),
    })),
  };
}

export function totalLabel(total) {
  if (total.visible === 0 && total.suppressed > 0) return "Withheld";
  return `${total.suppressed ? "≥ " : ""}${total.visible.toLocaleString("en-US")}`;
}

export function dateLabel(iso, long = false) {
  return new Intl.DateTimeFormat("en-US", {
    month: long ? "long" : "short", day: "numeric",
    ...(long ? {year: "numeric"} : {}), timeZone: "UTC",
  }).format(new Date(`${iso}T00:00:00Z`));
}
