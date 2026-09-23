// Automated WCAG checks supplement, not replace, human accessibility review.
import assert from "node:assert/strict";
import {createRequire} from "node:module";
import {chromium} from "playwright";
const require = createRequire(import.meta.url);
const base = process.argv[2] || "http://127.0.0.1:3000";
const browser = await chromium.launch({headless: true});
try {
  const page = await browser.newPage({viewport: {width: 1440, height: 900}, reducedMotion: "reduce"});
  for (const width of [1440, 375, 320]) {
    await page.setViewportSize({width, height: 900});
    for (const mode of ["light", "dark"]) {
      for (const route of ["#/", "#/sector/48-49", "#/methodology", "#/dataset"]) {
        await page.goto(`${base}/${route}`);
        await page.locator("#view .page-heading").waitFor();
        if (await page.locator("html").getAttribute("data-theme") !== mode)
          await page.getByTestId("button-theme").click();
        await page.addScriptTag({path: require.resolve("axe-core/axe.min.js")});
        const violations = await page.evaluate(async () => {
          const result = await window.axe.run(document, {
            runOnly: {type: "tag", values: ["wcag2a", "wcag2aa", "wcag21aa"]},
          });
          return result.violations.map(v => ({
            id: v.id, impact: v.impact, targets: v.nodes.map(n => n.target),
          }));
        });
        assert.deepEqual(violations, [], `${width}px ${mode} ${route}`);
      }
    }
  }
  console.log("PASS: 24 automated accessibility scans; not a WCAG compliance certification.");
} finally {
  await browser.close();
}
