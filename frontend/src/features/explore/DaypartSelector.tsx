"use client";
import { PERIODS, type TimePeriod } from "@/lib/presentation";
export default function DaypartSelector({
  value,
  onChange,
}: {
  value: TimePeriod;
  onChange: (period: TimePeriod) => void;
}) {
  return (
    <div className="daypart-selector">
      <div
        className="segmented"
        role="group"
        aria-label="DaypartDNA time period"
      >
        {(
          [
            ["weekday_morning", "Morning"],
            ["weekday_lunch", "Lunch"],
            ["weekday_evening", "Evening"],
            ["weekend_evening", "Weekend"],
          ] as const
        ).map(([id, label]) => (
          <button
            type="button"
            key={id}
            aria-pressed={
              id === value || (label === "Weekend" && value === "weekend_day")
            }
            onClick={() => onChange(id)}
          >
            {label}
          </button>
        ))}
      </div>
      <details className="period-more">
        <summary>{value === "weekday_night" ? "Night" : "All periods"}</summary>
        <label>
          <span className="sr-only">All six analytical periods</span>
          <select
            value={value}
            onChange={(e) => {
              onChange(e.target.value as TimePeriod);
              e.currentTarget.closest("details")?.removeAttribute("open");
            }}
          >
            {PERIODS.map(([id, label]) => (
              <option value={id} key={id}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </details>
    </div>
  );
}
