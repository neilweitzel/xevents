// Entirely synthetic network fixtures. Never write test releases to the site.
import assert from "node:assert/strict";
import {createRequire} from "node:module";
import {chromium} from "playwright";
import {CODES, SCHEMA} from "../aggregate.mjs";
const require = createRequire(import.meta.url);
const base = process.argv[2] || "http://127.0.0.1:3000";
const browser = await chromium.launch({headless: true});
const canonical = value => JSON.stringify(value, Object.keys(value).sort());
const fixture = state => {
  const generated = new Date(Date.now() - (state === "stale" ? 20 : 0) * 86400000);
  generated.setUTCHours(0, 0, 0, 0);
  const monday = new Date(generated);
  monday.setUTCDate(monday.getUTCDate() - (monday.getUTCDay() + 6) % 7);
  const weeks = [new Date(+monday - 7 * 86400000), monday].map(d => d.toISOString().slice(0, 10));
  const header = {file_purpose: "sector_aggregate", schema_version: SCHEMA,
    generated_at: generated.toISOString().replace(".000Z", "Z"),
    release_state: state === "blocked" ? "blocked" : "released",
    privacy_floor: 5, time_basis: "retrieved_at", coverage: "recent_only"};
  const rows = state === "empty" ? [] : weeks.flatMap(week_start => CODES.map(sector =>
    ({sector, week_start, claim_count: sector === "31-33" && state !== "withheld" ? 7 : null})));
  return [header, ...rows].map(canonical).join("\n") + "\n";
};
const context = await browser.newContext({viewport: {width: 1440, height: 1000}, reducedMotion: "reduce"});
const page = await context.newPage();
let mode = "waiting", errors = [], requested = [];
page.on("pageerror", e => errors.push(e.message));
page.on("request", r => requested.push(new URL(r.url()).pathname));
await page.route("**/data/aggregates/view1.jsonl", route => {
  if (mode === "failed") return route.abort();
  return route.fulfill({status: mode === "waiting" ? 404 : 200,
    contentType: "application/jsonl", body: mode === "invalid" ? "<html>bad</html>" : fixture(mode)});
});
async function visit(expected) {
  await page.goto(base);
  await page.getByRole("heading", {name: expected, exact: true}).waitFor();
}
try {
  await visit("Awaiting approved data");
  assert.equal(requested.some(path => path.endsWith("/model.mjs") || path.endsWith("/app.mjs")), false);
  assert.equal(await page.getByTestId("metric-total").count(), 0);
  mode = "ready";
  await page.getByRole("button", {name: "Check again", exact: true}).click();
  await page.getByRole("heading", {name: "Sector exposure", exact: true}).waitFor();
  assert.equal(await page.getByTestId("metric-total").innerText(), "≥ 14");
  await page.getByTestId("input-search").fill("manufact");
  await page.getByTestId("select-window").selectOption("1");
  assert.equal(await page.getByTestId("metric-total").innerText(), "7");
  await page.locator("#sort").selectOption("latest-desc");
  const download = page.waitForEvent("download");
  await page.getByTestId("button-export").click();
  const stream = await (await download).createReadStream(), chunks = [];
  for await (const chunk of stream) chunks.push(chunk);
  const exported = JSON.parse(Buffer.concat(chunks));
  assert.equal(exported.synthetic, false); assert.equal(exported.rows.length, 1);
  assert.equal(exported.rows[0].claim_count, 7); assert.match(exported.attribution, /RansomLook/);
  await page.getByTestId("input-search").fill("<img src=x onerror=alert(1)>");
  assert.equal(await page.locator("#view img").count(), 0);
  await page.getByRole("heading", {name: "No matching sectors", exact: true}).waitFor();
  await page.getByRole("button", {name: "Reset", exact: true}).click();
  await page.getByRole("link", {name: "Manufacturing", exact: true}).click();
  await page.getByRole("heading", {name: "Manufacturing", exact: true}).waitFor();
  await page.getByTestId("nav-dataset").click();
  await page.getByTestId("json-preview").waitFor();
  await page.getByTestId("nav-methodology").click();
  await page.getByRole("heading", {name: "Know what the numbers mean", exact: true}).waitFor();
  for (const [state, expected] of [
    ["blocked", "The dataset could not be loaded"], ["failed", "The dataset could not be loaded"],
    ["invalid", "The dataset could not be loaded"], ["empty", "No released aggregate cells"],
    ["withheld", "Sector exposure"], ["stale", "Sector exposure"],
  ]) {
    mode = state; await visit(expected);
    if (state === "withheld") assert.equal(await page.getByTestId("metric-total").innerText(), "Withheld");
    if (state === "stale") await page.getByText("Stale dataset.", {exact: true}).waitFor();
    if (["blocked", "failed", "invalid"].includes(state))
      assert.equal(await page.getByTestId("button-export").count(), 0);
  }
  let scans = 0;
  for (const state of ["waiting", "ready", "stale", "invalid"]) {
    mode = state;
    for (const width of [1440, 375, 320]) {
      await page.setViewportSize({width, height: 1000});
      await visit(state === "waiting" ? "Awaiting approved data" :
        state === "invalid" ? "The dataset could not be loaded" : "Sector exposure");
      for (const theme of ["light", "dark"]) {
        if (await page.locator("html").getAttribute("data-theme") !== theme)
          await page.getByTestId("button-theme").click();
        assert.equal(await page.evaluate(() => document.documentElement.scrollWidth > innerWidth ||
          document.querySelector("main").scrollWidth > document.querySelector("main").clientWidth), false);
        await page.addScriptTag({path: require.resolve("axe-core/axe.min.js")});
        const violations = await page.evaluate(async () => (await window.axe.run(document, {
          runOnly: {type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"]},
        })).violations.map(v => ({id: v.id, targets: v.nodes.map(n => n.target)})));
        assert.deepEqual(violations, [], `${state} ${width} ${theme}`); scans++;
      }
    }
  }
  assert.deepEqual(errors, []);
  const failedContext = await browser.newContext();
  const failedPage = await failedContext.newPage();
  await failedPage.route("**/research.mjs", route => route.abort());
  await failedPage.goto(base);
  await failedPage.getByRole("heading", {name: "The research app could not start", exact: true}).waitFor();
  await failedPage.unroute("**/research.mjs");
  await failedPage.getByRole("button", {name: "Reload app", exact: true}).click();
  await failedPage.getByRole("heading", {name: "Awaiting approved data", exact: true}).waitFor();
  await failedContext.close();
  console.log(`PASS: research loading/retry, filters, download, routes, fail-closed states, layouts and ${scans} accessibility scans.`);
} finally { await browser.close(); }
