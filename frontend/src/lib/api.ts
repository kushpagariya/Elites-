import type { DemoProjectResponse, HealthResponse } from "./types";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"
).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

/** T is the complete response envelope, not only its data property. */
export async function apiRequest<T>(path: string, init: RequestInit = {}): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type")) headers.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/${path.replace(/^\/+/, "")}`, {
      ...init,
      headers,
      cache: "no-store",
    });
  } catch (error) {
    if (init.signal?.aborted || (error instanceof Error && error.name === "AbortError")) throw error;
    throw new ApiError("Could not reach the API. Check that the backend is running.", 0);
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    const errorBody = payload && typeof payload === "object" && "error" in payload ? payload.error : null;
    const serverMessage = errorBody && typeof errorBody === "object" && "message" in errorBody && typeof errorBody.message === "string"
      ? errorBody.message : null;
    const detail = payload && typeof payload === "object" && "detail" in payload ? payload.detail : payload;
    const message = response.status === 501
      ? "This capability is awaiting implementation."
      : serverMessage ?? `The API request failed (${response.status}).`;
    throw new ApiError(message, response.status, detail);
  }
  if (payload === null) throw new ApiError("The API returned an invalid JSON response.", response.status);
  // This scaffold's two response types mirror CONTRACT.md. Generate analytics types from OpenAPI.
  return payload as T;
}

export const getHealth = (signal?: AbortSignal) => apiRequest<HealthResponse>("/health", { signal });
export const getDemoProject = (signal?: AbortSignal) => apiRequest<DemoProjectResponse>("/projects/demo", { signal });
