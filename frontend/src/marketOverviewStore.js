import { useSyncExternalStore } from "react";
import { loadMarketOverview } from "./features/advanced-chart/api.js";
import { mergeMarketOverview } from "./marketOverviewState.js";

const REFRESH_INTERVAL_MS = 30000;

export function createMarketOverviewStore(fetchOverview = loadMarketOverview, intervalMs = REFRESH_INTERVAL_MS) {
  let snapshot = { data: null, loading: false, error: "", updatedAt: null };
  let inFlight = null;
  let timer = null;
  let started = false;
  const listeners = new Set();

  const emit = () => listeners.forEach((listener) => listener());
  const getSnapshot = () => snapshot;

  const refresh = () => {
    if (inFlight) return inFlight;
    snapshot = { ...snapshot, loading: snapshot.data === null, error: "" };
    emit();
    inFlight = Promise.resolve()
      .then(() => fetchOverview())
      .then((next) => {
        snapshot = {
          data: mergeMarketOverview(snapshot.data, next),
          loading: false,
          error: Array.isArray(next?.errors) && next.errors.length
            ? "Some market sources failed; retained values are marked stale."
            : "",
          updatedAt: next?.last_updated || new Date().toISOString(),
        };
        emit();
        return snapshot.data;
      })
      .catch((error) => {
        snapshot = {
          ...snapshot,
          loading: false,
          error: error?.message || "Unable to refresh market overview.",
        };
        emit();
        throw error;
      })
      .finally(() => { inFlight = null; });
    return inFlight;
  };

  const start = () => {
    if (started || typeof document === "undefined") return;
    started = true;
    void refresh().catch(() => {});
    timer = window.setInterval(() => {
      if (document.visibilityState === "visible") void refresh().catch(() => {});
    }, intervalMs);
    document.addEventListener("visibilitychange", onVisibilityChange);
  };

  const onVisibilityChange = () => {
    if (document.visibilityState === "visible") void refresh().catch(() => {});
  };

  const subscribe = (listener) => {
    listeners.add(listener);
    start();
    return () => { listeners.delete(listener); };
  };

  return { subscribe, getSnapshot, refresh };
}

export const marketOverviewStore = createMarketOverviewStore();

export function useMarketOverview() {
  const state = useSyncExternalStore(
    marketOverviewStore.subscribe,
    marketOverviewStore.getSnapshot,
    marketOverviewStore.getSnapshot,
  );
  return { ...state, refresh: marketOverviewStore.refresh };
}
