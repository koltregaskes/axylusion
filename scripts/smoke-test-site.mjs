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
  { path: "/gallery.html", mode: "gallery" },
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
      const ids = [];
      const missingItemIdCards = [];
      const cards = document.querySelectorAll(".cn-gallery-card");
      for (const card of cards) {
        const itemId = (card.getAttribute("data-item-id") || "").trim().toLowerCase();
        if (itemId) {
          ids.push(itemId);
        } else {
          missingItemIdCards.push(card.id || "");
        }
      }
      let expectedVisible = 0;
      let expectedIds = [];
      let domExpected = 0;
      try {
        const pager = document.querySelector("[data-gallery-count]");
        if (pager && pager.textContent) {
          const m = pager.textContent.match(/of\\s+(\\d+)/i);
          if (m && m[1]) domExpected = Number.parseInt(m[1], 10) || 0;
        }
      } catch {}
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
          expectedIds = items
            .map((it) => String(it.id || "").toLowerCase())
            .filter((id) => id && !flagged.has(id));
        }
      } catch {}
      return { ids, count: cards.length, expectedVisible, domExpected, expectedIds, missingItemIdCards };
    });
    galleryCardCount = galleryData?.count || 0;
    galleryVisibleIds = galleryData?.ids || [];
    var expectedVisibleFromServer = (typeof galleryData?.expectedVisible === "number" && galleryData.expectedVisible > 0) ? galleryData.expectedVisible : 0; // eslint-disable-line no-var
    var expectedVisibleFromDom = (typeof galleryData?.domExpected === "number" && galleryData.domExpected > 0) ? galleryData.domExpected : 0; // eslint-disable-line no-var
    var expectedIdsFromServer = Array.isArray(galleryData?.expectedIds) ? galleryData.expectedIds : []; // eslint-disable-line no-var
    var missingItemIdCardsFromDom = Array.isArray(galleryData?.missingItemIdCards) ? galleryData.missingItemIdCards : []; // eslint-disable-line no-var
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
    expectedVisibleFromDom: typeof expectedVisibleFromDom === "number" ? expectedVisibleFromDom : 0,
    expectedIdsFromServer: Array.isArray(expectedIdsFromServer) ? expectedIdsFromServer : [],
    missingItemIdCardsFromDom: Array.isArray(missingItemIdCardsFromDom) ? missingItemIdCardsFromDom : [],
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
  // Gallery-specific assertions:
  // - No missing data-item-id on any card
  // - No duplicate IDs (unique count === card count)
  // - Visible ID set exactly equals expected set (gallery.json items minus unavailable)
  // - No unavailable IDs are visible
  // - Explicitly assert presence/absence for known multi-UUID frames
  let unavailableVisible = [];
  let cardCountOk = true;
  let expectedCountOk = true;
  let expectedVisibleCount = 0;
  let missingItemIdCount = 0;
  let duplicateIds = [];
  let missingIds = [];
  let unexpectedIds = [];
  let explicitChecksOk = true;
  const mustHaveIds = new Set([
    "89cf68fa-4ba7-436d-85b7-764bc8c0c43f",
    "bcf7ef43-a942-4255-bd47-a0baf1f820d2",
  ]);
  const mustNotContainIds = new Set([
    "68a3ddec-240a-4922-b99a-5c2400bbbf26",
  ]);
  if (result.path.endsWith("/gallery.html")) {
    // Prefer expected count from the server-rendered data.json if provided
    expectedVisibleCount =
      (typeof result.expectedVisibleFromServer === "number" && result.expectedVisibleFromServer > 0)
        ? result.expectedVisibleFromServer
        : (typeof result.expectedVisibleFromDom === "number" && result.expectedVisibleFromDom > 0)
          ? result.expectedVisibleFromDom
          : Math.max(0, TOTAL_ITEMS - UNAVAILABLE_IDS.size);
    if (UNAVAILABLE_IDS.size > 0) {
      unavailableVisible = (result.galleryVisibleIds || []).filter((id) => UNAVAILABLE_IDS.has(String(id).toLowerCase()));
    }
    cardCountOk = result.galleryCardCount > 0;
    expectedCountOk = expectedVisibleCount === result.galleryCardCount;
    // Missing data-item-id attributes
    missingItemIdCount = Array.isArray(result.missingItemIdCardsFromDom) ? result.missingItemIdCardsFromDom.length : 0;
    // Duplicate IDs
    const seen = new Set();
    duplicateIds = [];
    for (const id of result.galleryVisibleIds || []) {
      const key = String(id).toLowerCase();
      if (seen.has(key)) duplicateIds.push(key);
      seen.add(key);
    }
    // Set equality against expected IDs set
    const expectedIdsSet = new Set(
      Array.isArray(result.expectedIdsFromServer) && result.expectedIdsFromServer.length > 0
        ? result.expectedIdsFromServer.map((id) => String(id).toLowerCase())
        : Array.from(UNAVAILABLE_IDS).length > 0
          ? Array.from({ length: 0 }) // placeholder, we will fall back below
          : []
    );
    // Fallback when expectedIdsFromServer missing: compute from local gallery.json parse
    if (expectedIdsSet.size === 0) {
      try {
        // Compute locally from TOTAL_ITEMS/UNAVAILABLE_IDS is insufficient for exact set; skip strict check in this fallback.
      } catch {}
    }
    const visibleIdsSet = new Set((result.galleryVisibleIds || []).map((id) => String(id).toLowerCase()));
    if (expectedIdsSet.size > 0) {
      for (const id of expectedIdsSet) {
        if (!visibleIdsSet.has(id)) missingIds.push(id);
      }
      for (const id of visibleIdsSet) {
        if (!expectedIdsSet.has(id)) unexpectedIds.push(id);
      }
    }
    // Explicit checks for known frames
    for (const id of mustHaveIds) {
      if (!visibleIdsSet.has(id)) explicitChecksOk = false;
    }
    for (const id of mustNotContainIds) {
      if (visibleIdsSet.has(id)) explicitChecksOk = false;
    }
  }
  const passed =
    onlyAllowedFailures &&
    consoleOkay &&
    unavailableVisible.length === 0 &&
    cardCountOk &&
    expectedCountOk &&
    missingItemIdCount === 0 &&
    duplicateIds.length === 0 &&
    (missingIds.length === 0 && unexpectedIds.length === 0) &&
    explicitChecksOk;

  let summary = "clean";
  if (problemUrls.length > 0 && onlyAllowedFailures) {
    summary = `allowed host failures only (${problemUrls.length})`;
  } else if (!passed) {
    if (result.path.endsWith("/gallery.html")) {
      if (!cardCountOk) {
        summary = "gallery has 0 cards";
      } else if (!expectedCountOk) {
        summary = `gallery shows ${result.galleryCardCount} cards, expected ${expectedVisibleCount}`;
      } else if (missingItemIdCount > 0) {
        summary = `gallery has ${missingItemIdCount} card(s) missing data-item-id`;
      } else if (duplicateIds.length > 0) {
        summary = `gallery has ${duplicateIds.length} duplicate ID(s)`;
      } else if (missingIds.length > 0 || unexpectedIds.length > 0) {
        summary = `gallery IDs mismatch: ${missingIds.length} missing, ${unexpectedIds.length} unexpected`;
      } else if (unavailableVisible.length > 0) {
        summary = `gallery shows ${unavailableVisible.length} unavailable item(s)`;
      } else if (!explicitChecksOk) {
        summary = "gallery explicit ID assertions failed";
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
    missingItemIdCount,
    duplicateIds,
    missingIds,
    unexpectedIds,
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
      missingItemIdCount: evaluation.missingItemIdCount ?? 0,
      duplicateIds: evaluation.duplicateIds ?? [],
      missingIds: evaluation.missingIds ?? [],
      unexpectedIds: evaluation.unexpectedIds ?? [],
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
