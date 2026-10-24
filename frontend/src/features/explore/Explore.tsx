"use client";
import Link from "next/link";
import LocationMap from "./LocationMap";
import CashflowComparison from "./CashflowComparison";
import { useWorkspace } from "@/lib/workspace";
import { money, percent, years } from "@/lib/format";
import type { SiteAnalysis } from "@/lib/types";
import { Unavailable } from "@/components/Feedback";

function Diagnosis({ analysis }: { analysis: SiteAnalysis | undefined }) {
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
  const project = w.project?.data;
  const evaluation = w.evaluation?.data;
  const analyses = new Map(
    evaluation?.site_analyses.map((s) => [s.site_id, s]),
  );
  const rankedIds = new Set(evaluation?.rankings ?? []);
  const sites = project
    ? [
        ...(evaluation?.rankings ?? [])
          .map((id) => project.sites.find((site) => site.site_id === id))
          .filter((site) => site !== undefined),
        ...project.sites.filter((site) => !rankedIds.has(site.site_id)),
      ]
    : [];
  const compared = w.selection
    .map((id) => project?.sites.find((s) => s.site_id === id))
    .filter((s) => s !== undefined);
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Explore &amp; Compare</h1>
          <p>Find where new stores add value to the existing network.</p>
        </div>
        <Link className="text-link" href="/app/scenarios">
          Test an assumption →
        </Link>
      </div>
      {project ? (
        <>
          <div className="project-strip">
            <p>
              <strong>{project.city}</strong> · {project.category} ·{" "}
              {project.sites.length} candidate sites · {project.stores.length}{" "}
              fictional branches
            </p>
            <span className="source-label">{project.source_status}</span>
          </div>
          <section aria-labelledby="candidates-heading">
            <div className="section-heading">
              <div>
                <h2 id="candidates-heading">Candidate locations</h2>
                <p>
                  Choose exactly two sites. Ranking comes from a saved
                  evaluation, ordered by incremental network NPV.
                </p>
              </div>
              <span aria-live="polite">{w.selection.length} of 2 selected</span>
            </div>
            {project.sites.length === 0 ? (
              <Unavailable>
                No candidate sites are available in this project.
              </Unavailable>
            ) : (
              <div
                className="table-scroll"
                role="region"
                aria-label="Candidate locations"
                tabIndex={0}
              >
                <table>
                  <caption className="sr-only">
                    Synthetic project inputs; financial columns use{" "}
                    {w.current ? "the current" : "a previous or unavailable"}{" "}
                    saved evaluation.
                  </caption>
                  <thead>
                    <tr>
                      <th scope="col">Compare</th>
                      <th scope="col">Candidate site</th>
                      <th scope="col" className="numeric">
                        Annual modelled sales (INR)
                      </th>
                      <th scope="col" className="numeric">
                        CAPEX (INR)
                      </th>
                      <th scope="col" className="numeric">
                        Base rent (INR/month)
                      </th>
                      <th scope="col" className="numeric">
                        Lost branch contribution (INR/year)
                      </th>
                      <th scope="col" className="numeric">
                        Incremental NPV (INR)
                      </th>
                      <th scope="col" className="numeric">
                        Horizon ROI
                      </th>
                      <th scope="col" className="numeric">
                        Simple payback
                      </th>
                      <th scope="col">Diagnosis</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sites.map((site) => {
                      const analysis = analyses.get(site.site_id);
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
                            <small>
                              {site.site_id} · {site.store_size_sqm} m²
                            </small>
                          </th>
                          <td className="numeric">
                            {money(analysis?.annual_revenue_inr)}
                          </td>
                          <td className="numeric">{money(site.capex_inr)}</td>
                          <td className="numeric">
                            {money(site.monthly_rent_inr)}
                          </td>
                          <td className="numeric">
                            {money(analysis?.lost_existing_contribution_inr)}
                          </td>
                          <td className="numeric">
                            {money(analysis?.npv_inr)}
                            {analysis && !w.current && (
                              <small>Stale evaluation</small>
                            )}
                          </td>
                          <td className="numeric">
                            {percent(analysis?.roi_fraction)}
                          </td>
                          <td className="numeric">
                            {years(analysis?.payback_years)}
                          </td>
                          <td>
                            <Diagnosis analysis={analysis} />
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
                Revenue, NPV and diagnosis are unavailable until the analytical
                pipeline returns a saved evaluation. Project inputs above are
                not investment recommendations.
              </Unavailable>
            )}
          </section>
          <LocationMap />
          <div className="analysis-grid">
            <section aria-labelledby="comparison-heading">
              <div className="section-heading">
                <div>
                  <h2 id="comparison-heading">Two-site comparison</h2>
                  <p>
                    Compare sales with the value left after costs and branch
                    displacement.
                  </p>
                </div>
              </div>
              {compared.length !== 2 ? (
                <Unavailable>
                  Select two candidate sites to compare their investment cases.
                </Unavailable>
              ) : (
                <>
                  <div
                    className="table-scroll"
                    role="region"
                    aria-label="Two-site financial comparison"
                    tabIndex={0}
                  >
                    <table className="comparison-table">
                      <thead>
                        <tr>
                          <th scope="col">Measure</th>
                          {compared.map((s) => (
                            <th key={s.site_id} scope="col" className="numeric">
                              {s.name}
                            </th>
                          ))}
                        </tr>
                      </thead>
                      <tbody>
                        {[
                          [
                            "Annual modelled sales (INR)",
                            (id: string) =>
                              money(analyses.get(id)?.annual_revenue_inr),
                          ],
                          [
                            "CAPEX input (INR)",
                            (id: string) =>
                              money(
                                project.sites.find((s) => s.site_id === id)
                                  ?.capex_inr,
                              ),
                          ],
                          [
                            "Base rent input (INR/month)",
                            (id: string) =>
                              money(
                                project.sites.find((s) => s.site_id === id)
                                  ?.monthly_rent_inr,
                              ),
                          ],
                          [
                            "Lost branch contribution (INR/year)",
                            (id: string) =>
                              money(
                                analyses.get(id)
                                  ?.lost_existing_contribution_inr,
                              ),
                          ],
                          [
                            "Incremental network NPV (INR)",
                            (id: string) => money(analyses.get(id)?.npv_inr),
                          ],
                          [
                            "Horizon ROI",
                            (id: string) =>
                              percent(analyses.get(id)?.roi_fraction),
                          ],
                          [
                            "Simple payback",
                            (id: string) =>
                              years(analyses.get(id)?.payback_years),
                          ],
                          ["Low sensitivity NPV (INR)", () => "Not supplied"],
                          [
                            "Base sensitivity NPV (INR)",
                            (id: string) => money(analyses.get(id)?.npv_inr),
                          ],
                          ["High sensitivity NPV (INR)", () => "Not supplied"],
                        ].map(([label, format]) => (
                          <tr key={label as string}>
                            <th scope="row">{label as string}</th>
                            {compared.map((s) => (
                              <td key={s.site_id} className="numeric">
                                {(format as (id: string) => string)(s.site_id)}
                              </td>
                            ))}
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                  <CashflowComparison sites={compared} analyses={analyses} />
                  <p className="helper">
                    Rent and CAPEX are ASSUMED project inputs. Scenario
                    overrides and multipliers are shown in Scenario &amp;
                    Rescue. Sensitivity is unavailable in the current response
                    contract; no forecast interval is implied.
                  </p>
                  <div className="two-columns">
                    {compared.map((site) => {
                      const a = analyses.get(site.site_id);
                      return (
                        <div className="comparison-evidence" key={site.site_id}>
                          <h3>{site.name}</h3>
                          <Diagnosis analysis={a} />
                          {a ? (
                            <>
                              <h4>Computed drivers</h4>
                              {a.drivers.length ? (
                                <ul>
                                  {a.drivers.slice(0, 3).map((d, i) => (
                                    <li key={i}>{d}</li>
                                  ))}
                                </ul>
                              ) : (
                                <p>No drivers were supplied.</p>
                              )}
                              {a.drivers.length < 3 && (
                                <p className="helper">
                                  Fewer than three drivers were supplied by the
                                  backend.
                                </p>
                              )}
                              <h4>Rule evidence</h4>
                              {a.failfast.failed_rule_ids.length > 0 && (
                                <p>{a.failfast.failed_rule_ids.join(", ")}</p>
                              )}
                              {a.failfast.reasons.length ? (
                                <ul>
                                  {a.failfast.reasons.map((r, i) => (
                                    <li key={i}>{r}</li>
                                  ))}
                                </ul>
                              ) : (
                                <p>No failed-rule reasons were supplied.</p>
                              )}
                              <h4>Sources</h4>
                              <p>
                                {a.source_ids.join(", ") ||
                                  "No source IDs supplied."}
                              </p>
                              <p className="helper">
                                Source freshness and detailed missingness were
                                not supplied by this response.
                              </p>
                            </>
                          ) : (
                            <Unavailable>
                              No analytical evidence available.
                            </Unavailable>
                          )}
                        </div>
                      );
                    })}
                  </div>
                </>
              )}
            </section>
            <section aria-labelledby="ranking-heading">
              <h2 id="ranking-heading">Ranking &amp; exclusions</h2>
              {evaluation ? (
                <>
                  <p>Backend ordering · {w.current ? "current" : "stale"}</p>
                  {evaluation.rankings.length ? (
                    <ol className="ranking-list">
                      {evaluation.rankings.map((id) => (
                        <li key={id}>
                          <span>
                            {project.sites.find((s) => s.site_id === id)
                              ?.name ?? id}
                          </span>
                          <strong>{money(analyses.get(id)?.npv_inr)}</strong>
                        </li>
                      ))}
                    </ol>
                  ) : (
                    <Unavailable>
                      No ranked candidates were returned.
                    </Unavailable>
                  )}
                  {evaluation.site_analyses
                    .filter(
                      (s) =>
                        s.failfast.status === "REJECTED" ||
                        s.failfast.status === "REVIEW_REQUIRED",
                    )
                    .map((a) => (
                      <div className="excluded-site" key={a.site_id}>
                        <strong>
                          {project.sites.find((s) => s.site_id === a.site_id)
                            ?.name ?? a.site_id}
                        </strong>
                        <Diagnosis analysis={a} />
                        <p>
                          {a.failfast.reasons.join(" ") ||
                            "No reason supplied."}
                        </p>
                      </div>
                    ))}
                </>
              ) : (
                <Unavailable>
                  No ranking has been computed. Rejected and review-required
                  sites will remain visible alongside the shortlist.
                </Unavailable>
              )}
            </section>
          </div>
          <section aria-labelledby="dayparts-heading">
            <div className="section-heading">
              <div>
                <h2 id="dayparts-heading">DaypartDNA</h2>
                <p>POI-derived opportunity proxy — not measured footfall.</p>
              </div>
              <button
                className="secondary"
                disabled
                title="TODO: needs backend — frozen bin identifiers and profile schema"
                onClick={() => void w.loadDayparts()}
              >
                {w.operation === "dayparts"
                  ? "Loading profiles…"
                  : "Load both profiles"}
              </button>
            </div>
            <div className="two-columns">
              {["Weekday lunch", "Weekend evening"].map((bin) => (
                <div className="profile-state" key={bin}>
                  <h3>{bin}</h3>
                  <p>Opportunity index: unavailable</p>
                  <p className="helper">
                    Within-site share: unavailable. Supporting POI
                    categories/counts, coverage, source dates and opening-hours
                    assumptions are not supplied. Missing evidence is not zero
                    opportunity.
                  </p>
                </div>
              ))}
            </div>
            <details>
              <summary>Six display periods · Asia/Kolkata</summary>
              <ul>
                {[
                  "Weekday 06:00–11:00",
                  "Weekday 11:00–15:00",
                  "Weekday 15:00–20:00",
                  "Weekday 20:00–06:00",
                  "Weekend 06:00–18:00",
                  "Weekend 18:00–06:00",
                ].map((label) => (
                  <li key={label}>{label}</li>
                ))}
              </ul>
              <p className="helper">
                TODO: needs backend — freeze bin identifiers and the shared
                cross-site index, within-site share and support schema. Display
                labels are never used as wire identifiers.
              </p>
            </details>
          </section>
          <details className="branch-details">
            <summary>
              {project.stores.length} existing fictional branches and location
              inputs
            </summary>
            <div
              className="table-scroll"
              tabIndex={0}
              role="region"
              aria-label="Existing branches"
            >
              <table>
                <thead>
                  <tr>
                    <th scope="col">Branch</th>
                    <th scope="col" className="numeric">
                      Latitude (WGS84)
                    </th>
                    <th scope="col" className="numeric">
                      Longitude (WGS84)
                    </th>
                    <th scope="col" className="numeric">
                      Size (m²)
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {project.stores.map((s) => (
                    <tr key={s.store_id}>
                      <th scope="row">
                        {s.name}
                        <small>{s.store_id}</small>
                      </th>
                      <td className="numeric">{s.latitude}</td>
                      <td className="numeric">{s.longitude}</td>
                      <td className="numeric">{s.store_size_sqm}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            <p className="helper">
              SYNTHETIC geography. Candidate and branch inputs come from the
              API. The local map uses the same API coordinates; this table
              remains the accessible decision surface.
            </p>
          </details>
        </>
      ) : (
        !w.loading && (
          <Unavailable>
            The project is unavailable. Start the local API and retry the
            workspace connection.
          </Unavailable>
        )
      )}
    </>
  );
}
