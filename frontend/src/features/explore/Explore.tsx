"use client";
import { useState } from "react";
import Link from "next/link";
import LocationMap from "./LocationMap";
import CashflowComparison from "./CashflowComparison";
import { useWorkspace } from "@/lib/workspace";
import { money, percent, years } from "@/lib/format";
import type { SiteAnalysis, DaypartProfile } from "@/lib/types";
import { Unavailable } from "@/components/Feedback";

export const PERIODS: [DaypartProfile["time_bin"], string][] = [
  ["weekday_morning", "Weekday · 06–11"],
  ["weekday_lunch", "Weekday · 11–15"],
  ["weekday_evening", "Weekday · 15–20"],
  ["weekday_night", "Weekday · 20–06"],
  ["weekend_day", "Weekend · 06–18"],
  ["weekend_evening", "Weekend · 18–06"],
];
function Diagnosis({ analysis }: { analysis?: SiteAnalysis }) {
  return analysis ? (
    <span
      className={
        "diagnosis diagnosis-" + analysis.failfast.status.toLowerCase()
      }
    >
      {analysis.failfast.status}
    </span>
  ) : (
    <span className="muted">Not evaluated</span>
  );
}
export default function Explore() {
  const w = useWorkspace();
  const [period, setPeriod] =
    useState<DaypartProfile["time_bin"]>("weekday_lunch");
  const project = w.project?.data;
  const evaluation = w.evaluation?.data;
  const analyses = new Map(
    evaluation?.site_analyses.map((s) => [s.site_id, s]),
  );
  const ranked = new Set(evaluation?.rankings ?? []);
  const sites = project
    ? [
        ...(evaluation?.rankings ?? [])
          .map((id) => project.sites.find((s) => s.site_id === id))
          .filter((s) => s !== undefined),
        ...project.sites.filter((s) => !ranked.has(s.site_id)),
      ]
    : [];
  const compared = w.selection
    .map((id) => project?.sites.find((s) => s.site_id === id))
    .filter((s) => s !== undefined);
  if (!project)
    return (
      <Unavailable>
        {w.loading
          ? "Loading candidate locations…"
          : "Locations could not be loaded. Retry the workspace connection."}
      </Unavailable>
    );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Explore &amp; Compare</h1>
          <p>Find where new stores add value to the whole network.</p>
        </div>
        <Link className="text-link" href="/app/scenarios">
          Test an assumption →
        </Link>
      </div>
      <div className="project-strip">
        <p>
          <strong>{project.city}</strong> · {project.category} ·{" "}
          {project.sites.length} locations · {project.stores.length} fictional
          branches
        </p>
        <span className="source-label">{project.source_status}</span>
      </div>
      <div className="explore-layout">
        <section aria-labelledby="candidates-heading">
          <div className="section-heading">
            <div>
              <h2 id="candidates-heading">Candidate locations</h2>
              <p>
                Choose two to compare. Values include existing-store impact.
              </p>
            </div>
            <span aria-live="polite">{w.selection.length} of 2 selected</span>
          </div>
          {!sites.length ? (
            <Unavailable>No candidate locations are available.</Unavailable>
          ) : (
            <div
              className="table-scroll"
              role="region"
              aria-label="Candidate locations"
              tabIndex={0}
            >
              <table className="candidate-table">
                <caption className="sr-only">
                  All amounts are INR.{" "}
                  {w.current
                    ? "Current saved results."
                    : "Previous or unavailable results."}{" "}
                  Rejected and review-required sites remain visible.
                </caption>
                <thead>
                  <tr>
                    <th scope="col">Select</th>
                    <th scope="col">Location</th>
                    <th scope="col" className="numeric">
                      Annual sales
                    </th>
                    <th scope="col" className="numeric">
                      Network NPV
                    </th>
                    <th scope="col">Diagnosis</th>
                  </tr>
                </thead>
                <tbody>
                  {sites.map((site) => {
                    const a = analyses.get(site.site_id);
                    return (
                      <tr
                        key={site.site_id}
                        data-selected={w.selection.includes(site.site_id)}
                      >
                        <td>
                          <label className="compare-control">
                            <input
                              type="checkbox"
                              aria-label={"Compare " + site.name}
                              checked={w.selection.includes(site.site_id)}
                              disabled={
                                !w.selection.includes(site.site_id) &&
                                w.selection.length === 2
                              }
                              onChange={() => w.toggleSite(site.site_id)}
                            />
                          </label>
                        </td>
                        <th scope="row">
                          {site.name}
                          <small>{site.store_size_sqm} m²</small>
                        </th>
                        <td className="numeric">
                          {money(a?.annual_revenue_inr)}
                        </td>
                        <td className="numeric">
                          <strong>{money(a?.npv_inr)}</strong>
                          {a && !w.current && <small>Previous result</small>}
                        </td>
                        <td>
                          <Diagnosis analysis={a} />
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}
          {!evaluation && (
            <Unavailable>
              Evaluate the saved scenario to see sales, financial value and
              risk. Location inputs alone are not recommendations.
            </Unavailable>
          )}
        </section>
        <LocationMap />
      </div>
      <section aria-labelledby="comparison-heading">
        <div className="section-heading">
          <div>
            <h2 id="comparison-heading">Two-site investment comparison</h2>
            <p>
              Sales potential, costs and the value left after branch
              displacement. Amounts in INR.
            </p>
          </div>
        </div>
        {compared.length !== 2 ? (
          <Unavailable>
            Select exactly two locations above to compare their investment
            cases.
          </Unavailable>
        ) : (
          <>
            <div className="two-columns">
              {compared.map((site) => {
                const a = analyses.get(site.site_id);
                return (
                  <article className="investment-card" key={site.site_id}>
                    <div className="section-heading">
                      <h3>{site.name}</h3>
                      <Diagnosis analysis={a} />
                    </div>
                    <span className="eyebrow">
                      Incremental network NPV · INR
                    </span>
                    <p className="investment-value">{money(a?.npv_inr)}</p>
                    <dl className="comparison-metrics">
                      {[
                        ["Annual sales", money(a?.annual_revenue_inr)],
                        [
                          "Operating profit / year",
                          money(a?.operating_profit_inr),
                        ],
                        ["Initial investment", money(site.capex_inr)],
                        [
                          "Monthly rent",
                          money(a?.effective_inputs?.monthly_rent_inr),
                        ],
                        [
                          "Branch contribution lost / year",
                          money(a?.lost_existing_contribution_inr),
                        ],
                        ["Horizon ROI", percent(a?.roi_fraction)],
                        ["Simple payback", years(a?.payback_years)],
                      ].map(([label, value]) => (
                        <div key={label}>
                          <dt>{label}</dt>
                          <dd>{value}</dd>
                        </div>
                      ))}
                    </dl>
                    <p className="helper">
                      Operating profit excludes branch displacement. NPV and ROI
                      include it. Unrecovered payback is unknown / not
                      applicable.
                    </p>
                    {a ? (
                      <>
                        <div className="sensitivity-strip">
                          {["low", "base", "high"].map((key) => (
                            <div key={key}>
                              <span>{key} NPV</span>
                              <strong>
                                {money(a.sensitivity?.[key]?.npv_inr)}
                              </strong>
                            </div>
                          ))}
                        </div>
                        <p className="helper">
                          Low: −20% spending, +10% rent. High: +20% spending,
                          unchanged rent. Commercial cases, not prediction
                          intervals.
                        </p>
                        <h4>What drives this result</h4>
                        <ul>
                          {a.drivers.slice(0, 3).map((d, i) => (
                            <li key={i}>{d}</li>
                          ))}
                        </ul>
                        <details>
                          <summary>Risk, branch impact and sources</summary>
                          {a.failfast.reasons.length ? (
                            <ul>
                              {a.failfast.reasons.map((r, i) => (
                                <li key={i}>{r}</li>
                              ))}
                            </ul>
                          ) : (
                            <p>
                              No financial rules failed in the evaluated cases.
                            </p>
                          )}
                          <ul>
                            {a.branch_impacts?.map((b) => (
                              <li key={b.store_id}>
                                {project.stores.find(
                                  (s) => s.store_id === b.store_id,
                                )?.name ?? b.store_id}
                                : {money(b.lost_contribution_inr)} contribution
                                lost / year.
                              </li>
                            ))}
                          </ul>
                          <p>
                            SYNTHETIC inputs · ASSUMED economics. Sources:{" "}
                            {a.source_ids.join(", ")}. No measured-sales
                            validation is available.
                          </p>
                        </details>
                      </>
                    ) : (
                      <Unavailable>
                        Evaluate this scenario to see the investment case.
                      </Unavailable>
                    )}
                  </article>
                );
              })}
            </div>
            <details className="cashflow-details">
              <summary>Annual network cash flows</summary>
              <CashflowComparison sites={compared} analyses={analyses} />
            </details>
          </>
        )}
      </section>
      <section aria-labelledby="dayparts-heading">
        <div className="section-heading">
          <div>
            <h2 id="dayparts-heading">DaypartDNA</h2>
            <p>
              Nearby destinations reveal when opportunity is concentrated. POI
              proxy · Asia/Kolkata · no measured footfall.
            </p>
          </div>
        </div>
        <div
          className="period-controls"
          role="group"
          aria-label="Opportunity time period"
        >
          {PERIODS.map(([id, label]) => (
            <button
              key={id}
              type="button"
              className="secondary"
              aria-pressed={period === id}
              onClick={() => setPeriod(id)}
            >
              {label}
            </button>
          ))}
        </div>
        {compared.length !== 2 ? (
          <Unavailable>
            Select two locations to compare all six opportunity periods.
          </Unavailable>
        ) : (
          <div className="two-columns">
            {compared.map((site) => {
              const p = analyses
                .get(site.site_id)
                ?.dayparts?.find((p) => p.time_bin === period);
              return (
                <article className="daypart-card" key={site.site_id}>
                  <h3>{site.name}</h3>
                  {p ? (
                    <>
                      <p className="daypart-value">
                        {p.opportunity_index == null
                          ? "Unknown"
                          : p.opportunity_index.toFixed(1) + " / 100"}
                      </p>
                      {p.opportunity_index != null && (
                        <meter
                          min={0}
                          max={100}
                          value={p.opportunity_index}
                          aria-label={site.name + " opportunity share"}
                        />
                      )}
                      <p>
                        {p.reason ??
                          (p.opportunity_index === 0
                            ? "Supported evidence indicates zero opportunity in this period."
                            : "Share of this location’s six-period weekly opportunity.")}
                      </p>
                      <p>
                        {p.support_count} supporting destinations ·{" "}
                        {p.source_status}
                      </p>
                      <ul className="category-list">
                        {p.categories.map((c) => (
                          <li key={c.category}>
                            {c.category} <strong>{c.count}</strong>
                          </li>
                        ))}
                      </ul>
                      <details>
                        <summary>Source reliability and dates</summary>
                        <p>{p.reliability}</p>
                        <p>
                          Source date:{" "}
                          {p.observed_at ??
                            "Unknown — synthetic fixture has no observation date"}
                          .
                        </p>
                        <p>
                          Opening hours: assumed available. Raw weighted
                          opportunity:{" "}
                          {p.raw_opportunity?.toFixed(2) ?? "Unknown"}. Category
                          weights include weekly duration.
                        </p>
                        <p>
                          Sources:{" "}
                          {p.source_ids.join(", ") || "No supporting sources"}.
                        </p>
                      </details>
                    </>
                  ) : (
                    <Unavailable>
                      No opportunity evidence is available for this saved
                      evaluation. Missing evidence is different from zero.
                    </Unavailable>
                  )}
                </article>
              );
            })}
          </div>
        )}
      </section>
      {evaluation && (
        <details className="exclusion-details">
          <summary>Ranking, exclusions and all risk explanations</summary>
          <p>
            Ranked by saved incremental NPV, then lower investment and location
            identity. A high-sales location can rank lower after rent and
            existing-branch losses.
          </p>
          {sites.map((site) => {
            const a = analyses.get(site.site_id);
            return (
              <div className="excluded-site" key={site.site_id}>
                <strong>
                  {site.name} · {money(a?.npv_inr)}
                </strong>{" "}
                <Diagnosis analysis={a} />
                <p>
                  {a?.failfast.reasons.join(" ") ||
                    "No rule failures in the evaluated cases."}
                </p>
              </div>
            );
          })}
        </details>
      )}
    </>
  );
}
