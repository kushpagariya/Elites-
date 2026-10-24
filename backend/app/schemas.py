"""Canonical wire schema. Backend owner coordinates every shared change."""
from typing import Literal, Generic, TypeVar
from datetime import date
from pydantic import BaseModel, ConfigDict, Field, FiniteFloat, field_validator, model_validator


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


class Assumptions(StrictModel):
    demand_multiplier: FiniteFloat = Field(default=1, ge=0, le=3)
    rent_multiplier: FiniteFloat = Field(default=1, ge=0, le=3)
    site_overrides: dict[str, SiteOverride] = Field(default_factory=dict)
    infrastructure_state: Literal["current", "opens", "delayed"] = "current"
    infrastructure_effect_fraction: FiniteFloat = Field(default=0, ge=-1, le=2)
    opening_date: str | None = None
    delay_months: int = Field(default=24, ge=0, le=120)

    @field_validator("opening_date")
    @classmethod
    def iso_date(cls, value):
        if value is not None and date.fromisoformat(value).isoformat() != value:
            raise ValueError("Use an ISO calendar date: YYYY-MM-DD")
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
    max_viable_monthly_rent_inr: FiniteFloat | None = Field(default=None, ge=0)
    required_sales_multiplier: FiniteFloat | None = Field(default=None, ge=0, le=3)
    rescue_status: Literal["NOT_REQUESTED", "SOLVED", "NOT_RECOVERABLE_WITHIN_BOUNDS", "NON_MONOTONIC"] = "NOT_REQUESTED"


class SiteAnalysis(StrictModel):
    site_id: str
    annual_revenue_inr: FiniteFloat = Field(ge=0)
    lost_existing_contribution_inr: FiniteFloat = Field(ge=0)
    annual_cashflows_inr: list[FiniteFloat]
    npv_inr: FiniteFloat
    roi_fraction: FiniteFloat | None = None
    payback_years: FiniteFloat | None = Field(default=None, ge=0)
    failfast: FailFastDiagnosis
    drivers: list[str]
    source_ids: list[str]


class EvaluationData(StrictModel):
    evaluation_id: str
    project_id: str
    scenario_id: str
    method_mode: Literal["model_simulated", "model_real_evaluated", "scenario_assumptions"]
    site_analyses: list[SiteAnalysis]
    rankings: list[str]
    created_at_utc: str
    model_artifact_id: str | None = None


class PortfolioRequest(StrictModel):
    evaluation_id: str
    max_stores: int = Field(default=2, ge=0, le=10)
    acknowledged_risk_site_ids: list[str] = Field(default_factory=list)


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


class RescueRequest(StrictModel):
    evaluation_id: str
    lever: Literal["rent", "sales"] = "rent"
    lower_bound: FiniteFloat | None = Field(default=None, ge=0)
    upper_bound: FiniteFloat | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def ordered_bounds(self):
        if self.lower_bound is not None and self.upper_bound is not None and self.lower_bound > self.upper_bound:
            raise ValueError("lower_bound must not exceed upper_bound")
        return self


class RescueResult(StrictModel):
    rescue_id: str
    evaluation_id: str
    site_id: str
    lever: Literal["rent", "sales"]
    lower_bound: FiniteFloat = Field(ge=0)
    upper_bound: FiniteFloat = Field(ge=0)
    status: Literal["SOLVED", "NOT_RECOVERABLE_WITHIN_BOUNDS", "NON_MONOTONIC"]
    threshold: FiniteFloat | None = None
    verification_npv_inr: FiniteFloat | None = None
    reasons: list[str]
