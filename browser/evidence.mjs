import assert from "node:assert/strict";
import { createHash } from "node:crypto";
import { readFile, writeFile } from "node:fs/promises";
import process from "node:process";
import axe from "axe-core";
import { chromium } from "playwright";
import { startServer } from "./server.mjs";

const sha256 = bytes => createHash("sha256").update(bytes).digest("hex");
const canonical = value => `${JSON.stringify(value, null, 2)}\n`;
const read = path => readFile(path);

function option(name) {
  const index = process.argv.indexOf(name);
  if (index < 0 || index + 1 >= process.argv.length) throw new Error("arguments");
  return process.argv[index + 1];
}

const fixture = await read("browser/fixture.html");
const stylesheet = await read("browser/fixture.css");
const harness = await read("browser/evidence.mjs");
const staticReport = await read("evidence/failing-report.json");
const packages = JSON.parse(await readFile("package.json", "utf8"));
const server = await startServer();
let browser;
try {
  browser = await chromium.launch({ headless: true });
  const context = await browser.newContext({
    reducedMotion: "reduce",
    viewport: { width: 320, height: 720 },
  });
  const page = await context.newPage();
  let blockedRequests = 0;
  await page.route("**/*", async route => {
    const url = new URL(route.request().url());
    if (url.hostname !== "127.0.0.1" || url.origin !== server.origin) {
      blockedRequests += 1;
      await route.abort("blockedbyclient");
      return;
    }
    await route.continue();
  });
  const response = await page.goto(server.origin, { waitUntil: "domcontentloaded" });
  assert(response?.ok());
  assert.equal(response.headers()["referrer-policy"], "no-referrer");
  assert.equal(response.headers()["x-content-type-options"], "nosniff");

  await page.addScriptTag({ content: axe.source });
  const axeResult = await page.evaluate(async () => globalThis.axe.run(document));
  const violations = axeResult.violations
    .map(item => ({ count: item.nodes.length, impact: item.impact ?? "unknown", rule_id: item.id }))
    .sort((left, right) => left.rule_id.localeCompare(right.rule_id, "en"));
  assert.equal(violations.filter(item => ["critical", "serious"].includes(item.impact)).length, 0);

  const keyboard = [];
  for (let index = 0; index < 5; index += 1) {
    await page.keyboard.press("Tab");
    keyboard.push(await page.evaluate(() => {
      const element = document.activeElement;
      if (element?.classList.contains("skip-link")) return "skip";
      return element?.getAttribute("data-evidence-token") ?? "unknown";
    }));
  }
  assert.deepEqual(keyboard, ["skip", "input", "submit", "details", "docs"]);

  const focus = await page.evaluate(() => {
    const style = getComputedStyle(document.activeElement);
    return { outline_style: style.outlineStyle, outline_width_px: Number.parseFloat(style.outlineWidth) };
  });
  assert.notEqual(focus.outline_style, "none");
  assert(focus.outline_width_px >= 2);

  const reflow = await page.evaluate(() => ({
    document_width: document.documentElement.scrollWidth,
    viewport_width: document.documentElement.clientWidth,
  }));
  assert(reflow.document_width <= reflow.viewport_width);

  const reducedMotion = await page.locator(".motion-sample").evaluate(element => {
    const style = getComputedStyle(element);
    return {
      animation_duration_ms: Number.parseFloat(style.animationDuration) * 1000,
      media_matches: matchMedia("(prefers-reduced-motion: reduce)").matches,
    };
  });
  assert(reducedMotion.media_matches);
  assert(reducedMotion.animation_duration_ms <= 0.01);

  const externalSucceeded = await page.evaluate(async () => {
    try {
      await fetch("https://example.invalid/access-audit");
      return true;
    } catch {
      return false;
    }
  });
  assert.equal(externalSucceeded, false);

  const explorerResponse = await page.goto(`${server.origin}/explorer`, {
    waitUntil: "domcontentloaded",
  });
  assert(explorerResponse?.ok());
  await page.evaluate(axe.source);
  const explorerAxe = await page.evaluate(async () => globalThis.axe.run(document));
  const explorerSerious = explorerAxe.violations.filter(item =>
    ["critical", "serious"].includes(item.impact));
  assert.equal(explorerSerious.length, 0);
  await page.locator('[data-filter="error"]').click();
  assert.equal(await page.locator("#result-count").textContent(), "10 findings shown");
  assert.equal(await page.locator("tbody tr:not([hidden])").count(), 10);
  const explorerReflow = await page.evaluate(
    () => document.documentElement.scrollWidth <= document.documentElement.clientWidth,
  );
  assert(explorerReflow);

  const evidence = {
    schema: "access-audit/browser-evidence/v1",
    tool_version: "1.0.0",
    provenance: {
      axe_core_version: packages.devDependencies["axe-core"],
      fixture_sha256: sha256(fixture),
      harness_sha256: sha256(harness),
      playwright_version: packages.devDependencies.playwright,
      static_report_sha256: sha256(staticReport),
      stylesheet_sha256: sha256(stylesheet),
    },
    checks: {
      axe: { violations },
      explorer: {
        error_filter_count: 10,
        horizontal_overflow: false,
        serious_or_critical_violations: 0,
      },
      focus: { indicator_visible: true, minimum_outline_px: focus.outline_width_px },
      keyboard: { sequence: keyboard },
      network: { external_requests_blocked: blockedRequests, external_request_succeeded: false },
      reduced_motion: { animation_duration_ms: reducedMotion.animation_duration_ms, media_matches: true },
      reflow: { horizontal_overflow: false, viewport_css_px: 320 },
      security_headers: { csp: true, no_referrer: true, nosniff: true },
    },
    limitations: [
      "automated_evidence_is_not_wcag_conformance",
      "chromium_is_not_assistive_technology",
      "synthetic_fixture_is_not_a_public_website",
      "network_policy_is_not_a_general_sandbox",
    ],
  };
  const evidenceBytes = Buffer.from(canonical(evidence));
  const manifest = {
    schema: "access-audit/combined-evidence/v1",
    browser_report_sha256: sha256(evidenceBytes),
    static_report_sha256: sha256(staticReport),
  };
  await writeFile(option("--output"), evidenceBytes);
  await writeFile(option("--manifest"), canonical(manifest));
} finally {
  if (browser) await browser.close();
  await server.close();
}
