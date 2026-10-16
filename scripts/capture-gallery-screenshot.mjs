#!/usr/bin/env node

import path from "node:path";
import fs from "node:fs";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

const playwrightImportTarget = process.env.PLAYWRIGHT_MODULE_PATH
  ? pathToFileURL(path.join(process.env.PLAYWRIGHT_MODULE_PATH, "playwright", "index.js")).href
  : "playwright";

const { chromium } = await import(playwrightImportTarget);

const { values } = parseArgs({
  options: {
    "base-url": { type: "string", default: "http://127.0.0.1:4173" },
    "out": { type: "string", default: "/opt/cursor/artifacts/screenshots/gallery-after.png" },
    "wait-ms": { type: "string", default: "1500" },
    "chrome-executable": { type: "string" },
  },
});

const baseUrl = values["base-url"].replace(/\/$/, "");
const outPath = values["out"];
const waitMs = Number.parseInt(values["wait-ms"], 10);
const chromeExecutable = values["chrome-executable"];

fs.mkdirSync(path.dirname(outPath), { recursive: true });

const browser = await chromium.launch(
  chromeExecutable
    ? {
        executablePath: chromeExecutable,
        headless: true,
      }
    : { headless: true },
);

try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(`${baseUrl}/gallery.html`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await page.waitForTimeout(waitMs);
  await page.screenshot({ path: outPath, fullPage: true });
  console.log(JSON.stringify({ screenshot: outPath, ok: true }));
} finally {
  await browser.close();
}

