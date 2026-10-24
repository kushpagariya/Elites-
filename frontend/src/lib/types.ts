/** Wire units: INR, square metres, WGS84 coordinates, decimal fractions. */
export type Provenance = "REAL" | "SYNTHETIC" | "ASSUMED";

export interface CandidateSite {
  site_id: string;
  name: string;
  latitude: number;
  longitude: number;
  store_size_sqm: number;
  capex_inr: number;
  monthly_rent_inr: number;
  annual_opex_inr: number;
  gross_margin_fraction: number;
}

export interface ExistingStore {
  store_id: string;
  name: string;
  latitude: number;
  longitude: number;
  store_size_sqm: number;
  theta: number;
  variable_contribution_margin: number;
}

export interface Project {
  project_id: string;
  city: string;
  category: string;
  budget_inr: number;
  discount_rate_fraction: number;
  projection_years: number;
  sites: CandidateSite[];
  stores: ExistingStore[];
  source_status: Provenance;
}

export interface ResponseMeta {
  contract_version: "1";
  fixture_id: "demo-1";
  scenario_id?: string;
}

export interface ApiEnvelope<T> {
  data: T;
  meta: ResponseMeta;
}

export type DemoProject = Project & {
  project_id: "demo";
  source_status: "SYNTHETIC";
};
export type HealthResponse = ApiEnvelope<{
  status: "ok";
  implementation_status: "scaffold";
}>;
export type DemoProjectResponse = ApiEnvelope<DemoProject>;

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: { field: string; reason: string }[];
  };
}

/** Canonical analytical shapes mirror backend/app/schemas.py; endpoint availability is separate. */
export interface SiteOverride {
  monthly_rent_inr?: number | null;
  sales_multiplier?: number | null;
}

export interface Assumptions {
  demand_multiplier: number;
  rent_multiplier: number;
  site_overrides: Record<string, SiteOverride>;
  infrastructure_state: "current" | "opens" | "delayed";
  infrastructure_effect_fraction: number;
  opening_date: string | null;
  delay_months: number;
}

export interface ScenarioCreate {
  base_scenario_id?: string;
  name: string;
  budget_inr?: number | null;
  assumptions: Assumptions;
}

export interface Scenario {
  scenario_id: string;
  project_id: string;
  base_scenario_id: string | null;
  name: string;
  budget_inr: number;
  assumptions: Assumptions;
}

export interface EvaluateRequest {
  scenario_id?: string;
  feature_snapshot_id?: string;
}

export type Diagnosis = "VIABLE" | "AT_RISK" | "REJECTED" | "REVIEW_REQUIRED";
export type RescueStatus =
  | "NOT_REQUESTED"
  | "SOLVED"
  | "NOT_RECOVERABLE_WITHIN_BOUNDS"
  | "NON_MONOTONIC";

export interface FailFastDiagnosis {
  status: Diagnosis;
  failed_rule_ids: string[];
  reasons: string[];
  max_viable_monthly_rent_inr: number | null;
  required_sales_multiplier: number | null;
  rescue_status: RescueStatus;
}

export interface SiteAnalysis {
  site_id: string;
  annual_revenue_inr: number;
  lost_existing_contribution_inr: number;
  annual_cashflows_inr: number[];
  npv_inr: number;
  roi_fraction: number | null;
  payback_years: number | null;
  failfast: FailFastDiagnosis;
  drivers: string[];
  source_ids: string[];
}

export interface EvaluationData {
  evaluation_id: string;
  project_id: string;
  scenario_id: string;
  method_mode:
    | "model_simulated"
    | "model_real_evaluated"
    | "scenario_assumptions";
  site_analyses: SiteAnalysis[];
  rankings: string[];
  created_at_utc: string;
  model_artifact_id: string | null;
}

export interface PortfolioRequest {
  evaluation_id: string;
  max_stores?: number;
  acknowledged_risk_site_ids?: string[];
}

export type PortfolioStatus =
  | "FULL_NETWORK_EXACT"
  | "FEASIBLE_PARTIAL"
  | "UNKNOWN";

export interface PortfolioResult {
  portfolio_run_id: string;
  evaluation_id: string;
  selected_site_ids: string[];
  budget_used_inr: number;
  budget_unused_inr: number;
  full_network_npv_inr: number;
  status: PortfolioStatus;
  evaluated_subsets: number;
  total_subsets: number;
}

export interface RescueRequest {
  evaluation_id: string;
  lever?: "rent" | "sales";
  lower_bound?: number | null;
  upper_bound?: number | null;
}

export type ScenarioResponse = ApiEnvelope<Scenario>;
export type ScenarioListResponse = ApiEnvelope<Scenario[]>;
export type EvaluationResponse = ApiEnvelope<EvaluationData>;
export type PortfolioResponse = ApiEnvelope<PortfolioResult>;

/** Existing infrastructure response inspected from the live endpoint. */
export interface InfrastructureEvent {
  infra_project_id: string;
  name: string;
  status: string;
  hypothetical_demo: boolean;
  source_status: Provenance;
  source_id: string;
  expected_open_date: string | null;
  assumed_demo_open_date: string | null;
}
