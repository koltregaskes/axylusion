#!/usr/bin/env node

import path from "node:path";
import { pathToFileURL } from "node:url";
import { parseArgs } from "node:util";
import { evaluateResult } from "./lib/gallery-smoke.mjs";

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

// Keep explicit read state: malformed or missing expectations must fail the gallery check.
import fs from "node:fs";
import { fileURLToPath } from "node:url";
const REPO_DIR = path.dirname(path.dirname(fileURLToPath(import.meta.url)));
const GALLERY_JSON_PATH = path.join(REPO_DIR, "data", "gallery.json");
let localGalleryRead;
try {
  localGalleryRead = { ok: true, payload: JSON.parse(fs.readFileSync(GALLERY_JSON_PATH, "utf-8")) };
} catch {
  localGalleryRead = { ok: false };
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

async function capturePage(page, path) {
  const consoleErrors = [];
  const failedRequests = [];
  const badResponses = [];
  let galleryVisibleIds = [];
  let galleryCardCount = 0;
  let serverGalleryRead = { ok: false };
  let missingItemIdCardsFromDom = [];

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
      let serverRead = { ok: false };
      try {
        const response = await fetch("/data/gallery.json");
        if (response.ok) {
          serverRead = { ok: true, payload: await response.json() };
        }
      } catch {
        // Preserve failure, rather than treating it as a valid empty dataset.
      }
      return { ids, count: cards.length, serverRead, missingItemIdCards };
    });
    galleryCardCount = galleryData.count;
    galleryVisibleIds = galleryData.ids;
    serverGalleryRead = galleryData.serverRead;
    missingItemIdCardsFromDom = galleryData.missingItemIdCards;
  }

  return {
    path,
    title: await page.title(),
    consoleErrors,
    failedRequests,
    badResponses,
    galleryVisibleIds,
    galleryCardCount,
    serverGalleryRead,
    missingItemIdCardsFromDom,
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

    const evaluation = evaluateResult(result, check, { localGalleryRead });
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
      validationError: evaluation.validationError ?? null,
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

