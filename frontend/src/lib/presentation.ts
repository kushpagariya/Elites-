import type { DaypartProfile, Diagnosis } from "./types";
export type TimePeriod = DaypartProfile["time_bin"];
export const PERIODS: [TimePeriod, string][] = [
  ["weekday_morning", "Morning · weekdays 06–11"],
  ["weekday_lunch", "Lunch · weekdays 11–15"],
  ["weekday_evening", "Evening · weekdays 15–20"],
  ["weekday_night", "Night · weekdays 20–06"],
  ["weekend_day", "Weekend · 06–18"],
  ["weekend_evening", "Weekend evening · 18–06"],
];
export const statusLabel = (status?: Diagnosis) =>
  status
    ? {
        VIABLE: "Viable",
        AT_RISK: "At Risk",
        REJECTED: "Rejected",
        REVIEW_REQUIRED: "Needs Review",
      }[status]
    : "Not evaluated";
/** Input/presentation conversion only. Financial results always come from the API. */
export const changePercent = (multiplier: number) =>
  Math.round((multiplier - 1) * 10000) / 100;
export const changeMultiplier = (percent: number) => 1 + percent / 100;

export const compactMoney = (value: number | null | undefined) =>
  value == null || !Number.isFinite(value)
    ? "—"
    : new Intl.NumberFormat("en-IN", {
        style: "currency",
        currency: "INR",
        notation: "compact",
        maximumFractionDigits: 1,
      }).format(value);

const REASONS: Record<string, string> = {
  SHIFTED_MARKET_DEGRADATION_REVIEW: "The model needs review when market conditions change.",
  SYNTHETIC_MODEL_NO_REAL_OUTCOME_VALIDATION: "The model is trained on synthetic sales; real-store accuracy is unvalidated.",
  HISTORICAL_MODELLED_POPULATION_2020: "Population uses a historical 2020 model.",
  HCES_STATE_URBAN_SPENDING_2023_24: "Spending uses a state-level 2023–24 survey proxy.",
  NOMINAL_WALLET_2024_VS_SYNTHETIC_COSTS_2026: "Historical spending and assumed costs have no inflation adjustment.",
  OSM_PARTIAL_COVERAGE: "Mapped destinations may be incomplete.",
  "100_CELL_CENTROID_APPROXIMATION": "Spending is approximated using 100 geographic cell centres.",
  ASSUMED_EQUAL_COMPETITOR_ATTRACTION: "Competitor attraction is assumed to be equal.",
  REFERENCE_TARGET_UNATTAINABLE: "The requested sales target cannot be supported by this network.",
  CAPEX_EXCEEDS_SCENARIO_BUDGET: "Upfront investment exceeds the saved budget.",
};
export const reasonLabel = (reason: string) => REASONS[reason] ??
  (reason.includes("_") ? reason.replace(/^(HARD|REVIEW|EVIDENCE):/, "").replaceAll("_", " ").toLowerCase().replace(/^./, c => c.toUpperCase()) : reason);
export function riskSummary(reasons: string[]) {
  const priority = reasons.find(r => r.includes("NPV INR") || r.includes("CAPEX_EXCEEDS") || r.includes("REFERENCE_TARGET_UNATTAINABLE")) ??
    reasons.find(r => r.includes("SHIFTED_MARKET") || r.includes("SYNTHETIC_MODEL")) ?? reasons[0];
  return priority ? reasonLabel(priority) : "No rules failed in the evaluated cases.";
}
