import test from "node:test";
import assert from "node:assert/strict";
import { isLiveFeed } from "./liveFeedStatus.js";

test("does not report LIVE when the latest poll failed after a fresh snapshot", () => {
  const snapshot = { status: "success", feed: { status: "fresh" } };
  assert.equal(isLiveFeed(snapshot, false), false);
});

test("reports LIVE only when the latest poll succeeded and snapshot is fresh", () => {
  const snapshot = { status: "success", feed: { status: "fresh" } };
  assert.equal(isLiveFeed(snapshot, true), true);
});

test("does not report LIVE for stale or disconnected snapshots", () => {
  assert.equal(isLiveFeed({ status: "success", feed: { status: "stale" } }, true), false);
  assert.equal(isLiveFeed({ status: "success", feed: { status: "disconnected" } }, true), false);
  assert.equal(isLiveFeed(null, true), false);
});
