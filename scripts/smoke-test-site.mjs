#!/usr/bin/env node

import path from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";

const playwrightImportTarget = process.env.PLAYWRIGHT_MODULE_PATH
  ? pathToFileURL(path.join(process.env.PLAYWRIGHT_MODULE_PATH, "playwright", "index.js")).href
  : "playwright";

const playwrightModule = await import(playwrightImportTarget);
const chromium = playwrightModule.chromium ?? playwrightModule.default?.chromium;

const { values } = parseArgs({
  options: {
    "base-url": { type: "string", default: "http://127.0.0.1:4173" },
    "wait-ms": { type: "string", default: "2500" },
    "chrome-executable": { type: "string" },
  },
});

const baseUrl = values["base-url"].replace(/\/$/, "");
const waitMs = Number.parseInt(values["wait-ms"], 10);
const chromeExecutable = values["chrome-executable"];

// Load flagged-unavailable IDs from data/gallery.json (if available)
import fs from "node:fs";
import { fileURLToPath } from "node:url";
const REPO_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const GALLERY_JSON_PATH = path.join(REPO_DIR, "data", "gallery.json");
let UNAVAILABLE_IDS = new Set();
try {
  const raw = fs.readFileSync(GALLERY_JSON_PATH, "utf-8");
  const payload = JSON.parse(raw);
  const items = Array.isArray(payload?.items) ? payload.items : [];
  UNAVAILABLE_IDS = new Set(
    items.filter((it) => String(it?.media_status || "") === "unavailable").map((it) => String(it.id || "").toLowerCase()),
  );
} catch {
  // ignore, best-effort local check
}

const pageChecks = [
  { path: "/404.html", mode: "clean" },
  { path: "/about.html", mode: "clean" },
  { path: "/blog.html", mode: "clean" },
  { path: "/blog-welcome.html", mode: "clean" },
  { path: "/music.html", mode: "clean" },
  { path: "/news.html", mode: "clean" },
  { path: "/tools.html", mode: "clean" },
  { path: "/videos.html", mode: "clean" },
  { path: "/a-list.html", mode: "clean" },
  { path: "/a-list/image-generation.html", mode: "clean" },
  { path: "/index.html", mode: "clean" },
  { path: "/gallery.html", mode: "clean" },
];

function extractHost(urlString) {
  try {
    return new URL(urlString).hostname;
  } catch {
    return "";
  }
}

async function capturePage(page, path) {
  const consoleErrors = [];
  const failedRequests = [];
  const badResponses = [];
  let galleryVisibleIds = [];

  page.on("console", (message) => {
    if (message.type() === "error") {
      consoleErrors.push(message.text());
    }
  });

  page.on("requestfailed", (request) => {
    failedRequests.push({
      url: request.url(),
      error: request.failure()?.errorText || "unknown",
    });
  });

  page.on("response", (response) => {
    if (response.status() >= 400) {
      badResponses.push({
        url: response.url(),
        status: response.status(),
      });
    }
  });

  await page.goto(`${baseUrl}${path}`, { waitUntil: "domcontentloaded", timeout: 20000 });
  await page.waitForTimeout(waitMs);

  // On gallery.html, extract visible item IDs from image URLs and data-id attributes
  if (path.endsWith("/gallery.html")) {
    galleryVisibleIds = await page.evaluate(() => {
      const ids = new Set();
      // Cards from cinematic static gallery
      for (const img of document.querySelectorAll("img")) {
        const m = (img.src || "").match(/[0-9a-f]{8}-[0-9a-f-]{27,36}/i);
        if (m && m[0]) ids.add(m[0].toLowerCase());
      }
      // Dynamic grid (if rendered by gallery.js)
      for (const el of document.querySelectorAll(".gallery-item[data-id]")) {
        const id = (el.getAttribute("data-id") || "").toLowerCase();
        if (id) ids.add(id);
      }
      return Array.from(ids);
    });
  }

  return {
    path,
    title: await page.title(),
    consoleErrors,
    failedRequests,
    badResponses,
    galleryVisibleIds,
  };
}

function evaluateResult(result, check) {
  const problemUrls = [
    ...result.failedRequests.map((entry) => entry.url),
    ...result.badResponses.map((entry) => entry.url),
  ];

  if (check.mode === "clean") {
    const passed = result.consoleErrors.length === 0 && problemUrls.length === 0;
    return {
      passed,
      summary: passed ? "clean" : "unexpected runtime issues",
    };
  }

  const allowedHosts = new Set(check.allowedHosts || []);
  const disallowedUrls = problemUrls.filter((url) => !allowedHosts.has(extractHost(url)));
  const onlyAllowedFailures = disallowedUrls.length === 0;
  const consoleOkay = result.consoleErrors.length === 0 || (problemUrls.length > 0 && onlyAllowedFailures);
  // Fail if any visible gallery ID is flagged as unavailable
  let unavailableVisible = [];
  if (result.path.endsWith("/gallery.html") && UNAVAILABLE_IDS.size > 0) {
    unavailableVisible = (result.galleryVisibleIds || []).filter((id) => UNAVAILABLE_IDS.has(String(id).toLowerCase()));
  }
  const passed = onlyAllowedFailures && consoleOkay && unavailableVisible.length === 0;

  let summary = "clean";
  if (problemUrls.length > 0 && onlyAllowedFailures) {
    summary = `allowed host failures only (${problemUrls.length})`;
  } else if (!passed) {
    summary =
      unavailableVisible.length > 0
        ? `gallery shows ${unavailableVisible.length} unavailable item(s)`
        : "unexpected runtime issues";
  }

  return {
    passed,
    summary,
    disallowedUrls,
    unavailableVisible,
  };
}

const browser = await chromium.launch(
  chromeExecutable
    ? {
        executablePath: chromeExecutable,
        headless: true,
      }
    : { headless: true },
);

let failed = false;

try {
  for (const check of pageChecks) {
    const page = await browser.newPage();
    const result = await capturePage(page, check.path);
    await page.close();

    const evaluation = evaluateResult(result, check);
    const payload = {
      path: result.path,
      title: result.title,
      summary: evaluation.summary,
      consoleErrorCount: result.consoleErrors.length,
      failedRequestCount: result.failedRequests.length,
      badResponseCount: result.badResponses.length,
      unavailableVisible: evaluation.unavailableVisible ?? [],
    };

    console.log(JSON.stringify(payload));

    if (!evaluation.passed) {
      failed = true;
      if (result.consoleErrors.length > 0) {
        console.error(`Console errors on ${result.path}:`);
        for (const error of result.consoleErrors) {
          console.error(`- ${error}`);
        }
      }
      if (result.failedRequests.length > 0) {
        console.error(`Failed requests on ${result.path}:`);
        for (const entry of result.failedRequests.slice(0, 12)) {
          console.error(`- ${entry.url} (${entry.error})`);
        }
      }
      if (result.badResponses.length > 0) {
        console.error(`Bad responses on ${result.path}:`);
        for (const entry of result.badResponses.slice(0, 12)) {
          console.error(`- ${entry.url} (${entry.status})`);
        }
      }
      if (evaluation.disallowedUrls?.length) {
        console.error(`Disallowed failing hosts on ${result.path}:`);
        for (const url of evaluation.disallowedUrls.slice(0, 12)) {
          console.error(`- ${url}`);
        }
      }
    }
  }
} finally {
  await browser.close();
}

if (failed) {
  process.exit(1);
}
