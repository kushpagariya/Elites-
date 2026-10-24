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
  implementation_status: "scaffold" | "assumption_based_analytics";
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
  gross_margin_fraction?: number | null;
  annual_opex_inr?: number | null;
  competition_multiplier?: number | null;
}

export interface Assumptions {
  gross_margin_fraction?: number | null;
  operating_cost_multiplier?: number;
  competition_multiplier?: number;
  valuation_date?: string;
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
  operating_profit_inr?: number | null;
  sensitivity?: Record<string, FinanceSnapshot>;
  branch_impacts?: BranchImpact[];
  effective_inputs?: EffectiveInputs | null;
  infrastructure_exposure?: InfrastructureExposure[];
  calibration?: {
    target_revenue_inr: number;
    achieved_reference_revenue_inr: number;
    within_tolerance: boolean;
  } | null;
  dayparts?: DaypartProfile[];
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
  evidence?: Evidence | null;
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
  max_stores?: number;
  acknowledged_risk_site_ids?: string[];
  solver_status?:
    | "OPTIMAL"
    | "FEASIBLE"
    | "PARTIAL"
    | "UNAVAILABLE"
    | "UNKNOWN";
  solver_name?: string;
  solver_version?: string | null;
  exclusions?: { site_id: string; reason_codes: string[]; reasons: string[] }[];
  objective_precision_inr?: number;
  optimality_gap?: number | null;
  limitations?: string[];
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
  type?: string;
  geometry?: {
    type: "Point" | "LineString" | "Polygon";
    coordinates: number[] | number[][] | number[][][];
  };
  infra_project_id: string;
  name: string;
  status: string;
  hypothetical_demo: boolean;
  source_status: Provenance;
  source_id: string;
  expected_open_date: string | null;
  assumed_demo_open_date: string | null;
}

export interface FinanceSnapshot {
  annual_revenue_inr: number;
  operating_profit_inr: number;
  lost_existing_contribution_inr: number;
  npv_inr: number;
  roi_fraction: number | null;
  payback_years: number | null;
}
export interface BranchImpact {
  store_id: string;
  baseline_revenue_inr: number;
  after_revenue_inr: number;
  lost_contribution_inr: number;
}
export interface EffectiveInputs {
  monthly_rent_inr: number;
  annual_opex_inr: number;
  gross_margin_fraction: number;
  sales_multiplier: number;
  competition_multiplier: number;
}
export interface InfrastructureExposure {
  event_id: string;
  distance_m: number | null;
  exposure_fraction: number;
  opening_date: string | null;
  active_fractions: number[];
  assumed_effect_fraction: number;
  hypothetical: boolean;
}
export interface DaypartProfile {
  time_bin:
    | "weekday_morning"
    | "weekday_lunch"
    | "weekday_evening"
    | "weekday_night"
    | "weekend_day"
    | "weekend_evening";
  opportunity_index: number | null;
  raw_opportunity: number | null;
  support_count: number;
  categories: {
    category: string;
    count: number;
    weighted_opportunity: number;
  }[];
  source_ids: string[];
  source_status: Provenance;
  reliability: string;
  observed_at: string | null;
  reason: string | null;
}
export interface Evidence {
  feature_snapshot_id: string;
  source_snapshot_id: string;
  finance_version: string;
  rule_version: string;
  weight_version: string;
  estimator_version: string;
  valuation_date: string;
  limitations: string[];
  assumed_parameters: Record<string, number>;
}
export interface RescueResult {
  evaluation_id: string;
  site_id: string;
  lever: "rent" | "sales";
  status: "SOLVED" | "NOT_RECOVERABLE_WITHIN_BOUNDS" | "NON_MONOTONIC";
  lower_bound: number;
  upper_bound: number;
  threshold: number | null;
  verified: boolean;
  npv_at_threshold: number | null;
  reasons: string[];
  remaining_failed_rule_ids: string[];
}
export interface GeoContext {
  evaluation_id: string;
  catchment_radius_m: number;
  pois: {
    poi_id: string;
    category: string;
    latitude: number;
    longitude: number;
    source_id: string;
    source_status: Provenance;
    opening_hours: string | null;
  }[];
  cells: {
    cell_id: string;
    latitude: number;
    longitude: number;
    annual_wallet_inr: number;
    source_id: string;
    source_status: Provenance;
  }[];
  roads: unknown[];
  competitors: unknown[];
  limitations: string[];
  catchments?: {
    site_id: string;
    geometry: { type: "Polygon"; coordinates: number[][][] };
  }[];
}
