import {loadAggregate, selection, exportSelection} from "./aggregate.mjs";

const $ = selector => document.querySelector(selector);
const escape = value => String(value).replace(/[&<>"']/g, c =>
  ({"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}[c]));
const count = value => value === null ? "Withheld" : value.toLocaleString("en-US");
let theme = matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
function applyTheme() {
  document.documentElement.dataset.theme = theme;
  $("#theme").textContent = theme === "dark" ? "Light mode" : "Dark mode";
  $("#theme").setAttribute("aria-label", `Switch to ${theme === "dark" ? "light" : "dark"} mode`);
}
$("#theme").addEventListener("click", () => { theme = theme === "dark" ? "light" : "dark"; applyTheme(); });
applyTheme();
$(".skip").addEventListener("click", event => {
  event.preventDefault(); $("#main").focus(); $("#main").scrollTop = 0;
});
document.title = "xevents | Incident-claim research";
$(".preview-label").textContent = "Research RC";
$(".sidebar-bottom .version").textContent = "RESEARCH RC · VIEW 1";
$("footer span:last-child").textContent = "Name-free sector aggregates";
$(".sample-notice").innerHTML = "<strong>Claims, not confirmed breaches.</strong><span>Partial source coverage. Withheld cells are not zero.</span>";
$(".sidebar-bottom strong").textContent = "Checking public data";
$(".sidebar-bottom p").textContent = "Only published aggregates are requested. This browser never reads private records.";
$("#view").innerHTML = '<section class="empty" role="status"><h1>Loading the research dataset</h1><p>Checking the public release file. No private source is contacted.</p></section>';
let result = await loadAggregate();
const state = {query: "", sort: "name", end: (result.dataset?.weeks.length || 1) - 1, length: 12};
let current;
const heading = (title, body) => `<div class="page-heading"><div><p class="eyebrow">XEVENTS / RESEARCH</p><h1>${title}</h1><p class="lede">${body}</p></div></div>`;
function connection() {
  const names = {ready: result.dataset?.stale ? "Published data · stale" : "Published data",
    empty: "No released cells", waiting: "Awaiting approved data", unavailable: "Dataset unavailable"};
  $(".sidebar-bottom strong").textContent = names[result.state];
}
function unavailable() {
  const title = {waiting: "Awaiting approved data", empty: "No released aggregate cells",
    unavailable: "The dataset could not be loaded"}[result.state];
  const message = result.state === "unavailable" ?
    "The release file is unreachable or failed validation. No sample counts have been substituted." :
    "There are no approved aggregate cells available here yet. This does not mean there were no incidents.";
  $("#view").innerHTML = heading(title, message) +
    '<section class="panel prose"><h2>A clear boundary</h2><p>Collection and processing happen privately. This site reads only released, name-free aggregates; it cannot authorize their publication.</p><p>You can inspect the interface using explicitly labeled synthetic data while research releases are pending.</p><p><button class="primary" id="refresh-data">Check again</button> <a href="?demo=1#/">Open synthetic demo</a></p></section>';
  $("#refresh-data").addEventListener("click", async () => {
    $("#refresh-data").disabled = true;
    $("#refresh-data").textContent = "Checking…";
    result = await loadAggregate();
    state.end = (result.dataset?.weeks.length || 1) - 1;
    render();
  });
}
function methodology() {
  $("#view").innerHTML = heading("Know what the numbers mean", "Claims are observations to examine, not breaches to declare.") +
    `<section class="panel prose"><h2>One limited source window</h2><p>Released counts describe incident claims observed through a bounded recent-record source window. They are not a complete census, a count of confirmed breaches or a risk score.</p>
    <h2>Retrieval weeks, not attack dates</h2><p>Weeks begin on Monday in UTC and use first retrieval time. Source-claimed dates are not used to backdate a sighting or imply when a compromise occurred.</p>
    <h2>Privacy and uncertainty</h2><p>A cell below five is withheld as null, including zero. Missing, pending and withheld data must not be interpreted as absence of activity. No demo activity bands are applied to research data.</p>
    <h2>Release controls</h2><p>The reader validates the format of a published file. Review, evidence linkage, name scanning and signed publication must happen before that file reaches this site; a browser cannot replace those controls.</p>
    <h2>Attribution</h2><p>Derived source attribution: <a href="https://www.ransomlook.io/" rel="noreferrer">RansomLook</a>, CC BY 4.0. This RC shows counts only, not the complete planned evidence and correction views.</p>
    <p><a href="?demo=1#/">Open the separate synthetic demo</a></p></section>`;
}
function research(datasetMode, sectorCode) {
  const dataset = result.dataset;
  const sector = dataset.sectors.find(s => s.id === sectorCode);
  $("#view").innerHTML = heading(datasetMode ? "A portable research snapshot" : sector ? escape(sector.name) : "Sector exposure",
    "Listing claims aggregated by retrieval week. Uncertainty remains visible.") +
    (dataset.stale ? '<div class="sample-notice" role="status"><strong>Stale dataset.</strong><span>This release was generated more than two weeks ago. It is not current coverage.</span></div>' : "") +
    `<section class="filters"><label class="search-field"><span>Search sectors</span><input id="search" data-testid="input-search" value="${escape(state.query)}" type="search"></label>
    <label><span>Reporting week</span><select id="week" data-testid="select-week">${dataset.weeks.map((w, i) =>
      `<option value="${i}" ${i === state.end ? "selected" : ""}>${w}</option>`).reverse().join("")}</select></label>
    <label><span>Window</span><select id="window" data-testid="select-window">${[1, 4, 12].map(n =>
      `<option value="${n}" ${n === state.length ? "selected" : ""}>${n} week${n > 1 ? "s" : ""}</option>`).join("")}</select></label>
    <label><span>Sort</span><select id="sort"><option value="name">Sector name</option><option value="latest-desc">Most claims</option><option value="latest-asc">Fewest claims</option></select></label>
    <button id="reset" class="quiet">Reset</button><button id="export" class="primary" data-testid="button-export">Download JSON</button></section>
    <p class="lede">Generated ${escape(dataset.header.generated_at)} · Recent-window coverage only</p>
    <div id="results" aria-live="polite"></div>`;
  $("#sort").value = state.sort;
  function update() {
    current = selection(dataset, sector ? sector.id : state.query, state.end, state.length, state.sort);
    const visible = current.rows.reduce((sum, row) => sum + (row.claim_count ?? 0), 0);
    const withheld = current.rows.filter(row => row.claim_count === null).length;
    const total = !visible && withheld ? "Withheld" : `${withheld ? "≥ " : ""}${visible.toLocaleString("en-US")}`;
    const output = exportSelection(dataset, current);
    $("#results").innerHTML = `<section class="metrics"><div><span>Visible claims</span><strong data-testid="metric-total">${total}</strong><span>Not confirmed breaches</span></div><div><span>Sectors selected</span><strong>${current.sectors.length}</strong><span>${current.weeks.length} retrieval weeks</span></div><div><span>Withheld cells</span><strong>${withheld}</strong><span>Never interpreted as zero</span></div></section>` +
      (datasetMode ? `<section class="panel json-panel"><div class="panel-heading"><h2>Selected aggregate export</h2></div><pre tabindex="0" data-testid="json-preview" aria-label="Selected aggregate JSON">${escape(JSON.stringify(output, null, 2))}</pre></section>` :
      current.sectors.length ? `<section class="panel"><div class="table-scroll"><table class="sectors"><caption class="sr-only">Sector claims by retrieval week</caption><thead><tr><th scope="col">Sector</th>${current.weeks.map(w => `<th scope="col">${w}</th>`).join("")}</tr></thead><tbody>${current.sectors.map(s =>
        `<tr><th scope="row"><a href="#/sector/${s.id}">${escape(s.name)}</a></th>${current.weeks.map(w => `<td>${count(s.counts[dataset.weeks.indexOf(w)])}</td>`).join("")}</tr>`).join("")}</tbody></table></div><p class="table-footnote">Counts are claims from partial coverage. Null cells remain withheld in every export.</p></section>` :
      '<section class="empty"><h2>No matching sectors</h2><p>Try a broader search or reset the filters. No zero-valued observations have been inserted.</p></section>');
  }
  $("#search").addEventListener("input", event => { state.query = event.target.value; update(); });
  $("#week").addEventListener("change", event => { state.end = Number(event.target.value); update(); });
  $("#window").addEventListener("change", event => { state.length = Number(event.target.value); update(); });
  $("#sort").addEventListener("change", event => { state.sort = event.target.value; update(); });
  $("#reset").addEventListener("click", () => {
    Object.assign(state, {query: "", sort: "name", end: dataset.weeks.length - 1, length: 12}); render();
  });
  $("#export").addEventListener("click", () => {
    const blob = new Blob([JSON.stringify(exportSelection(dataset, current), null, 2) + "\n"], {type: "application/json"});
    const url = URL.createObjectURL(blob), a = document.createElement("a");
    a.href = url; a.download = "xevents-sector-claims.json"; document.body.append(a); a.click(); a.remove();
    setTimeout(() => URL.revokeObjectURL(url), 1000);
    $("#download-status").textContent = "Selected aggregate JSON download requested.";
  });
  update();
}
function render() {
  connection();
  const hash = location.hash || "#/";
  const page = hash === "#/methodology" ? "methodology" : hash === "#/dataset" ? "dataset" : "overview";
  $("#breadcrumb").textContent = {overview: "Sector exposure", methodology: "Methodology", dataset: "Dataset & export"}[page];
  document.querySelectorAll("[data-page]").forEach(link => {
    if (link.dataset.page === page) link.setAttribute("aria-current", "page");
    else link.removeAttribute("aria-current");
  });
  $("#download-status").textContent = "";
  if (page === "methodology") methodology();
  else if (result.state !== "ready") unavailable();
  else if (["#/", "#", "#/dataset"].includes(hash) ||
           result.dataset.sectors.some(s => hash === `#/sector/${s.id}`)) research(page === "dataset", hash.slice(9));
  else $("#view").innerHTML = heading("That view is not available", "Choose Sector exposure to return to the dataset.");
}
window.addEventListener("hashchange", () => { render(); $("#main").focus(); $("#main").scrollTop = 0; });
render();
