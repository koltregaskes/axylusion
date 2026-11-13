import test from "node:test";
import assert from "node:assert/strict";
import { auditGalleryIdentity, evaluateResult } from "../scripts/lib/gallery-smoke.mjs";

const plus = (id) => ({ id });
const minus = (id) => ({ id, media_status: "unavailable" });
const read = (items) => ({ ok: true, payload: { items } });
const dom = (ids, extra = {}) => ({
  galleryVisibleIds: ids,
  missingItemIdCardsFromDom: [],
  galleryCardCount: ids.length,
  ...extra,
});
const base = [plus("A"), minus("B")];

// These are the same 25 synthetic admission cases checked during the Chat review,
// now executable against the implementation without importing Playwright.
const cases = [
  ["valid case-normalised visible IDs", read(base), read(base), dom(["a"]), ["a", "b"], true],
  ["server source failed", { ok: false }, read(base), dom(["a"]), [], false, /server: source unavailable/],
  ["local source failed", read(base), { ok: false }, dom(["a"]), [], false, /local: source unavailable/],
  ["missing items", { ok: true, payload: {} }, read(base), dom(["a"]), [], false, /invalid items/],
  ["non-array items", { ok: true, payload: { items: {} } }, read(base), dom(["a"]), [], false, /invalid items/],
  ["null item", read([null]), read([null]), dom(["a"]), [], false, /invalid item/],
  ["numeric ID", read([{ id: 7 }]), read([{ id: 7 }]), dom(["7"]), [], false, /invalid gallery ID/],
  ["blank ID", read([{ id: " " }]), read([{ id: " " }]), dom([" "]), [], false, /invalid gallery ID/],
  ["numeric status", read([{ id: "a", media_status: 1 }]), read([{ id: "a", media_status: 1 }]), dom(["a"]), [], false, /invalid media_status/],
  ["canonical dataset collision", read([plus("A"), minus(" a ")]), read([plus("A"), minus(" a ")]), dom(["a"]), [], false, /duplicate canonical ID/],
  ["availability conflict", read(base), read([plus("A"), plus("B")]), dom(["a"]), [], false, /source conflict|availability conflict/],
  ["identity conflict", read(base), read([plus("A"), minus("C")]), dom(["a"]), [], false, /source conflict|availability conflict/],
  ["valid empty dataset retains nonempty policy", read([]), read([]), dom([]), [], false],
  ["all-unavailable dataset retains nonempty policy", read([minus("A")]), read([minus("A")]), dom([]), ["a"], false],
  ["known A becomes unavailable", read([minus("A"), plus("B")]), read([minus("A"), plus("B")]), dom(["b"]), ["a", "b"], true],
  ["unavailable item remains visible", read([minus("A"), plus("B")]), read([minus("A"), plus("B")]), dom(["a", "b"]), ["a", "b"], false],
  ["known B becomes available", read([plus("A"), plus("B")]), read([plus("A"), plus("B")]), dom(["a", "b"]), ["a", "b"], true],
  ["known A removed from current dataset", read([plus("B")]), read([plus("B")]), dom(["b"]), ["a", "b"], true],
  ["canonical DOM duplicate and missing B", read([plus("A"), plus("B")]), read([plus("A"), plus("B")]), dom(["A", "a"]), [], false],
  ["missing attribute and card-count reconciliation", read([plus("A"), plus("B")]), read([plus("A"), plus("B")]), dom(["a"], { galleryCardCount: 2, missingItemIdCardsFromDom: ["card2"] }), [], false],
  ["null status is unflagged", read([{ id: "a", media_status: null }]), read([plus("A")]), dom(["a"]), [], true],
  ["nonexact unavailable case is unflagged", read([{ id: "a", media_status: "Unavailable" }]), read([plus("A")]), dom(["a"]), [], true],
  ["invalid DOM ID", read([plus("a")]), read([plus("a")]), dom([null]), [], false, /invalid gallery ID/],
  ["mismatched DOM count", read([plus("a")]), read([plus("a")]), dom(["a"], { galleryCardCount: 2 }), [], false],
  ["invalid known ID", read([plus("a")]), read([plus("a")]), dom(["a"]), [null], false, /invalid gallery ID/],
];

for (const [name, server, local, snapshot, known, expected, reason] of cases) {
  test(name, () => {
    const result = auditGalleryIdentity(server, local, snapshot, known);
    assert.equal(result.passed, expected);
    if (reason) assert.match(result.validationError, reason);
    if (name.includes("dataset retains nonempty")) {
      assert.equal(result.validationError, undefined);
      assert.equal(result.cardCountOk, false);
      assert.equal(result.expectedCountOk, true);
    }
    if (name === "unavailable item remains visible") {
      assert.deepEqual(result.unavailableVisible, ["a"]);
    }
    if (name === "canonical DOM duplicate and missing B") {
      assert.deepEqual(result.duplicateIds, ["a"]);
      assert.deepEqual(result.missingIds, ["b"]);
    }
    if (name === "missing attribute and card-count reconciliation") {
      assert.equal(result.missingItemIdCount, 1);
      assert.deepEqual(result.missingIds, ["b"]);
    }
  });
}

const snapshot = (extra = {}) => ({
  path: "/gallery.html",
  consoleErrors: [],
  failedRequests: [],
  badResponses: [],
  serverGalleryRead: read(base),
  ...dom(["a"]),
  ...extra,
});
const options = { localGalleryRead: read(base), knownIds: ["a", "b"] };

test("gallery evaluator accepts valid sources and availability-derived frames", () => {
  const result = evaluateResult(snapshot(), { mode: "gallery" }, options);
  assert.equal(result.passed, true);
  assert.equal(result.summary, "clean");
  assert.equal(result.expectedVisibleCount, 1);
});

test("missing authoritative expectations cannot pass plausible counts", () => {
  const result = evaluateResult(snapshot({ serverGalleryRead: { ok: false } }), { mode: "gallery" }, options);
  assert.equal(result.passed, false);
  assert.match(result.validationError, /server: source unavailable/);
});

test("non-gallery clean page does not require gallery data", () => {
  assert.deepEqual(
    evaluateResult(snapshot({ path: "/about.html", serverGalleryRead: { ok: false } }), { mode: "clean" }),
    { passed: true, summary: "clean" },
  );
});

test("clean mode preserves strict console and network failure checks", () => {
  const result = evaluateResult(
    snapshot({ path: "/about.html", consoleErrors: ["error"], failedRequests: [{ url: "https://allowed.example/image" }] }),
    { mode: "clean", allowedHosts: ["allowed.example"] },
  );
  assert.equal(result.passed, false);
  assert.equal(result.summary, "unexpected runtime issues");
});

test("gallery check remains active if its mode is accidentally set to clean", () => {
  const result = evaluateResult(snapshot({ serverGalleryRead: { ok: false } }), { mode: "clean" }, options);
  assert.equal(result.passed, false);
  assert.match(result.validationError, /source unavailable/);
});

test("allowed network failure cannot hide gallery source failure diagnostics", () => {
  const result = evaluateResult(
    snapshot({ serverGalleryRead: { ok: false }, failedRequests: [{ url: "https://allowed.example/image" }] }),
    { mode: "gallery", allowedHosts: ["allowed.example"] },
    options,
  );
  assert.equal(result.passed, false);
  assert.match(result.summary, /^gallery expectations invalid/);
  assert.doesNotMatch(result.summary, /^allowed host failures only/);
});

test("gallery mode preserves the existing allowed-host runtime rule", () => {
  const result = evaluateResult(
    snapshot({ consoleErrors: ["resource error"], failedRequests: [{ url: "https://allowed.example/image" }] }),
    { mode: "gallery", allowedHosts: ["allowed.example"] },
    options,
  );
  assert.equal(result.passed, true);
  assert.equal(result.summary, "allowed host failures only (1)");
});

