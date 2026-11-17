export function isLiveFeed(snapshot, lastPollSucceeded) {
  return Boolean(
    lastPollSucceeded
    && snapshot?.status === "success"
    && snapshot?.feed?.status === "fresh"
  );
}
