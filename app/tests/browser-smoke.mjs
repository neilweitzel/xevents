// Optional browser QA. Requires Playwright in the test environment, not the app.
// Serve app/ first. Run: node app/tests/browser-smoke.mjs http://127.0.0.1:3000
import assert from "node:assert/strict";
import {chromium} from "playwright";

const base = process.argv[2] || "http://127.0.0.1:3000";
const demo = address => { const url = new URL(address); url.searchParams.set("demo", "1"); return url.href; };
const origin = new URL(base).origin;
const browser = await chromium.launch({headless: true});
const context = await browser.newContext({viewport: {width: 1440, height: 1000}});
const page = await context.newPage();
const errors = [], external = [];
page.on("pageerror", e => errors.push(e.message));
page.on("request", r => { if (new URL(r.url()).origin !== origin) external.push(r.url()); });
const ui = id => page.getByTestId(id);
const heading = name => page.getByRole("heading", {name, exact: true}).waitFor();
async function download() {
  const pending = page.waitForEvent("download");
  await ui("button-export").click();
  const item = await pending, stream = await item.createReadStream(), parts = [];
  for await (const part of stream) parts.push(part);
  return JSON.parse(Buffer.concat(parts).toString());
}

try {
  await page.goto(demo(base));
  await heading("Sector exposure");
  assert.equal(await ui("metric-latest").innerText(), "≥ 128");
  await ui("input-search").fill("manufact");
  await ui("select-window").selectOption("4");
  assert.equal(await page.locator(".sectors tbody tr").count(), 1);
  assert.equal(await ui("metric-total").innerText(), "144");
  const selected = await download();
  assert.equal(selected.synthetic, true);
  assert.equal(selected.publication_authorized, false);
  assert.equal(selected.sectors.length, 1);
  assert.equal(selected.sectors[0].weekly_claims.length, 4);
  assert.equal(selected.sectors[0].weekly_claims.at(-1).count, 42);
  await ui("input-search").fill("<img src=x onerror=alert(1)>");
  assert.equal(await page.locator(".empty").count(), 1);
  assert.equal(await page.locator("#view img").count(), 0);
  await ui("button-clear-search").click();
  assert.equal(await page.locator(".sectors tbody tr").count(), 6);
  await ui("button-reset").click();
  await ui("sort-count").click();
  assert.match(await page.locator(".sectors tbody tr").first().innerText(), /Educational/);
  assert.match(await page.locator(".sectors tbody tr").last().innerText(), /Transportation/);
  await ui("sort-count").click();
  assert.match(await page.locator(".sectors tbody tr").first().innerText(), /Manufacturing/);
  await ui("sort-name").click();
  assert.match(await page.locator(".sectors tbody tr").first().innerText(), /Educational/);
  assert.equal(await ui("sort-name").locator("..").getAttribute("aria-sort"), "ascending");
  assert.equal(await ui("sort-count").locator("..").getAttribute("aria-sort"), "none");
  assert.equal(await ui("sort-count").innerText(), "Claims");
  await ui("select-week").selectOption("0");
  assert.equal(await page.locator(".band.insufficient").count(), 6);
  assert.equal(await page.locator(".bar-slot").count(), 1);
  await ui("button-reset").click();
  await ui("link-sector-48-49").click();
  await heading("Transportation and warehousing");
  await ui("select-window").selectOption("1");
  assert.equal(await ui("metric-total").innerText(), "Withheld");
  assert.equal(await page.locator(".bar-value").innerText(), "—");
  assert.equal((await download()).sectors[0].weekly_claims[0].count, null);
  await ui("toggle-weekly-data").click();
  assert.equal(await page.locator("details").getAttribute("open"), "");
  await ui("link-back").click();
  await heading("Sector exposure");
  await page.goBack();
  await heading("Transportation and warehousing");
  await ui("nav-methodology").click();
  await heading("Know what the numbers mean");
  await page.getByRole("link", {name: "Inspect the export"}).click();
  await ui("json-preview").waitFor();
  await ui("input-search").fill("62");
  await ui("select-window").selectOption("4");
  await ui("select-week").selectOption("1");
  const json = JSON.parse(await ui("json-preview").innerText());
  assert.equal(json.sectors[0].sector_code, "62");
  assert.equal(json.sectors[0].weekly_claims.length, 2);
  await ui("button-reset").click();
  await ui("input-search").fill("no-such-sector");
  assert.deepEqual(JSON.parse(await ui("json-preview").innerText()).sectors, []);
  await ui("button-reset").click();
  await ui("link-home").click();
  await heading("Sector exposure");
  await ui("button-theme").click();
  assert.equal(await page.locator("html").getAttribute("data-theme"), "dark");
  await ui("button-theme").click();
  assert.equal(await page.locator("html").getAttribute("data-theme"), "light");

  for (const width of [1440, 375, 320]) {
    await page.setViewportSize({width, height: 900});
    for (const [hash, title] of [
      ["#/", "Sector exposure"], ["#/sector/54", "Professional and technical services"],
      ["#/methodology", "Know what the numbers mean"], ["#/dataset", "A portable research snapshot"],
    ]) {
      await page.goto(demo(`${base}/${hash}`));
      await heading(title);
      assert.equal(await page.evaluate(() =>
        document.documentElement.scrollWidth > innerWidth ||
        document.querySelector("main").scrollWidth > document.querySelector("main").clientWidth
      ), false, `Overflow at ${width} ${hash}`);
    }
  }
  await page.goto(demo(`${base}/#/invalid`));
  await heading("That view is not available");
  await page.getByRole("link", {name: "Back to sector exposure"}).click();
  await heading("Sector exposure");
  await page.reload();
  await heading("Sector exposure");
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").innerText(), "Skip to content");
  await page.keyboard.press("Enter");
  assert.equal(await page.locator(":focus").getAttribute("id"), "main");
  await ui("input-search").focus();
  await page.keyboard.type("retail");
  assert.equal(await page.locator(".sectors tbody tr").count(), 1);
  await page.keyboard.press("Tab");
  assert.equal(await page.locator(":focus").getAttribute("id"), "week");
  assert.deepEqual(errors, []);
  assert.deepEqual(external, []);
  // Inject a failed module request, then verify an actual user retry recovers.
  const failurePage = await context.newPage();
  let failOnce = true;
  await failurePage.route("**/model.mjs", route => {
    if (failOnce) { failOnce = false; return route.abort(); }
    return route.continue();
  });
  await failurePage.goto(demo(base));
  await failurePage.getByRole("heading", {name: "The preview could not start", exact: true}).waitFor();
  await failurePage.getByTestId("button-retry").click();
  await failurePage.getByTestId("metric-latest").waitFor();
  assert.equal(await failurePage.getByTestId("metric-latest").innerText(), "≥ 128");
  await failurePage.close();
  console.log("PASS: filters, sorting, downloads, nulls, routes, themes, layouts, keyboard, network, startup recovery.");
} finally {
  await context.close();
  await browser.close();
}
