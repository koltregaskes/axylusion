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
  { path: "/index.html", mode: "allow-hosts", allowedHosts: ["cdn.midjourney.com"] },
  { path: "/gallery.html", mode: "allow-hosts", allowedHosts: ["cdn.midjourney.com"] },
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

  return {
    path,
    title: await page.title(),
    consoleErrors,
    failedRequests,
    badResponses,
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
  const passed = onlyAllowedFailures && consoleOkay;

  let summary = "clean";
  if (problemUrls.length > 0 && onlyAllowedFailures) {
    summary = `allowed host failures only (${problemUrls.length})`;
  } else if (!passed) {
    summary = "unexpected runtime issues";
  }

  return {
    passed,
    summary,
    disallowedUrls,
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
