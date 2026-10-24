import type { DemoProjectResponse, HealthResponse } from "./types";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "/api/v1"
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
export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
): Promise<T> {
  const headers = new Headers(init.headers);
  headers.set("Accept", "application/json");
  if (init.body && !headers.has("Content-Type"))
    headers.set("Content-Type", "application/json");

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/${path.replace(/^\/+/, "")}`, {
      ...init,
      headers,
      cache: "no-store",
      credentials: "include",
    });
  } catch (error) {
    if (
      init.signal?.aborted ||
      (error instanceof Error && error.name === "AbortError")
    )
      throw error;
    throw new ApiError(
      "The calculation service could not be reached. Please retry.",
      0,
    );
  }

  const payload: unknown = await response.json().catch(() => null);
  if (!response.ok) {
    if (response.status === 401 && path.startsWith('/projects/') && typeof window !== 'undefined') {
      window.location.assign('/login');
    }
    const errorBody =
      payload && typeof payload === "object" && "error" in payload
        ? payload.error
        : null;
    const serverMessage =
      errorBody &&
      typeof errorBody === "object" &&
      "message" in errorBody &&
      typeof errorBody.message === "string"
        ? errorBody.message
        : null;
    const detail =
      payload && typeof payload === "object" && "detail" in payload
        ? payload.detail
        : payload;
    const message =
      response.status === 501
        ? "This calculation is currently unavailable."
        : (serverMessage ?? `The API request failed (${response.status}).`);
    throw new ApiError(message, response.status, detail);
  }
  if (payload === null)
    throw new ApiError(
      "The API returned an invalid JSON response.",
      response.status,
    );
  // Runtime shape checks are performed by the resource adapters below.
  return payload as T;
}

export const getHealth = (signal?: AbortSignal) =>
  apiRequest<HealthResponse>("/health", { signal });
export const getDemoProject = (signal?: AbortSignal) =>
  apiRequest<DemoProjectResponse>("/projects/demo", { signal });

import type {
  ApiEnvelope,
  Scenario,
  ScenarioCreate,
  EvaluationData,
  PortfolioRequest,
  PortfolioResult,
  RescueRequest,
  InfrastructureEvent,
  GeoContext,
  RescueResult,
} from "./types";
import {
  record,
  isEnvelope,
  isProject,
  isScenario,
  isEvaluation,
  isPortfolio,
  isRescue,
  isGeoContext,
} from "./guards";
import { FEATURE_SNAPSHOT_ID } from "./workspace-model";

async function checked<T>(
  path: string,
  guard: (x: unknown) => x is T,
  init: RequestInit = {},
): Promise<ApiEnvelope<T>> {
  const result = await apiRequest<unknown>(path, init);
  if (!isEnvelope(result, guard))
    throw new ApiError(
      "The API returned incomplete or unsupported data. No results were applied.",
      502,
    );
  return result;
}
const post = (body: unknown, signal?: AbortSignal): RequestInit => ({
  method: "POST",
  body: JSON.stringify(body),
  signal,
});
export const loadProject = (signal?: AbortSignal) =>
  checked("/projects/demo", isProject, { signal });
export const getScenarios = (signal?: AbortSignal) =>
  checked(
    "/projects/demo/scenarios",
    (x): x is Scenario[] => Array.isArray(x) && x.every(isScenario),
    { signal },
  );
export const createScenario = (body: ScenarioCreate, signal?: AbortSignal) =>
  checked("/projects/demo/scenarios", isScenario, post(body, signal));
export const evaluateScenario = (scenarioId: string, signal?: AbortSignal) =>
  checked(
    "/projects/demo/evaluate",
    isEvaluation,
    post(
      { scenario_id: scenarioId, feature_snapshot_id: FEATURE_SNAPSHOT_ID },
      signal,
    ),
  );
export const optimisePortfolio = (
  body: PortfolioRequest,
  signal?: AbortSignal,
) => checked("/projects/demo/portfolios", isPortfolio, post(body, signal));
export const requestRescue = (
  siteId: string,
  body: RescueRequest,
  signal?: AbortSignal,
) =>
  checked(
    "/projects/demo/sites/" + encodeURIComponent(siteId) + "/rescue",
    isRescue,
    post(body, signal),
  );
/** Period identifiers are frozen in the canonical weight and profile schema. */
export const getDayparts = (
  evaluationId: string,
  bin: string,
  signal?: AbortSignal,
) =>
  apiRequest<unknown>(
    "/projects/demo/dayparts?" +
      new URLSearchParams({ evaluation_id: evaluationId, time_bin: bin }),
    { signal },
  );
export const getInfrastructure = (signal?: AbortSignal) =>
  checked(
    "/projects/demo/infrastructure",
    (x): x is InfrastructureEvent[] =>
      Array.isArray(x) &&
      x.every(
        (e) =>
          record(e) &&
          typeof e.infra_project_id === "string" &&
          typeof e.name === "string" &&
          typeof e.status === "string" &&
          typeof e.source_id === "string" &&
          typeof e.hypothetical_demo === "boolean" &&
          ["REAL", "SYNTHETIC", "ASSUMED"].includes(String(e.source_status)) &&
          (e.expected_open_date === null ||
            typeof e.expected_open_date === "string") &&
          (e.assumed_demo_open_date === null ||
            typeof e.assumed_demo_open_date === "string"),
      ),
    { signal },
  );

export async function getSavedReport(
  evaluationId: string,
  runId: string,
  signal?: AbortSignal,
) {
  let response: Response;
  try {
    response = await fetch(
      API_BASE_URL +
        "/projects/demo/reports/" +
        encodeURIComponent(evaluationId) +
        "?" +
        new URLSearchParams({ portfolio_run_id: runId }),
      { signal, cache: "no-store", credentials: "include" },
    );
  } catch (error) {
    if (signal?.aborted) throw error;
    throw new ApiError(
      "Could not reach the API. Check that the backend is running.",
      0,
    );
  }
  if (!response.ok)
    throw new ApiError(
      response.status === 404 || response.status === 501
        ? "A saved report is not available for this investment case."
        : "Report download failed. Try again.",
      response.status,
    );
  const type = response.headers.get("content-type") ?? "";
  if (!type.includes("text/html") && !type.includes("application/json"))
    throw new ApiError("The report format is not supported.", 502);
  const blob = await response.blob();
  const text = await blob.text();
  if (!text.includes(evaluationId) || !text.includes(runId))
    throw new ApiError(
      "The report does not identify the active evaluation and portfolio. Download was stopped.",
      409,
    );
  return { blob, text, type };
}

export const getGeoContext = (evaluationId: string, signal?: AbortSignal) =>
  checked(
    "/projects/demo/features?" +
      new URLSearchParams({ evaluation_id: evaluationId }),
    isGeoContext,
    { signal },
  );
