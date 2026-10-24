import type {
  Project,
  Scenario,
  EvaluationData,
  PortfolioResult,
  ApiEnvelope,
  RescueResult,
  GeoContext,
} from "./types";

export function record(x: unknown): x is Record<string, unknown> {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}
const finite = (x: unknown): x is number =>
  typeof x === "number" && Number.isFinite(x);
const nullable = (x: unknown) => x === null || finite(x);
const strings = (x: unknown): x is string[] =>
  Array.isArray(x) && x.every((v) => typeof v === "string");
const text = (x: unknown) => typeof x === "string" && x.length > 0;
const unique = (x: string[]) => new Set(x).size === x.length;
export function isProject(x: unknown): x is Project {
  if (
    !record(x) ||
    x.project_id !== "demo" ||
    !text(x.city) ||
    !text(x.category) ||
    !finite(x.budget_inr) ||
    !finite(x.discount_rate_fraction) ||
    !finite(x.projection_years) ||
    !["REAL", "SYNTHETIC", "ASSUMED"].includes(String(x.source_status)) ||
    !Array.isArray(x.sites) ||
    x.sites.length > 10 ||
    !Array.isArray(x.stores) ||
    x.stores.length > 4
  )
    return false;
  const sites = x.sites.every(
    (s) =>
      record(s) &&
      text(s.site_id) &&
      text(s.name) &&
      [
        "latitude",
        "longitude",
        "store_size_sqm",
        "capex_inr",
        "monthly_rent_inr",
        "annual_opex_inr",
        "gross_margin_fraction",
      ].every((k) => finite(s[k])),
  );
  const stores = x.stores.every(
    (s) =>
      record(s) &&
      text(s.store_id) &&
      text(s.name) &&
      [
        "latitude",
        "longitude",
        "store_size_sqm",
        "theta",
        "variable_contribution_margin",
      ].every((k) => finite(s[k])),
  );
  return (
    sites &&
    stores &&
    unique(x.sites.map((s) => s.site_id)) &&
    unique(x.stores.map((s) => s.store_id))
  );
}
export function isScenario(x: unknown): x is Scenario {
  if (
    !record(x) ||
    !text(x.scenario_id) ||
    x.project_id !== "demo" ||
    !text(x.name) ||
    !finite(x.budget_inr) ||
    !(x.base_scenario_id === null || text(x.base_scenario_id)) ||
    !record(x.assumptions)
  )
    return false;
  const a = x.assumptions;
  if (
    !["operating_cost_multiplier", "competition_multiplier"].every(
      (k) => a[k] === undefined || finite(a[k]),
    ) ||
    !(
      a.gross_margin_fraction === undefined || nullable(a.gross_margin_fraction)
    )
  )
    return false;
  return (
    [
      "demand_multiplier",
      "rent_multiplier",
      "infrastructure_effect_fraction",
      "delay_months",
    ].every((k) => finite(a[k])) &&
    ["current", "opens", "delayed"].includes(String(a.infrastructure_state)) &&
    (a.opening_date === null || typeof a.opening_date === "string") &&
    record(a.site_overrides) &&
    Object.values(a.site_overrides).every(
      (v) =>
        record(v) &&
        [
          "monthly_rent_inr",
          "sales_multiplier",
          "gross_margin_fraction",
          "annual_opex_inr",
          "competition_multiplier",
        ].every((k) => v[k] === undefined || nullable(v[k])),
    )
  );
}
export function isEvaluation(x: unknown): x is EvaluationData {
  if (
    !record(x) ||
    !text(x.evaluation_id) ||
    x.project_id !== "demo" ||
    !text(x.scenario_id) ||
    !text(x.created_at_utc) ||
    Number.isNaN(Date.parse(String(x.created_at_utc))) ||
    !(x.model_artifact_id === null || text(x.model_artifact_id)) ||
    ![
      "model_simulated",
      "model_real_evaluated",
      "scenario_assumptions",
    ].includes(String(x.method_mode)) ||
    !strings(x.rankings) ||
    !unique(x.rankings) ||
    !Array.isArray(x.site_analyses)
  )
    return false;
  if (
    x.evidence != null &&
    (!record(x.evidence) ||
      ![
        "feature_snapshot_id",
        "source_snapshot_id",
        "finance_version",
        "rule_version",
        "weight_version",
        "estimator_version",
        "valuation_date",
      ].every((k) => text((x.evidence as Record<string, unknown>)[k])) ||
      !strings(x.evidence.limitations) ||
      !record(x.evidence.assumed_parameters))
  )
    return false;
  return x.site_analyses.every(
    (s) =>
      record(s) &&
      text(s.site_id) &&
      validAnalysisExtras(s) &&
      ["annual_revenue_inr", "lost_existing_contribution_inr", "npv_inr"].every(
        (k) => finite(s[k]),
      ) &&
      nullable(s.roi_fraction) &&
      nullable(s.payback_years) &&
      Array.isArray(s.annual_cashflows_inr) &&
      s.annual_cashflows_inr.every(finite) &&
      strings(s.drivers) &&
      strings(s.source_ids) &&
      record(s.failfast) &&
      ["VIABLE", "AT_RISK", "REJECTED", "REVIEW_REQUIRED"].includes(
        String(s.failfast.status),
      ) &&
      strings(s.failfast.failed_rule_ids) &&
      strings(s.failfast.reasons) &&
      nullable(s.failfast.max_viable_monthly_rent_inr) &&
      nullable(s.failfast.required_sales_multiplier) &&
      [
        "NOT_REQUESTED",
        "SOLVED",
        "NOT_RECOVERABLE_WITHIN_BOUNDS",
        "NON_MONOTONIC",
      ].includes(String(s.failfast.rescue_status)),
  );
}
export function isPortfolio(x: unknown): x is PortfolioResult {
  return (
    record(x) &&
    (x.solver_status === undefined ||
      ["OPTIMAL", "FEASIBLE", "PARTIAL", "UNAVAILABLE", "UNKNOWN"].includes(
        String(x.solver_status),
      )) &&
    (x.exclusions === undefined ||
      (Array.isArray(x.exclusions) &&
        x.exclusions.every(
          (e) =>
            record(e) &&
            text(e.site_id) &&
            strings(e.reason_codes) &&
            strings(e.reasons),
        ))) &&
    (x.solver_status !== "OPTIMAL" || x.status === "FULL_NETWORK_EXACT") &&
    (x.status !== "FULL_NETWORK_EXACT" ||
      x.solver_status === undefined ||
      x.solver_status === "OPTIMAL") &&
    text(x.portfolio_run_id) &&
    text(x.evaluation_id) &&
    strings(x.selected_site_ids) &&
    unique(x.selected_site_ids) &&
    [
      "budget_used_inr",
      "budget_unused_inr",
      "full_network_npv_inr",
      "evaluated_subsets",
      "total_subsets",
    ].every((k) => finite(x[k])) &&
    ["FULL_NETWORK_EXACT", "FEASIBLE_PARTIAL", "UNKNOWN"].includes(
      String(x.status),
    ) &&
    Number(x.budget_used_inr) >= 0 &&
    Number(x.budget_unused_inr) >= 0 &&
    Number.isInteger(x.evaluated_subsets) &&
    Number.isInteger(x.total_subsets) &&
    Number(x.total_subsets) >= 1 &&
    Number(x.evaluated_subsets) >= 0 &&
    Number(x.evaluated_subsets) <= Number(x.total_subsets) &&
    (x.status !== "FULL_NETWORK_EXACT" ||
      x.evaluated_subsets === x.total_subsets)
  );
}
export function isEnvelope<T>(
  x: unknown,
  guard: (v: unknown) => v is T,
): x is ApiEnvelope<T> {
  return (
    record(x) &&
    record(x.meta) &&
    x.meta.contract_version === "1" &&
    typeof x.meta.fixture_id === "string" &&
    guard(x.data)
  );
}

function validAnalysisExtras(s: Record<string, unknown>): boolean {
  const snapshot = (v: unknown) =>
    record(v) &&
    [
      "annual_revenue_inr",
      "operating_profit_inr",
      "lost_existing_contribution_inr",
      "npv_inr",
    ].every((k) => finite(v[k])) &&
    nullable(v.roi_fraction) &&
    nullable(v.payback_years);
  if (s.operating_profit_inr !== undefined && !nullable(s.operating_profit_inr))
    return false;
  if (
    s.sensitivity !== undefined &&
    (!record(s.sensitivity) || !Object.values(s.sensitivity).every(snapshot))
  )
    return false;
  if (
    s.effective_inputs != null &&
    (!record(s.effective_inputs) ||
      ![
        "monthly_rent_inr",
        "annual_opex_inr",
        "gross_margin_fraction",
        "sales_multiplier",
        "competition_multiplier",
      ].every((k) =>
        finite((s.effective_inputs as Record<string, unknown>)[k]),
      ))
  )
    return false;
  if (
    s.dayparts !== undefined &&
    (!Array.isArray(s.dayparts) ||
      !s.dayparts.every(
        (p) =>
          record(p) &&
          [
            "weekday_morning",
            "weekday_lunch",
            "weekday_evening",
            "weekday_night",
            "weekend_day",
            "weekend_evening",
          ].includes(String(p.time_bin)) &&
          nullable(p.opportunity_index) &&
          nullable(p.raw_opportunity) &&
          finite(p.support_count) &&
          strings(p.source_ids) &&
          Array.isArray(p.categories) &&
          p.categories.every(
            (c) =>
              record(c) &&
              text(c.category) &&
              finite(c.count) &&
              finite(c.weighted_opportunity),
          ),
      ))
  )
    return false;
  if (
    s.infrastructure_exposure !== undefined &&
    (!Array.isArray(s.infrastructure_exposure) ||
      !s.infrastructure_exposure.every(
        (e) =>
          record(e) &&
          text(e.event_id) &&
          nullable(e.distance_m) &&
          finite(e.exposure_fraction) &&
          finite(e.assumed_effect_fraction) &&
          Array.isArray(e.active_fractions) &&
          e.active_fractions.every(finite) &&
          typeof e.hypothetical === "boolean",
      ))
  )
    return false;
  if (
    s.branch_impacts !== undefined &&
    (!Array.isArray(s.branch_impacts) ||
      !s.branch_impacts.every(
        (b) =>
          record(b) &&
          text(b.store_id) &&
          [
            "baseline_revenue_inr",
            "after_revenue_inr",
            "lost_contribution_inr",
          ].every((k) => finite(b[k])),
      ))
  )
    return false;
  return true;
}
export function isRescue(x: unknown): x is RescueResult {
  return (
    record(x) &&
    text(x.evaluation_id) &&
    text(x.site_id) &&
    ["rent", "sales"].includes(String(x.lever)) &&
    ["SOLVED", "NOT_RECOVERABLE_WITHIN_BOUNDS", "NON_MONOTONIC"].includes(
      String(x.status),
    ) &&
    finite(x.lower_bound) &&
    finite(x.upper_bound) &&
    x.lower_bound < x.upper_bound &&
    nullable(x.threshold) &&
    nullable(x.npv_at_threshold) &&
    typeof x.verified === "boolean" &&
    strings(x.reasons) &&
    strings(x.remaining_failed_rule_ids) &&
    (x.status !== "SOLVED" ||
      (finite(x.threshold) &&
        x.threshold >= x.lower_bound &&
        x.threshold <= x.upper_bound &&
        x.verified &&
        finite(x.npv_at_threshold) &&
        x.npv_at_threshold >= -0.01))
  );
}
export function isGeoContext(x: unknown): x is GeoContext {
  return (
    record(x) &&
    (x.catchments === undefined ||
      (Array.isArray(x.catchments) &&
        x.catchments.every(
          (c) =>
            record(c) &&
            text(c.site_id) &&
            record(c.geometry) &&
            c.geometry.type === "Polygon" &&
            Array.isArray(c.geometry.coordinates) &&
            c.geometry.coordinates.every(
              (r) =>
                Array.isArray(r) &&
                r.every(
                  (p) => Array.isArray(p) && p.length === 2 && p.every(finite),
                ),
            ),
        ))) &&
    text(x.evaluation_id) &&
    finite(x.catchment_radius_m) &&
    Array.isArray(x.pois) &&
    x.pois.every(
      (p) =>
        record(p) &&
        text(p.poi_id) &&
        text(p.category) &&
        finite(p.latitude) &&
        finite(p.longitude),
    ) &&
    Array.isArray(x.cells) &&
    x.cells.every(
      (c) =>
        record(c) &&
        text(c.cell_id) &&
        finite(c.latitude) &&
        finite(c.longitude) &&
        finite(c.annual_wallet_inr),
    ) &&
    Array.isArray(x.roads) &&
    Array.isArray(x.competitors) &&
    strings(x.limitations)
  );
}
