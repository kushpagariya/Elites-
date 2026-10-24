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
