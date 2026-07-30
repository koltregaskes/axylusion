#!/usr/bin/env node

import fs from "node:fs";
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
    "wait-ms": { type: "string", default: "500" },
    "browser-executable": { type: "string" },
    "chrome-executable": { type: "string" },
    "screenshot-dir": { type: "string" },
  },
});

const baseUrl = values["base-url"].replace(/\/$/, "");
const waitMs = Number.parseInt(values["wait-ms"], 10);
const browserExecutable = values["browser-executable"] ?? values["chrome-executable"];
const screenshotDir = values["screenshot-dir"];
const productionOrigin = "https://axylusion.com";

const routes = [
  "/404.html",
  "/about.html",
  "/blog.html",
  "/blog-welcome.html",
  "/music.html",
  "/news.html",
  "/store.html",
  "/tools.html",
  "/videos.html",
  "/a-list.html",
  "/a-list/3d-generation.html",
  "/a-list/image-editing.html",
  "/a-list/image-generation.html",
  "/a-list/music-generation.html",
  "/a-list/upscaling.html",
  "/a-list/video-generation.html",
  "/a-list/voice-tts.html",
  "/index.html",
  "/gallery.html",
];

const viewports = [
  { name: "mobile-light-os", width: 390, height: 844, colorScheme: "light" },
  { name: "desktop-dark-os", width: 1440, height: 1000, colorScheme: "dark" },
];

const screenshotRoutes = new Set([
  "/index.html",
  "/gallery.html",
  "/blog.html",
  "/a-list.html",
  "/tools.html",
]);

function expectedCanonical(route) {
  if (route === "/404.html") return null;
  if (route === "/index.html") return `${productionOrigin}/`;
  return `${productionOrigin}${route}`;
}

async function checkInteraction(page, route) {
  if (route === "/index.html") {
    const buttons = page.locator("[data-hero-index]");
    if (await buttons.count() < 2) return "hero index has fewer than two controls";
    const before = await page.locator("[data-hero-ref]").textContent();
    await buttons.nth(1).click();
    const after = await page.locator("[data-hero-ref]").textContent();
    return before !== after ? "hero index changed the active frame" : "hero index did not change the active frame";
  }

  if (route === "/gallery.html") {
    const search = page.locator("[data-gallery-search]");
    await search.fill("axy-no-match-regression-query");
    const emptyVisible = await page.locator("[data-gallery-empty]").isVisible();
    await page.locator("[data-gallery-reset]:visible").first().click();
    const visibleCards = await page.locator("[data-search]:visible").count();
    return emptyVisible && visibleCards > 0
      ? "gallery search and reset worked"
      : "gallery search or reset failed";
  }

  if (route === "/news.html") {
    const search = page.locator("[data-news-search]");
    await search.fill("axy-no-match-regression-query");
    const emptyVisible = await page.locator("[data-news-empty]").isVisible();
    await page.locator("[data-news-empty-reset]").click();
    const visibleRows = await page.locator("[data-digest-date]:visible").count();
    return emptyVisible && visibleRows > 0
      ? "news search and reset worked"
      : "news search or reset failed";
  }

  if (route === "/tools.html") {
    const filter = page.locator(".tool-filter-link[data-filter]:not([data-filter='all'])").first();
    await filter.click();
    const selected = await filter.evaluate((element) => element.classList.contains("active"));
    const hiddenSections = await page.locator(".tools-category.is-hidden").count();
    return selected && hiddenSections > 0
      ? "tools category filter worked"
      : "tools category filter failed";
  }

  if (route === "/blog.html") {
    return (await page.getByText("Coming soon", { exact: true }).count()) === 0
      ? "blog exposes no speculative coming-soon promise"
      : "blog still exposes speculative coming-soon copy";
  }

  return "not applicable";
}

async function capturePage(page, route, viewport) {
  const consoleErrors = [];
  const failedRequests = [];
  const badResponses = [];

  page.on("console", (message) => {
    if (message.type() === "error") consoleErrors.push(message.text());
  });
  page.on("requestfailed", (request) => {
    failedRequests.push({ url: request.url(), error: request.failure()?.errorText || "unknown" });
  });
  page.on("response", (response) => {
    if (response.status() >= 400) badResponses.push({ url: response.url(), status: response.status() });
  });

  const navigation = await page.goto(`${baseUrl}${route}`, {
    waitUntil: "domcontentloaded",
    timeout: 20000,
  });
  await page.waitForTimeout(waitMs);

  const expected = expectedCanonical(route);
  const state = await page.evaluate(() => {
    const canonicalLinks = Array.from(document.querySelectorAll("link[rel='canonical']"))
      .map((element) => element.href);
    const referrer = document.querySelector("meta[name='referrer']")?.content ?? "";
    const cspCount = document.querySelectorAll("meta[http-equiv='Content-Security-Policy']").length;
    const colourScheme = document.querySelector("meta[name='color-scheme']")?.content ?? "";
    const firstFrameImage = document.querySelector(".cn-frame__img");
    const heroBackground = document.querySelector("[data-hero-bg]")
      ? getComputedStyle(document.querySelector("[data-hero-bg]")).backgroundImage
      : "";
    const headerBottom = document.querySelector("header")?.getBoundingClientRect().bottom ?? 0;
    const headingTop = document.querySelector("h1")?.getBoundingClientRect().top ?? headerBottom;
    return {
      canonicalLinks,
      referrer,
      cspCount,
      colourScheme,
      hasFooter: Boolean(document.querySelector("footer")),
      horizontalOverflow: Math.max(
        0,
        document.documentElement.scrollWidth - document.documentElement.clientWidth,
      ),
      backgroundColour: getComputedStyle(document.body).backgroundColor,
      frameImagePresent: Boolean(firstFrameImage),
      firstFrameImageLoaded: firstFrameImage
        ? firstFrameImage.complete && firstFrameImage.naturalWidth > 0
        : null,
      heroUsesArtwork: heroBackground ? heroBackground.includes("url(") : null,
      headerBottom,
      headingTop,
      headingClearsHeader: headingTop >= headerBottom - 1,
    };
  });

  const interaction = await checkInteraction(page, route);
  const interactionFailed = interaction.endsWith("failed")
    || interaction.includes("did not")
    || interaction.includes("fewer than")
    || interaction.includes("still exposes");
  const canonicalOkay = expected === null
    ? state.canonicalLinks.length === 0
    : state.canonicalLinks.length === 1 && state.canonicalLinks[0] === expected;
  const passed = navigation?.status() < 400
    && consoleErrors.length === 0
    && failedRequests.length === 0
    && badResponses.length === 0
    && canonicalOkay
    && state.referrer === "strict-origin-when-cross-origin"
    && state.cspCount === 1
    && state.colourScheme === "dark"
    && state.hasFooter
    && state.horizontalOverflow <= 1
    && state.headingClearsHeader
    && state.firstFrameImageLoaded !== false
    && !interactionFailed;

  if (screenshotDir && screenshotRoutes.has(route)) {
    await page.evaluate(() => window.scrollTo({ top: 0, behavior: "instant" }));
    await page.waitForTimeout(100);
    fs.mkdirSync(screenshotDir, { recursive: true });
    const name = route.replace(/^\/|\.html$/g, "").replaceAll("/", "-") || "home";
    await page.screenshot({
      path: path.join(screenshotDir, `${name}-${viewport.name}.png`),
      fullPage: true,
    });
  }

  return {
    route,
    viewport: viewport.name,
    status: navigation?.status() ?? 0,
    title: await page.title(),
    ...state,
    interaction,
    consoleErrors,
    failedRequests,
    badResponses,
    canonicalOkay,
    passed,
  };
}

const browser = await chromium.launch(
  browserExecutable
    ? { executablePath: browserExecutable, headless: true }
    : { headless: true },
);

let failed = false;

try {
  for (const viewport of viewports) {
    const context = await browser.newContext({
      viewport: { width: viewport.width, height: viewport.height },
      colorScheme: viewport.colorScheme,
    });

    for (const route of routes) {
      const page = await context.newPage();
      const result = await capturePage(page, route, viewport);
      await page.close();

      console.log(JSON.stringify({
        route: result.route,
        viewport: result.viewport,
        status: result.status,
        title: result.title,
        interaction: result.interaction,
        canonicalOkay: result.canonicalOkay,
        cspCount: result.cspCount,
        overflow: result.horizontalOverflow,
        backgroundColour: result.backgroundColour,
        firstFrameImageLoaded: result.firstFrameImageLoaded,
        heroUsesArtwork: result.heroUsesArtwork,
        headerBottom: result.headerBottom,
        headingTop: result.headingTop,
        headingClearsHeader: result.headingClearsHeader,
        consoleErrors: result.consoleErrors.length,
        failedRequests: result.failedRequests.length,
        badResponses: result.badResponses.length,
        passed: result.passed,
      }));

      if (!result.passed) {
        failed = true;
        console.error(JSON.stringify(result, null, 2));
      }
    }

    await context.close();
  }
} finally {
  await browser.close();
}

if (failed) process.exit(1);
