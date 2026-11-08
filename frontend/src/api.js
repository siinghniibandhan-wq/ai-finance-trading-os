// ============================================================
// FINANCIAL OS — AUTHENTICATED API CLIENT
// Same-origin API by default; VITE_API_BASE_URL can override it.
// ============================================================

export const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ||
  (typeof window !== "undefined" ? window.location.origin : "http://localhost")
).replace(/\/+$/, "");

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

  // Clear salary details on logout.
  try {
    Object.keys(localStorage)
      .filter((key) =>
        key.startsWith("financial-os:salary-components:")
      )
      .forEach((key) => localStorage.removeItem(key));
  } catch {
    // Storage may be unavailable.
  }
}

// ============================================================
// AUTHENTICATED API REQUEST
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

// ============================================================
// HUMAN-READABLE ERRORS
// ============================================================

const STATUS_MESSAGES = {
  400: "The request could not be completed. Please check the details and try again.",
  401: "Your session has expired or the sign-in details are not correct. Please sign in again.",
  403: "You do not have permission to do this.",
  404: "We could not find what you asked for.",
  405: "This action is not available.",
  409: "This conflicts with something that already exists. Please check and try again.",
  413: "The information you sent is too large.",
  422: "Some of the details are missing or not valid. Please check the form.",
  429: "Too many attempts. Please wait a little while and try again.",
  500: "Something went wrong on our server. Please try again in a moment.",
  502: "A connected service (such as your broker) did not respond correctly. Please try again shortly.",
  503: "This service is temporarily unavailable or not set up yet. Please try again later.",
  504: "The service took too long to respond. Please try again.",
};

const GENERIC_SERVER_TEXT =
  /^(internal server error|bad gateway|service unavailable|gateway timeout|not found|bad request|unauthorized|forbidden|method not allowed|unprocessable entity|conflict)\.?$/i;

function humanizeField(path) {
  const parts = Array.isArray(path)
    ? path.filter(
        (p) =>
          p !== "body" &&
          p !== "query" &&
          typeof p === "string"
      )
    : [];

  const name = parts[parts.length - 1];

  if (!name) return "";

  const text = name.replace(/_/g, " ");
  return text.charAt(0).toUpperCase() + text.slice(1);
}

export function friendlyErrorMessage(status, data) {
  const detail =
    data && typeof data === "object" ? data.detail : undefined;

  if (
    typeof detail === "string" &&
    detail.trim() &&
    !GENERIC_SERVER_TEXT.test(detail.trim())
  ) {
    return detail.trim();
  }

  if (Array.isArray(detail) && detail.length) {
    const lines = detail.slice(0, 3).map((item) => {
      const field = humanizeField(item?.loc);
      const message = String(
        item?.msg || "is not valid"
      ).replace(/^Value error, /, "");

      return field ? `${field}: ${message}` : message;
    });

    return lines.join(". ") + ".";
  }

  if (
    detail &&
    typeof detail === "object" &&
    typeof detail.message === "string" &&
    detail.message.trim()
  ) {
    return detail.message.trim();
  }

  return (
    STATUS_MESSAGES[status] ||
    (status >= 500
      ? STATUS_MESSAGES[500]
      : "The request could not be completed. Please try again.")
  );
}

// ============================================================
// NETWORK ERROR HANDLING
// ============================================================

export function describeError(
  error,
  fallback = "Something went wrong. Please try again."
) {
  const message = String(error?.message || "");

  if (
    error instanceof TypeError ||
    /failed to fetch|networkerror|load failed|network request failed/i.test(
      message
    )
  ) {
    return "Cannot reach the server. Please check your internet connection and try again.";
  }

  return message || fallback;
}
