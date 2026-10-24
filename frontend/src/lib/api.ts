import type {
  DemoProjectResponse, HealthResponse, ScenarioCreate, ScenarioResponse,
  ScenarioListResponse, EvaluateRequest, EvaluationResponse, SiteAnalysisResponse,
  RankingResponse, PortfolioRequest, PortfolioResponse, RescueRequest, RescueResponse,
} from "./types";

export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://127.0.0.1:8000/api/v1"
).replace(/\/+$/, "");

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status: number,
    public readonly details?: unknown,
    public readonly code?: string,
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
    const code = errorBody && typeof errorBody === "object" && "code" in errorBody && typeof errorBody.code === "string"
      ? errorBody.code : undefined;
    throw new ApiError(message, response.status, detail, code);
  }
  if (payload === null) throw new ApiError("The API returned an invalid JSON response.", response.status);
  // These interfaces mirror the backend contract; UI must also match response IDs.
  return payload as T;
}

export const getHealth = (signal?: AbortSignal) => apiRequest<HealthResponse>("/health", { signal });
export const getDemoProject = (signal?: AbortSignal) => apiRequest<DemoProjectResponse>("/projects/demo", { signal });

const projectPath = (id: string) => `/projects/${encodeURIComponent(id)}`;
type MutationOptions = { signal?: AbortSignal; idempotencyKey?: string };

function post<T>(path: string, body: unknown, options: MutationOptions = {}) {
  return apiRequest<T>(path, {
    method: "POST",
    body: JSON.stringify(body),
    signal: options.signal,
    headers: options.idempotencyKey ? { "Idempotency-Key": options.idempotencyKey } : undefined,
  });
}

export const getScenarios = (projectId: string, signal?: AbortSignal) =>
  apiRequest<ScenarioListResponse>(`${projectPath(projectId)}/scenarios`, { signal });
export const getScenario = (projectId: string, scenarioId: string, signal?: AbortSignal) =>
  apiRequest<ScenarioResponse>(`${projectPath(projectId)}/scenarios/${encodeURIComponent(scenarioId)}`, { signal });
export const createScenario = (projectId: string, body: ScenarioCreate, options?: MutationOptions) =>
  post<ScenarioResponse>(`${projectPath(projectId)}/scenarios`, body, options);
export const evaluateProject = (projectId: string, body: EvaluateRequest, options?: MutationOptions) =>
  post<EvaluationResponse>(`${projectPath(projectId)}/evaluate`, body, options);
export const getEvaluation = (projectId: string, evaluationId: string, signal?: AbortSignal) =>
  apiRequest<EvaluationResponse>(`${projectPath(projectId)}/evaluations/${encodeURIComponent(evaluationId)}`, { signal });
export const getSiteAnalysis = (projectId: string, siteId: string, evaluationId: string, signal?: AbortSignal) =>
  apiRequest<SiteAnalysisResponse>(`${projectPath(projectId)}/sites/${encodeURIComponent(siteId)}/analysis?${new URLSearchParams({ evaluation_id: evaluationId })}`, { signal });
export const getRankings = (projectId: string, evaluationId: string, signal?: AbortSignal) =>
  apiRequest<RankingResponse>(`${projectPath(projectId)}/rankings?${new URLSearchParams({ evaluation_id: evaluationId })}`, { signal });
export const requestRescue = (projectId: string, siteId: string, body: RescueRequest, options?: MutationOptions) =>
  post<RescueResponse>(`${projectPath(projectId)}/sites/${encodeURIComponent(siteId)}/rescue`, body, options);
export const createPortfolio = (projectId: string, body: PortfolioRequest, options?: MutationOptions) =>
  post<PortfolioResponse>(`${projectPath(projectId)}/portfolios`, body, options);
export const getPortfolio = (projectId: string, portfolioRunId: string, signal?: AbortSignal) =>
  apiRequest<PortfolioResponse>(`${projectPath(projectId)}/portfolios/${encodeURIComponent(portfolioRunId)}`, { signal });
export function getReportUrl(projectId: string, evaluationId: string, portfolioRunId?: string, format: "html" | "json" = "html") {
  const params = new URLSearchParams({ format });
  if (portfolioRunId) params.set("portfolio_run_id", portfolioRunId);
  return `${API_BASE_URL}${projectPath(projectId)}/reports/${encodeURIComponent(evaluationId)}?${params}`;
}
