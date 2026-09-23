import {
  SECTORS, WEEKS, FIXTURE_ID, filterSectors, selectWeeks, totalFor,
  weeklySeries, activity, changeFor, makeExport, dateLabel, totalLabel,
} from "./model.mjs";

const state = {query: "", sort: "latest-desc", end: WEEKS.length - 1, window: 12};
const $ = selector => document.querySelector(selector);
$(".sidebar-bottom strong").textContent = "Synthetic only";
$(".sidebar-bottom p").textContent = "No source data is used in this demo. Public publishing is disabled.";
$(".sidebar-bottom .version").textContent = "SYNTHETIC DEMO · VIEW 1";
$(".preview-label").textContent = "Synthetic preview";
$(".sample-notice").innerHTML = "<strong>Test data, not threat intelligence.</strong><span>All counts are invented. No real incidents are represented.</span>";
$("footer span:last-child").textContent = "Synthetic fixture · No live data";
const escape = value => String(value).replace(/[&<>"']/g, c =>
  ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const number = value => value.toLocaleString("en-US");
let route = {page: "overview", sector: null};
let theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";

function applyTheme() {
  document.documentElement.dataset.theme = theme;
  $("#theme").textContent = theme === "dark" ? "Light mode" : "Dark mode";
  $("#theme").setAttribute("aria-label", `Switch to ${theme === "dark" ? "light" : "dark"} mode`);
}
$("#theme").addEventListener("click", () => { theme = theme === "dark" ? "light" : "dark"; applyTheme(); });
applyTheme();
document.querySelector(".skip").addEventListener("click", event => {
  event.preventDefault(); $("#main").focus(); $("#main").scrollTop = 0;
});

function currentRows() {
  return route.sector ? [route.sector] : filterSectors(state.query, state.sort, state.end);
}
function indices() { return selectWeeks(state.end, state.window); }
function countLabel(n) { return n === null ? "Insufficient data" : number(n); }
function badge(sector) {
  const band = activity(sector, state.end);
  return `<span class="band ${band.key}">${band.label}</span>`;
}
function changeLabel(sector) {
  const change = changeFor(sector, state.end);
  return change === null ? '<span class="muted">Not comparable</span>' :
    change === 0 ? '<span class="muted">No change</span>' :
    `<span class="delta">${change > 0 ? "↑" : "↓"} ${number(Math.abs(change))}<span class="sr-only"> ${change > 0 ? "more" : "fewer"} synthetic claims</span></span>`;
}
function spark(sector) {
  const cells = indices().map(i => sector.counts[i]);
  const max = Math.max(1, ...cells.filter(n => n !== null));
  return `<div class="spark" role="img" aria-label="${escape(sector.name)}: ${cells.map(countLabel).join(", ")}">
    ${cells.map(n => `<span class="${n === null ? "missing" : ""}" style="height:${n === null ? 12 : Math.max(8, n / max * 100)}%"></span>`).join("")}
  </div>`;
}
function exportButton() {
  return '<button class="primary export" data-testid="button-export">Export JSON <span aria-hidden="true">↓</span></button>';
}
function controls(includeSearch = true) {
  return `<section class="filters" aria-label="Research filters">
    ${includeSearch ? '<label class="search-field"><span>Find a sector</span><input id="search" data-testid="input-search" type="search" maxlength="100" placeholder="Search sector or code" autocomplete="off" value="' + escape(state.query) + '"></label>' : ""}
    <label><span>Reporting week</span><select id="week" data-testid="select-week">${WEEKS.map((w, i) => `<option value="${i}" ${i === state.end ? "selected" : ""}>${dateLabel(w, true)}</option>`).reverse().join("")}</select></label>
    <label><span>Lookback</span><select id="window" data-testid="select-window">${[12, 4, 1].map(n => `<option value="${n}" ${n === state.window ? "selected" : ""}>${n === 1 ? "Selected week" : `${n} weeks`}</option>`).join("")}</select></label>
    <button id="reset" class="quiet reset" data-testid="button-reset">Reset filters</button>
  </section>`;
}
function title(kicker, heading, description, extra = "") {
  return `<section class="page-heading"><div><p class="eyebrow">${kicker}</p><h1>${heading}</h1><p class="lede">${description}</p></div><div class="heading-actions">${extra}${exportButton()}</div></section>`;
}
function graph(rows, selected) {
  const series = weeklySeries(rows, selected);
  const max = Math.max(1, ...series.map(r => r.visible));
  const ticks = [0, 1, 2, 3].map(i => Math.ceil(max / 3) * i);
  const scale = ticks[3] || 1;
  return `<section class="panel trend-panel" aria-labelledby="trend-title">
    <div class="panel-heading"><div><h2 id="trend-title">Weekly claim volume</h2><p>Visible synthetic claims${series.some(r => r.suppressed) ? "; some cells are withheld." : "."}</p></div><span class="chart-key"><i></i> Invented counts</span></div>
    <div class="chart-wrap"><div class="y-axis" aria-hidden="true">${ticks.reverse().map(t => `<span>${t}</span>`).join("")}</div>
    <div class="plot" role="img" aria-label="Synthetic weekly claim volume. Exact visible values follow in the weekly data table.">
      <div class="gridlines" aria-hidden="true"><i></i><i></i><i></i><i></i></div>
      ${series.map((row, i) => `<div class="bar-slot" style="--bar-height:${row.visible / scale * 100}%"><span class="bar-value">${row.visible === 0 && row.suppressed ? "—" : totalLabel(row).replace(" ", "")}</span>
        <div class="bar ${i === series.length - 1 ? "current" : ""} ${row.suppressed ? "partial" : ""}" style="height:${row.visible / scale * 100}%"></div>
        <span class="x-label">${dateLabel(row.week)}</span></div>`).join("")}
    </div></div>
    <div class="chart-footnote"><span>${dateLabel(series[0].week)} to ${dateLabel(series.at(-1).week)} · ${series.length} ${series.length === 1 ? "week" : "weeks"}</span><span>≥ indicates a partial total</span></div>
    <details class="data-details"><summary data-testid="toggle-weekly-data">Show weekly values</summary>
      <table><caption class="sr-only">Weekly synthetic counts for the current selection</caption><thead><tr><th scope="col">Week starting</th><th scope="col">Visible claims</th><th scope="col">Withheld cells</th></tr></thead><tbody>
      ${series.map(r => `<tr><th scope="row">${dateLabel(r.week, true)}</th><td>${totalLabel(r)}</td><td>${r.suppressed}</td></tr>`).join("")}
      </tbody></table>
    </details>
  </section>`;
}
function metrics(rows, selected) {
  const totals = totalFor(rows, selected), latest = totalFor(rows, [state.end]);
  return `<section class="metrics" aria-label="Selection summary">
    <div><span class="metric-label">Visible synthetic claims</span><strong data-testid="metric-total">${totalLabel(totals)}</strong><span>${selected.length}-week selection · not real incidents</span></div>
    <div><span class="metric-label">Selected week</span><strong data-testid="metric-latest">${totalLabel(latest)}</strong><span>Week starting ${dateLabel(WEEKS[state.end])}</span></div>
    <div><span class="metric-label">Sectors in view</span><strong data-testid="metric-sectors">${rows.length}<small> / ${SECTORS.length}</small></strong><span>${totals.suppressed} sector-week ${totals.suppressed === 1 ? "cell" : "cells"} withheld</span></div>
  </section>`;
}
function table(rows) {
  return `<section class="panel sector-panel"><div class="panel-heading"><div><h2>Sector activity</h2><p>Illustrative bands compare the selected week with its prior four weeks.</p></div><span class="pill">View 1</span></div>
    <div class="table-scroll"><table class="sectors"><caption class="sr-only">Synthetic sector activity for the selected week</caption>
      <thead><tr><th scope="col" aria-sort="${state.sort === "name" ? "ascending" : "none"}"><button id="sort-name" data-testid="sort-name">Sector${state.sort === "name" ? " A–Z" : ""}</button></th><th scope="col">Demo activity</th>
        <th scope="col" aria-sort="${state.sort === "latest-desc" ? "descending" : state.sort === "latest-asc" ? "ascending" : "none"}"><button id="sort-count" data-testid="sort-count">Claims${state.sort === "latest-asc" ? " ↑" : state.sort === "latest-desc" ? " ↓" : ""}</button></th><th scope="col">Week change</th><th scope="col">Trend</th></tr></thead>
      <tbody>${rows.map(s => `<tr data-testid="row-sector-${s.id}"><th scope="row"><a class="sector-link" href="#/sector/${s.id}" data-testid="link-sector-${s.id}">${s.name}<span>SECTOR ${s.id}</span></a></th><td>${badge(s)}</td><td class="numeric">${s.counts[state.end] === null ? '<span class="muted cell-withheld">Withheld</span>' : number(s.counts[state.end])}</td><td>${changeLabel(s)}</td><td>${spark(s)}</td></tr>`).join("")}</tbody>
    </table></div><div class="table-footnote">A withheld cell means insufficient data, not zero activity. All values are synthetic.</div>
  </section>`;
}
function empty() {
  return `<section class="empty"><p class="eyebrow">NO MATCHING SECTORS</p><h2>Try a broader search</h2><p>Search by sector name or code, or clear your filters to see all six sample sectors.</p><button class="primary clear-search" data-testid="button-clear-search">Clear search</button></section>`;
}
function detailNotes(sector) {
  return `<section class="detail-notes"><article class="panel"><p class="eyebrow">READING THIS SECTOR</p><h2>${badge(sector)} <span class="plain">illustrative activity</span></h2><p>This band is a demonstration of change in invented listing-claim counts. It is not a risk rating, a confidence score or a finding about this industry.</p><a href="#/methodology">Read the methodology →</a></article><article class="panel"><p class="eyebrow">EVIDENCE STATUS</p><h2>No source evidence</h2><p>These values were authored for interface testing. No source observations, victim acknowledgements or evidence receipts back this fixture.</p><p class="muted">Real-data claims require the separate ingestion and publication pipeline.</p></article></section>`;
}
function renderResults() {
  const rows = currentRows(), selected = indices();
  $("#results").innerHTML = rows.length ?
    metrics(rows, selected) + graph(rows, selected) + (route.sector ? detailNotes(route.sector) : table(rows)) : empty();
  $("#result-status").textContent = `${rows.length} ${rows.length === 1 ? "sector" : "sectors"} shown; ${selected.length} ${selected.length === 1 ? "week" : "weeks"} selected.`;
  $(".clear-search")?.addEventListener("click", () => { state.query = ""; $("#search").value = ""; renderResults(); $("#search").focus(); });
  $("#sort-name")?.addEventListener("click", () => { state.sort = "name"; renderResults(); $("#sort-name").focus(); });
  $("#sort-count")?.addEventListener("click", () => { state.sort = state.sort === "latest-desc" ? "latest-asc" : "latest-desc"; renderResults(); $("#sort-count").focus(); });
}
function bindFilters(callback) {
  $("#search")?.addEventListener("input", event => { state.query = event.target.value; callback(); });
  $("#week")?.addEventListener("change", event => { state.end = Number(event.target.value); callback(); });
  $("#window")?.addEventListener("change", event => { state.window = Number(event.target.value); callback(); });
  $("#reset")?.addEventListener("click", () => {
    Object.assign(state, {query: "", sort: "latest-desc", end: WEEKS.length - 1, window: 12});
    render(false); $("#reset").focus();
  });
}
function researchView() {
  const sector = route.sector;
  $("#view").innerHTML = (sector ? '<a class="back-link" href="#/" data-testid="link-back">← All sectors</a>' : "") +
    title(sector ? `SECTOR ${sector.id} · SYNTHETIC SAMPLE` : "RESEARCH / SECTOR EXPOSURE",
      sector ? escape(sector.name) : "Sector exposure",
      sector ? "Inspect the weekly pattern behind this sample sector." : "Explore patterns in listing claims. Keep the uncertainty in view.") +
    controls(!sector) + '<p id="result-status" class="sr-only" role="status"></p><div id="results"></div>';
  bindFilters(renderResults);
  renderResults();
}
function methodologyView() {
  $("#view").innerHTML = title("RESEARCH / METHODOLOGY", "Know what the numbers mean",
    "Claims are observations to examine, not breaches to declare.") +
    `<div class="method-grid"><section class="panel prose"><p class="eyebrow">THIS PREVIEW</p><h2>Invented data. Working interactions.</h2>
      <p>Every count in this preview is synthetic. The fixture covers six sectors and twelve weekly windows. It demonstrates navigation, filtering, comparison and export. It does not demonstrate live collection or verify any incident.</p>
      <h2>How the illustrative bands work</h2><p>For a selected week, the demo compares its count with the mean of the previous four weeks. A ratio of at least 1.25 is “High”; at least 1.10 is “Elevated”; otherwise it is “Low”. These are interface-test thresholds, not an approved production model.</p>
      <p>A missing current count, missing baseline cell or fewer than four prior weeks produces “Insufficient data”. No baseline or observation is invented to fill a gap.</p>
      <h2>Withheld is not zero</h2><p>Some fixture cells are stored as <code>null</code> to exercise insufficient-data states. Exact hidden counts do not exist in this bundle. Partial totals use ≥ and include only visible cells. The preview is not a production privacy validator.</p>
      <h2>Read counts, not certainty</h2><p>Activity bands describe relative volume, not evidence confidence or business risk. No victim acknowledgement, attribution, confidence assessment or source evidence is modeled in this fixture.</p>
    </section><aside class="method-aside"><section class="panel prose"><p class="eyebrow">PRODUCTION BOUNDARY</p><h2>Real data stays gated</h2><ul><li>No live source calls or private credentials.</li><li>No organization or threat-actor records.</li><li>No publication proof or verified evidence.</li><li>No production publishing from this app.</li></ul><p>The live application will consume separately approved name-free aggregates. Connecting a dataset is not permission to publish it.</p></section>
    <section class="panel prose"><p class="eyebrow">REPRODUCIBLE SAMPLE</p><h2>Take the data with you</h2><p>JSON exports contain the selected sectors and weeks, explicit synthetic labels, and <code>publication_authorized: false</code>.</p><a href="#/dataset">Inspect the export →</a></section></aside></div>`;
}
function datasetView() {
  $("#view").innerHTML = title("RESEARCH / DATASET", "A portable research snapshot",
    "Inspect and download the current synthetic selection.") + controls() +
    '<p id="result-status" class="sr-only" role="status"></p><div id="dataset-content"></div>';
  const update = () => {
    const rows = currentRows(), selected = indices(), output = makeExport(rows, selected);
    $("#result-status").textContent = `${rows.length} sectors included in export.`;
    $("#dataset-content").innerHTML = `<section class="export-layout"><div class="panel prose"><p class="eyebrow">EXPORT CONTENTS</p><h2>${rows.length} sectors · ${selected.length} weeks</h2><p>Only the currently selected rows and weeks are included. Withheld cells remain <code>null</code>, never zero.</p><dl class="metadata"><dt>Data type</dt><dd>Synthetic fixture</dd><dt>Source connections</dt><dd>None</dd><dt>Publication authorized</dt><dd>No</dd><dt>Fixture</dt><dd>${FIXTURE_ID}</dd></dl><p class="muted">This is a preview-specific schema, not the approved production export contract.</p></div>
      <section class="panel json-panel"><div class="panel-heading"><h2>JSON preview</h2><span class="pill">application/json</span></div><pre tabindex="0" aria-label="Current synthetic JSON export" data-testid="json-preview">${escape(JSON.stringify(output, null, 2))}</pre></section></section>`;
  };
  bindFilters(update); update();
}
function render(moveFocus = true) {
  const hash = location.hash || "#/";
  const id = hash.startsWith("#/sector/") ? hash.slice(9) : "";
  const sector = SECTORS.find(s => s.id === id);
  route = sector ? {page: "overview", sector} :
    {page: hash === "#/" || hash === "#" ? "overview" : hash === "#/methodology" ? "methodology" : hash === "#/dataset" ? "dataset" : "missing", sector: null};
  $("#breadcrumb").textContent = sector ? sector.name : ({
    overview: "Sector exposure", methodology: "Methodology", dataset: "Dataset & export", missing: "Page not found",
  }[route.page]);
  document.querySelectorAll("[data-page]").forEach(link => {
    if (link.dataset.page === route.page) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  $("#download-status").textContent = "";
  if (route.page === "overview") researchView();
  else if (route.page === "methodology") methodologyView();
  else if (route.page === "dataset") datasetView();
  else $("#view").innerHTML = '<section class="empty"><h1>That view is not available</h1><p>Return to the sector overview to continue exploring the synthetic dataset.</p><a class="primary" href="#/">Back to sector exposure</a></section>';
  document.querySelectorAll(".export").forEach(button => button.addEventListener("click", download));
  document.title = `xevents | ${sector ? sector.name : $("#breadcrumb").textContent} | Synthetic preview`;
  if (moveFocus) { $("#main").scrollTop = 0; $("#main").focus({preventScroll: true}); }
}
function download() {
  try {
    const output = makeExport(currentRows(), indices());
    const blob = new Blob([JSON.stringify(output, null, 2) + "\n"], {type: "application/json"});
    const url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url; a.download = `xevents-synthetic-view1-${WEEKS[state.end]}.json`;
    document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    $("#download-status").textContent = `Synthetic JSON download requested: ${output.sectors.length} sectors. No production data included.`;
  } catch {
    $("#download-status").textContent = "The export could not be created. Reset the filters and try again.";
  }
}
window.addEventListener("hashchange", () => render());
render(false);
