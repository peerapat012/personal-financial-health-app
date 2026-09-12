import type { ErrorEnvelope } from "@/lib/api-types";

const API_BASE_URL = (
  import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"
).replace(/\/$/, "");

let token: string | null = null;

export class ApiError extends Error {
  constructor(
    message: string,
    readonly status: number,
    readonly code = "REQUEST_FAILED",
    readonly fields?: Record<string, string>,
  ) {
    super(message);
  }
}

export function setApiToken(value: string) {
  token = value;
}

export function clearApiToken() {
  token = null;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const controller = new AbortController();
  const requestToken = token;
  const timeout = window.setTimeout(() => controller.abort(), 20_000);

  try {
    const headers = new Headers(init.headers);
    headers.set("Accept", "application/json");
    if (init.body) headers.set("Content-Type", "application/json");
    if (requestToken) headers.set("Authorization", `Bearer ${requestToken}`);

    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      headers,
      signal: controller.signal,
    });
    const body =
      response.status === 204
        ? null
        : await response.json().catch(() => null);

    if (!response.ok) {
      if (response.status === 401 && requestToken && token === requestToken && !path.startsWith("/auth/")) {
        window.dispatchEvent(new Event("session-expired"));
      }
      const error = (body as ErrorEnvelope | null)?.error;
      throw new ApiError(
        error?.message ?? "Request failed",
        response.status,
        error?.code,
        error?.fields,
      );
    }

    return body as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    if (error instanceof DOMException && error.name === "AbortError") {
      throw new ApiError("Request timed out", 0, "TIMEOUT");
    }
    throw new ApiError("API is unavailable", 0, "NETWORK_ERROR");
  } finally {
    window.clearTimeout(timeout);
  }
}
