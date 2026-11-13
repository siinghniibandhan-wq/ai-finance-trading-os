const STORAGE_KEY = "financial-os:order-flow-preferences:v1";

export function loadOrderFlowPreferences(storage = globalThis.localStorage) {
  try {
    const value = JSON.parse(storage?.getItem(STORAGE_KEY) || "null");
    return {
      scope: value?.scope === "nifty50" ? "nifty50" : "fno",
      selectedSymbol: typeof value?.selectedSymbol === "string" ? value.selectedSymbol : "NIFTY",
    };
  } catch {
    return { scope: "fno", selectedSymbol: "NIFTY" };
  }
}

export function saveOrderFlowPreferences(preferences, storage = globalThis.localStorage) {
  try {
    storage?.setItem(STORAGE_KEY, JSON.stringify({
      scope: preferences.scope === "nifty50" ? "nifty50" : "fno",
      selectedSymbol: String(preferences.selectedSymbol || "NIFTY"),
    }));
    return true;
  } catch {
    return false;
  }
}
