// API client: base URL from NEXT_PUBLIC_API_URL, access token in memory only,
// silent refresh through the HttpOnly refresh-token cookie.

export const API_URL = (process.env.NEXT_PUBLIC_API_URL || "http://localhost:8001").replace(/\/$/, "");

// Never persisted: a page reload gets a fresh one from the refresh cookie.
let accessToken: string | null = null;
// The refresh token rotates on every use, so concurrent refreshes must share one request.
let refreshing: Promise<string | null> | null = null;

export function hasAccessToken(): boolean {
  return accessToken !== null;
}

async function refreshAccessToken(): Promise<string | null> {
  if (!refreshing) {
    refreshing = (async () => {
      try {
        const res = await fetch(`${API_URL}/api/v1/auth/refresh`, { method: "POST", credentials: "include" });
        accessToken = res.ok ? (await res.json()).access_token : null;
      } catch {
        accessToken = null;
      }
      return accessToken;
    })().finally(() => {
      refreshing = null;
    });
  }
  return refreshing;
}

/** fetch() against the API with the access token; refreshes it once on 401. */
export async function apiFetch(path: string, init: RequestInit = {}): Promise<Response> {
  if (!accessToken) await refreshAccessToken();

  const send = () =>
    fetch(`${API_URL}${path}`, {
      ...init,
      credentials: "include",
      headers: {
        ...(init.headers || {}),
        ...(accessToken ? { Authorization: `Bearer ${accessToken}` } : {}),
      },
    });

  let res = await send();
  if (res.status === 401 && (await refreshAccessToken())) {
    res = await send();
  }
  return res;
}

export async function login(email: string, password: string): Promise<boolean> {
  const res = await fetch(`${API_URL}/api/v1/auth/login`, {
    method: "POST",
    credentials: "include", // stores the HttpOnly refresh cookie
    headers: { "Content-Type": "application/json" },
    // The API's LoginRequest field is "username"; its value is the email.
    body: JSON.stringify({ username: email, password }),
  });
  if (!res.ok) return false;
  accessToken = (await res.json()).access_token;
  return true;
}

export async function logout(): Promise<void> {
  accessToken = null;
  try {
    await fetch(`${API_URL}/api/v1/auth/logout`, { method: "POST", credentials: "include" });
  } catch {
    // Already logged out locally; the cookie expires on its own.
  }
}
