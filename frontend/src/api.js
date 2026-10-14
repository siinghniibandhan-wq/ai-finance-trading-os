// ============================================================
// FINANCIAL OS — AUTHENTICATED API CLIENT
// Attaches the current session's Bearer token to backend requests.
// ============================================================

export const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL ||
  "https://wealthmanager.duckdns.org";

// ============================================================
// SESSION MANAGEMENT
// ============================================================

export function getAccessToken() {
  return sessionStorage.getItem("financial_os_access_token") || "";
}

export function getCurrentUser() {
  try {
    const raw = sessionStorage.getItem("financial_os_user");
    return raw ? JSON.parse(raw) : null;
  } catch {
    return null;
  }
}

export function getCurrentUserId() {
  const id = Number(getCurrentUser()?.id);
  return Number.isInteger(id) && id > 0 ? id : 0;
}

// ============================================================
// SAVE LOGIN SESSION
// ============================================================

export function saveSession(payload) {
  if (!payload?.access_token || !payload?.user?.id) {
    throw new Error("The login response did not contain a valid session.");
  }

  sessionStorage.setItem(
    "financial_os_access_token",
    payload.access_token
  );

  sessionStorage.setItem(
    "financial_os_user",
    JSON.stringify(payload.user)
  );
}

// ============================================================
// LOGOUT
// ============================================================

export function clearSession() {
  sessionStorage.removeItem("financial_os_access_token");
  sessionStorage.removeItem("financial_os_user");
}

// ============================================================
// AUTHENTICATED API REQUEST
// Automatically attaches the Bearer token to requests sent
// to the configured backend API.
// ============================================================

export async function apiFetch(input, init = {}) {
  const requestUrl =
    typeof input === "string" || input instanceof URL
      ? new URL(String(input), window.location.href)
      : new URL(input.url, window.location.href);

  const apiOrigin = new URL(API_BASE_URL).origin;

  const headers = new Headers(
    init.headers ||
      (typeof Request !== "undefined" && input instanceof Request
        ? input.headers
        : undefined)
  );

  if (requestUrl.origin === apiOrigin) {
    const token = getAccessToken();

    if (token && !headers.has("Authorization")) {
      headers.set("Authorization", `Bearer ${token}`);
    }
  }

  return fetch(input, {
    ...init,
    headers,
  });
}
