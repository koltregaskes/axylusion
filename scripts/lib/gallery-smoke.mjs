// Repository-bound smoke policy: fetched and local ID/availability maps must agree.
// An absent or malformed source is a failure, never a count-based fallback.
function galleryId(value) {
  if (typeof value !== "string" || !value.trim()) {
    throw new Error("invalid gallery ID");
  }
  return value.trim().toLowerCase();
}

function galleryMap(read, label) {
  if (read?.ok !== true) {
    throw new Error(`${label}: source unavailable`);
  }
  const payload = read.payload;
  if (!payload || typeof payload !== "object" ||
      Array.isArray(payload) || !Array.isArray(payload.items)) {
    throw new Error(`${label}: invalid items array`);
  }

  const map = new Map();
  for (const item of payload.items) {
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      throw new Error(`${label}: invalid item`);
    }
    const id = galleryId(item.id);
    if (map.has(id)) {
      throw new Error(`${label}: duplicate canonical ID`);
    }
    if (item.media_status != null &&
        typeof item.media_status !== "string") {
      throw new Error(`${label}: invalid media_status`);
    }
    map.set(id, item.media_status === "unavailable");
  }
  return map;
}

function auditGalleryIdentity(serverRead, localRead, result, knownIds) {
  try {
    const server = galleryMap(serverRead, "server");
    const local = galleryMap(localRead, "local");
    if (server.size !== local.size ||
        [...server].some(([id, flag]) => local.get(id) !== flag)) {
      throw new Error("server/local identity or availability conflict");
    }

    const ids = result.galleryVisibleIds;
    const missing = result.missingItemIdCardsFromDom;
    const count = result.galleryCardCount;
    if (!Array.isArray(ids) || !Array.isArray(missing) ||
        !Number.isInteger(count) || count < 0 ||
        !Array.isArray(knownIds)) {
      throw new Error("invalid DOM snapshot or known-ID configuration");
    }

    const expected = new Set(
      [...server].filter(([, unavailable]) => !unavailable)
        .map(([id]) => id)
    );
    const visible = new Set();
    const duplicateIds = [];
    for (const raw of ids) {
      const id = galleryId(raw);
      if (visible.has(id)) duplicateIds.push(id);
      visible.add(id);
    }

    const missingIds = [...expected].filter(id => !visible.has(id));
    const unexpectedIds = [...visible].filter(id => !expected.has(id));
    const unavailableVisible = [...visible]
      .filter(id => server.get(id) === true);
    const explicitChecksOk = knownIds.every(raw => {
      const id = galleryId(raw);
      return visible.has(id) === expected.has(id);
    });
    const cardCountOk = count > 0;
    const expectedCountOk = count === expected.size;
    const missingItemIdCount = missing.length;
    const passed =
      cardCountOk && expectedCountOk && count === ids.length &&
      missingItemIdCount === 0 && duplicateIds.length === 0 &&
      missingIds.length === 0 && unexpectedIds.length === 0 &&
      unavailableVisible.length === 0 && explicitChecksOk;

    return {
      passed, cardCountOk, expectedCountOk,
      expectedVisibleCount: expected.size,
      missingItemIdCount, duplicateIds, missingIds, unexpectedIds,
      unavailableVisible, explicitChecksOk,
    };
  } catch (error) {
    return { passed: false, validationError: error.message };
  }
}

export const KNOWN_FRAME_IDS = [
  "89cf68fa-4ba7-436d-85b7-764bc8c0c43f",
  "bcf7ef43-a942-4255-bd47-a0baf1f820d2",
  "68a3ddec-240a-4922-b99a-5c2400bbbf26",
];

function extractHost(urlString) {
  try { return new URL(urlString).hostname; } catch { return ""; }
}

function identitySummary(result, identity) {
  if (identity.validationError) return "gallery expectations invalid: " + identity.validationError;
  if (!identity.cardCountOk) return "gallery has 0 cards";
  if (!identity.expectedCountOk) {
    return "gallery shows " + result.galleryCardCount + " cards, expected " + identity.expectedVisibleCount;
  }
  if (identity.missingItemIdCount > 0) {
    return "gallery has " + identity.missingItemIdCount + " card(s) missing data-item-id";
  }
  if (identity.duplicateIds.length > 0) {
    return "gallery has " + identity.duplicateIds.length + " duplicate ID(s)";
  }
  if (identity.missingIds.length > 0 || identity.unexpectedIds.length > 0) {
    return "gallery IDs mismatch: " + identity.missingIds.length + " missing, " + identity.unexpectedIds.length + " unexpected";
  }
  if (identity.unavailableVisible.length > 0) {
    return "gallery shows " + identity.unavailableVisible.length + " unavailable item(s)";
  }
  if (!identity.explicitChecksOk) return "gallery explicit ID assertions failed";
  return "gallery card and ID counts differ";
}

export function evaluateResult(result, check, options = {}) {
  const problemUrls = [
    ...result.failedRequests.map((entry) => entry.url),
    ...result.badResponses.map((entry) => entry.url),
  ];
  const isGallery = result.path.endsWith("/gallery.html");
  if (check.mode === "clean" && !isGallery) {
    const passed = result.consoleErrors.length === 0 && problemUrls.length === 0;
    return { passed, summary: passed ? "clean" : "unexpected runtime issues" };
  }

  const allowedHosts = new Set(check.allowedHosts || []);
  const disallowedUrls = problemUrls.filter((url) => !allowedHosts.has(extractHost(url)));
  const onlyAllowedFailures = check.mode === "clean"
    ? problemUrls.length === 0
    : disallowedUrls.length === 0;
  const consoleOkay = check.mode === "clean"
    ? result.consoleErrors.length === 0
    : result.consoleErrors.length === 0 || (problemUrls.length > 0 && onlyAllowedFailures);
  const runtimePassed = onlyAllowedFailures && consoleOkay;
  const identity = isGallery
    ? auditGalleryIdentity(
      result.serverGalleryRead,
      options.localGalleryRead,
      result,
      options.knownIds ?? KNOWN_FRAME_IDS,
    )
    : { passed: true };
  const passed = runtimePassed && identity.passed;
  let summary = "clean";
  if (!identity.passed) {
    // An allowed network failure must not hide an identity/source failure.
    summary = identitySummary(result, identity);
  } else if (!runtimePassed) {
    summary = "unexpected runtime issues";
  } else if (problemUrls.length > 0 && onlyAllowedFailures) {
    summary = "allowed host failures only (" + problemUrls.length + ")";
  }
  return { ...identity, passed, summary, disallowedUrls };
}

export { galleryId, galleryMap, auditGalleryIdentity };

