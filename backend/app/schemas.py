"""Canonical wire schema. Backend owner coordinates every shared change."""
from typing import Literal, Generic, TypeVar
from datetime import date
from pydantic import field_validator, model_validator
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


T = TypeVar("T")


class Envelope(StrictModel, Generic[T]):
    data: T
    meta: dict


class ErrorDetail(StrictModel):
    field: str
    reason: str


class ErrorBody(StrictModel):
    code: str
    message: str
    details: list[ErrorDetail]


class ErrorEnvelope(StrictModel):
    error: ErrorBody


class Site(StrictModel):
    site_id: str
    name: str
    latitude: FiniteFloat = Field(ge=-90, le=90)
    longitude: FiniteFloat = Field(ge=-180, le=180)
    store_size_sqm: FiniteFloat = Field(gt=0)
    capex_inr: FiniteFloat = Field(ge=0)
    monthly_rent_inr: FiniteFloat = Field(ge=0)
    annual_opex_inr: FiniteFloat = Field(ge=0)
    gross_margin_fraction: FiniteFloat = Field(ge=0, le=1)


class Store(StrictModel):
    store_id: str
    name: str
    latitude: FiniteFloat = Field(ge=-90, le=90)
    longitude: FiniteFloat = Field(ge=-180, le=180)
    store_size_sqm: FiniteFloat = Field(gt=0)
    theta: FiniteFloat
    variable_contribution_margin: FiniteFloat = Field(ge=0, le=1)


class Project(StrictModel):
    project_id: str
    city: str
    category: str
    budget_inr: FiniteFloat = Field(ge=0)
    discount_rate_fraction: FiniteFloat = Field(ge=0, le=1)
    projection_years: int = Field(ge=1, le=10)
    sites: list[Site] = Field(max_length=10)
    stores: list[Store] = Field(max_length=4)
    source_status: Literal["SYNTHETIC", "REAL", "ASSUMED"]

    @model_validator(mode="after")
    def unique_ids(self):
        for rows, key in [(self.sites, "site_id"), (self.stores, "store_id")]:
            ids = [getattr(row, key) for row in rows]
            if len(set(ids)) != len(ids):
                raise ValueError(f"Duplicate {key}")
        return self


class SiteOverride(StrictModel):
    monthly_rent_inr: FiniteFloat | None = Field(default=None, ge=0)
    sales_multiplier: FiniteFloat | None = Field(default=None, ge=0, le=3)
    gross_margin_fraction: FiniteFloat | None = Field(default=None, ge=0, le=1)
    annual_opex_inr: FiniteFloat | None = Field(default=None, ge=0)
    competition_multiplier: FiniteFloat | None = Field(default=None, ge=0, le=3)


class Assumptions(StrictModel):
    gross_margin_fraction: FiniteFloat | None = Field(default=None, ge=0, le=1)
    operating_cost_multiplier: FiniteFloat = Field(default=1, ge=0, le=3)
    competition_multiplier: FiniteFloat = Field(default=1, ge=0, le=3)
    valuation_date: str = "2026-10-24"
    demand_multiplier: FiniteFloat = Field(default=1, ge=0, le=3)
    rent_multiplier: FiniteFloat = Field(default=1, ge=0, le=3)
    site_overrides: dict[str, SiteOverride] = Field(default_factory=dict)
    infrastructure_state: Literal["current", "opens", "delayed"] = "current"
    infrastructure_effect_fraction: FiniteFloat = Field(default=0, ge=-1, le=2)
    opening_date: str | None = None
    delay_months: int = Field(default=24, ge=0, le=120)


    @field_validator("opening_date", "valuation_date")
    @classmethod
    def iso_date(cls, value):
        if value is not None and date.fromisoformat(value).isoformat() != value:
            raise ValueError("Use an ISO date: YYYY-MM-DD")
        return value


class ScenarioCreate(StrictModel):
    base_scenario_id: str = "baseline"
    name: str = Field(min_length=1, max_length=100)
    budget_inr: FiniteFloat | None = Field(default=None, ge=0)
    assumptions: Assumptions


class Scenario(StrictModel):
    scenario_id: str
    project_id: str
    base_scenario_id: str | None = None
    name: str
    budget_inr: FiniteFloat = Field(ge=0)
    assumptions: Assumptions


class EvaluateRequest(StrictModel):
    scenario_id: str = "baseline"
    feature_snapshot_id: str = "features-demo-1"


class FailFastDiagnosis(StrictModel):
    status: Literal["VIABLE", "AT_RISK", "REJECTED", "REVIEW_REQUIRED"]
    failed_rule_ids: list[str] = Field(default_factory=list)
    reasons: list[str] = Field(default_factory=list)
    max_viable_monthly_rent_inr: FiniteFloat | None = None
    required_sales_multiplier: FiniteFloat | None = None
    rescue_status: Literal["NOT_REQUESTED", "SOLVED", "NOT_RECOVERABLE_WITHIN_BOUNDS", "NON_MONOTONIC"] = "NOT_REQUESTED"


class FinanceSnapshot(StrictModel):
    annual_revenue_inr: FiniteFloat
    operating_profit_inr: FiniteFloat
    lost_existing_contribution_inr: FiniteFloat
    npv_inr: FiniteFloat
    roi_fraction: FiniteFloat | None
    payback_years: FiniteFloat | None


class BranchImpact(StrictModel):
    store_id: str
    baseline_revenue_inr: FiniteFloat
    after_revenue_inr: FiniteFloat
    lost_contribution_inr: FiniteFloat


class DaypartCategory(StrictModel):
    category: str
    count: int = Field(ge=0)
    weighted_opportunity: FiniteFloat = Field(ge=0)


class DaypartProfile(StrictModel):
    time_bin: Literal["weekday_morning", "weekday_lunch", "weekday_evening", "weekday_night", "weekend_day", "weekend_evening"]
    opportunity_index: FiniteFloat | None = Field(ge=0, le=100)
    raw_opportunity: FiniteFloat | None
    support_count: int = Field(ge=0)
    categories: list[DaypartCategory]
    source_ids: list[str]
    source_status: Literal["REAL", "SYNTHETIC", "ASSUMED"]
    reliability: str
    observed_at: str | None
    reason: str | None


class InfrastructureExposure(StrictModel):
    event_id: str
    distance_m: FiniteFloat | None
    exposure_fraction: FiniteFloat = Field(ge=0, le=1)
    opening_date: str | None
    active_fractions: list[FiniteFloat]
    assumed_effect_fraction: FiniteFloat
    hypothetical: bool


class Calibration(StrictModel):
    target_revenue_inr: FiniteFloat
    achieved_reference_revenue_inr: FiniteFloat
    within_tolerance: bool


class EffectiveInputs(StrictModel):
    monthly_rent_inr: FiniteFloat
    annual_opex_inr: FiniteFloat
    gross_margin_fraction: FiniteFloat
    sales_multiplier: FiniteFloat
    competition_multiplier: FiniteFloat


class Evidence(StrictModel):
    feature_snapshot_id: str
    source_snapshot_id: str
    finance_version: str
    rule_version: str
    weight_version: str
    estimator_version: str
    valuation_date: str
    limitations: list[str]
    assumed_parameters: dict


class SiteAnalysis(StrictModel):
    site_id: str
    annual_revenue_inr: FiniteFloat = Field(ge=0)
    lost_existing_contribution_inr: FiniteFloat
    annual_cashflows_inr: list[FiniteFloat]
    npv_inr: FiniteFloat
    roi_fraction: FiniteFloat | None = None
    payback_years: FiniteFloat | None = None
    failfast: FailFastDiagnosis
    drivers: list[str]
    source_ids: list[str]
    operating_profit_inr: FiniteFloat | None = None
    sensitivity: dict[str, FinanceSnapshot] = Field(default_factory=dict)
    branch_impacts: list[BranchImpact] = Field(default_factory=list)
    effective_inputs: EffectiveInputs | None = None
    infrastructure_exposure: list[InfrastructureExposure] = Field(default_factory=list)
    calibration: Calibration | None = None
    dayparts: list[DaypartProfile] = Field(default_factory=list)


class EvaluationData(StrictModel):
    evaluation_id: str
    project_id: str
    scenario_id: str
    method_mode: Literal["model_simulated", "model_real_evaluated", "scenario_assumptions"]
    site_analyses: list[SiteAnalysis]
    rankings: list[str]
    created_at_utc: str
    model_artifact_id: str | None = None
    evidence: Evidence | None = None


class PortfolioRequest(StrictModel):
    evaluation_id: str
    max_stores: int = Field(default=2, ge=0, le=10)
    acknowledged_risk_site_ids: list[str] = Field(default_factory=list)


class Exclusion(StrictModel):
    site_id: str
    reason_codes: list[str]
    reasons: list[str]


class PortfolioResult(StrictModel):
    portfolio_run_id: str
    evaluation_id: str
    selected_site_ids: list[str]
    budget_used_inr: FiniteFloat = Field(ge=0)
    budget_unused_inr: FiniteFloat = Field(ge=0)
    full_network_npv_inr: FiniteFloat
    status: Literal["FULL_NETWORK_EXACT", "FEASIBLE_PARTIAL", "UNKNOWN"]
    evaluated_subsets: int = Field(ge=0)
    total_subsets: int = Field(ge=1)
    max_stores: int = Field(default=2, ge=0, le=10)
    acknowledged_risk_site_ids: list[str] = Field(default_factory=list)
    solver_status: Literal["OPTIMAL", "FEASIBLE", "PARTIAL", "UNAVAILABLE", "UNKNOWN"] = "UNKNOWN"
    solver_name: str = "Exact full-network enumeration"
    solver_version: str | None = None
    exclusions: list[Exclusion] = Field(default_factory=list)
    objective_precision_inr: FiniteFloat = 0.01
    optimality_gap: FiniteFloat | None = None
    limitations: list[str] = Field(default_factory=list)


class RescueRequest(StrictModel):
    evaluation_id: str
    lever: Literal["rent", "sales"] = "rent"
    lower_bound: FiniteFloat | None = Field(default=None, ge=0)
    upper_bound: FiniteFloat | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def ordered_bounds(self):
        if self.lower_bound is not None and self.upper_bound is not None and self.lower_bound >= self.upper_bound:
            raise ValueError("lower_bound must be less than upper_bound")
        return self


class RescueResult(StrictModel):
    rescue_id: str
    evaluation_id: str
    site_id: str
    lever: Literal["rent", "sales"]
    status: Literal["SOLVED", "NOT_RECOVERABLE_WITHIN_BOUNDS", "NON_MONOTONIC"]
    lower_bound: FiniteFloat
    upper_bound: FiniteFloat
    threshold: FiniteFloat | None
    verified: bool = False
    npv_at_threshold: FiniteFloat | None = None
    verification_npv_inr: FiniteFloat | None = None
    reasons: list[str]
    remaining_failed_rule_ids: list[str] = Field(default_factory=list)


class PoiRecord(StrictModel):
    poi_id: str
    category: str
    latitude: FiniteFloat
    longitude: FiniteFloat
    opening_hours: str | None
    source_id: str
    source_status: Literal["REAL", "SYNTHETIC", "ASSUMED"]


class CellRecord(StrictModel):
    cell_id: str
    latitude: FiniteFloat
    longitude: FiniteFloat
    annual_wallet_inr: FiniteFloat = Field(ge=0)
    source_id: str
    source_status: Literal["REAL", "SYNTHETIC", "ASSUMED"]


class CatchmentGeometry(StrictModel):
    type: Literal["Polygon"]
    coordinates: list[list[list[FiniteFloat]]]


class Catchment(StrictModel):
    site_id: str
    geometry: CatchmentGeometry


class GeographicContext(StrictModel):
    evaluation_id: str
    catchment_radius_m: FiniteFloat = Field(gt=0)
    pois: list[PoiRecord]
    cells: list[CellRecord]
    catchments: list[Catchment]
    roads: list[dict]
    competitors: list[dict]
    limitations: list[str]


class SiteDayparts(StrictModel):
    site_id: str
    profiles: list[DaypartProfile]


class DaypartsData(StrictModel):
    evaluation_id: str
    sites: list[SiteDayparts]


class RankingData(StrictModel):
    evaluation_id: str
    rankings: list[str]
    exclusions: list[SiteAnalysis]


class ModelCard(StrictModel):
    method_mode: Literal["scenario_assumptions", "model_simulated", "model_real_evaluated"]
    model_artifact_id: str | None
    estimator_version: str
    feature_schema: str
    trained_model_available: bool
    metrics: dict | None
    limitations: list[str]
