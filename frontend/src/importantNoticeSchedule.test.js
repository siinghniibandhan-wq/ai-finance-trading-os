import test from "node:test";
import assert from "node:assert/strict";
import {
  dismissImportantNotice,
  shouldShowImportantNotice,
  shouldRenderImportantNotice,
} from "./importantNoticeSchedule.js";

const makeStorage = () => {
  const values = new Map();
  return {
    getItem: (key) => values.has(key) ? values.get(key) : null,
    setItem: (key, value) => values.set(key, String(value)),
  };
};

test("notice is shown until dismissed, then suppressed for the same local day", () => {
  const storage = makeStorage();
  const now = new Date(2026, 10, 13, 9, 30);
  assert.equal(shouldShowImportantNotice(storage, now), true);
  dismissImportantNotice(storage, now);
  assert.equal(shouldShowImportantNotice(storage, new Date(2026, 10, 13, 21, 0)), false);
});

test("notice is shown again on the next local calendar day", () => {
  const storage = makeStorage();
  dismissImportantNotice(storage, new Date(2026, 10, 13, 23, 50));
  assert.equal(shouldShowImportantNotice(storage, new Date(2026, 10, 14, 0, 5)), true);
});

test("storage failures do not prevent the notice from rendering", () => {
  const unavailableStorage = {
    getItem() { throw new Error("storage blocked"); },
    setItem() { throw new Error("storage blocked"); },
  };
  assert.equal(shouldShowImportantNotice(unavailableStorage), true);
  assert.equal(dismissImportantNotice(unavailableStorage), false);
});

test("notice is eligible only on the exact public homepage path", () => {
  assert.equal(shouldRenderImportantNotice("/"), true);
  assert.equal(shouldRenderImportantNotice("/?source=direct"), true);
  assert.equal(shouldRenderImportantNotice("/login"), false);
  assert.equal(shouldRenderImportantNotice("/register"), false);
  assert.equal(shouldRenderImportantNotice("/app"), false);
  assert.equal(shouldRenderImportantNotice("/app/dashboard"), false);
  assert.equal(shouldRenderImportantNotice("/contact"), false);
});
