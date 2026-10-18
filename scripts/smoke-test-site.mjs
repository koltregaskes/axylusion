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
let TOTAL_ITEMS = 0;
try {
  const raw = fs.readFileSync(GALLERY_JSON_PATH, "utf-8");
  const payload = JSON.parse(raw);
  const items = Array.isArray(payload?.items) ? payload.items : [];
  TOTAL_ITEMS = items.length;
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
  let galleryCardCount = 0;

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

  // On gallery.html, extract visible item IDs from cinematic cards
  if (path.endsWith("/gallery.html")) {
    const galleryData = await page.evaluate(async () => {
      const uuidRe = /[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}/i;
      const ids = new Set();
      const cards = document.querySelectorAll(".cn-gallery-card");
      for (const card of cards) {
        const haystack = (card.getAttribute("data-search") || "").toLowerCase();
        const m = haystack.match(uuidRe);
        if (m && m[0]) ids.add(m[0].toLowerCase());
      }
      let expectedVisible = 0;
      try {
        const resp = await fetch("/data/gallery.json");
        if (resp.ok) {
          const payload = await resp.json();
          const items = Array.isArray(payload?.items) ? payload.items : [];
          const flagged = new Set(
            items
              .filter((it) => String(it?.media_status || "") === "unavailable")
              .map((it) => String(it.id || "").toLowerCase()),
          );
          expectedVisible = Math.max(0, items.length - flagged.size);
        }
      } catch {}
      return { ids: Array.from(ids), count: cards.length, expectedVisible };
    });
    galleryCardCount = galleryData?.count || 0;
    galleryVisibleIds = galleryData?.ids || [];
    var expectedVisibleFromServer = (typeof galleryData?.expectedVisible === "number" && galleryData.expectedVisible > 0) ? galleryData.expectedVisible : 0; // eslint-disable-line no-var
  }

  return {
    path,
    title: await page.title(),
    consoleErrors,
    failedRequests,
    badResponses,
    galleryVisibleIds,
    galleryCardCount,
    expectedVisibleFromServer: typeof expectedVisibleFromServer === "number" ? expectedVisibleFromServer : 0,
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
  // Fail if any visible gallery ID is flagged as unavailable; fail if 0 cards; assert expected total
  let unavailableVisible = [];
  let cardCountOk = true;
  let expectedCountOk = true;
  let expectedVisibleCount = 0;
  if (result.path.endsWith("/gallery.html")) {
    // Prefer expected count from the server-rendered data.json if provided
    expectedVisibleCount =
      (typeof result.expectedVisibleFromServer === "number" && result.expectedVisibleFromServer > 0)
        ? result.expectedVisibleFromServer
        : Math.max(0, TOTAL_ITEMS - UNAVAILABLE_IDS.size);
    if (UNAVAILABLE_IDS.size > 0) {
      unavailableVisible = (result.galleryVisibleIds || []).filter((id) => UNAVAILABLE_IDS.has(String(id).toLowerCase()));
    }
    cardCountOk = result.galleryCardCount > 0;
    expectedCountOk = expectedVisibleCount === result.galleryCardCount;
  }
  const passed = onlyAllowedFailures && consoleOkay && unavailableVisible.length === 0 && cardCountOk && expectedCountOk;

  let summary = "clean";
  if (problemUrls.length > 0 && onlyAllowedFailures) {
    summary = `allowed host failures only (${problemUrls.length})`;
  } else if (!passed) {
    if (result.path.endsWith("/gallery.html")) {
      if (!cardCountOk) {
        summary = "gallery has 0 cards";
      } else if (!expectedCountOk) {
        summary = `gallery shows ${result.galleryCardCount} cards, expected ${expectedVisibleCount}`;
      } else if (unavailableVisible.length > 0) {
        summary = `gallery shows ${unavailableVisible.length} unavailable item(s)`;
      } else {
        summary = "unexpected runtime issues";
      }
    } else {
      summary = "unexpected runtime issues";
    }
  }

  return {
    passed,
    summary,
    disallowedUrls,
    unavailableVisible,
    expectedVisibleCount,
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
      galleryCardCount: result.galleryCardCount ?? 0,
      expectedVisibleCount: evaluation.expectedVisibleCount ?? 0,
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
