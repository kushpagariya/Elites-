"use client";
import Link from "next/link";
import LocationMap from "./LocationMap";
import InvestmentCard from "./InvestmentCard";
import DaypartSelector from "./DaypartSelector";
import CashflowComparison from "./CashflowComparison";
import StatusBadge from "@/components/StatusBadge";
import { useWorkspace } from "@/lib/workspace";
import { money, percent, years } from "@/lib/format";
import { compactMoney, reasonLabel, PERIODS } from "@/lib/presentation";
import { Unavailable } from "@/components/Feedback";
export { PERIODS } from "@/lib/presentation";

export default function Explore() {
  const w = useWorkspace();
  const project = w.project?.data;
  const evaluation = !w.dirty && w.evaluation && w.evaluation.data.scenario_id === w.scenario?.scenario_id ? w.evaluation.data : undefined;
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
  const profileSites = compared.length
    ? compared
    : sites.filter((s) => s.site_id === w.focusedSiteId);
  if (!project)
    return (
      <Unavailable>
        {w.loading
          ? "Loading your locations…"
          : "We couldn’t load the locations. Retry the connection above."}
      </Unavailable>
    );
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Explore Locations</h1>
          <p>Which locations look promising?</p>
        </div>
        <Link className="text-link" href="/app/scenarios">
          Test business conditions →
        </Link>
      </div>
      <div className="explore-workbench">
        <div className="map-workbench">
          <DaypartSelector
            value={w.activePeriod ?? "weekday_lunch"}
            onChange={w.setActivePeriod}
          />
          <LocationMap />
        </div>
        <aside
          className="location-shortlist"
          aria-labelledby="locations-heading"
        >
          <div className="shortlist-heading">
            <div>
              <h2 id="locations-heading">
                Locations <span>{sites.length}</span>
              </h2>
              <p>{w.selection.length}/2 selected for comparison</p>
            </div>
            {w.selection.length > 0 && (
              <a href="#comparison-heading">Compare ↓</a>
            )}
          </div>
          {!evaluation && (
            <div className="shortlist-guide">
              <strong>Start with a location</strong>
              <p>
                Select a marker or card. Run analysis above to see sales, value
                and risk.
              </p>
            </div>
          )}
          {evaluation && !w.current && (
            <p className="helper stale-label">
              Previous results · refresh this scenario
            </p>
          )}
          <div className="location-card-list">
            {sites.map((site, index) => {
              const a = analyses.get(site.site_id);
              return (
                <article
                  className="location-card"
                  key={site.site_id}
                  data-selected={w.selection.includes(site.site_id)}
                  data-focused={w.focusedSiteId === site.site_id}
                >
                  <button
                    className="location-card-main"
                    type="button"
                    onClick={() => w.focusSite(site.site_id)}
                    aria-label={"View " + site.name}
                  >
                    <span className="location-rank">
                      {ranked.has(site.site_id) ? index + 1 : "·"}
                    </span>
                    <span>
                      <strong>{site.name}</strong>
                      <small>
                        {site.store_size_sqm} m² · investment{" "}
                        {compactMoney(site.capex_inr)}
                      </small>
                    </span>
                    <span className="card-value" title={money(a?.npv_inr)}>
                      {a ? compactMoney(a.npv_inr) : "—"}
                      <small>NPV</small>
                    </span>
                  </button>
                  <div className="location-card-footer">
                    <StatusBadge status={a?.failfast.status} />
                    <label className="compare-check">
                      <input
                        type="checkbox"
                        aria-label={"Compare " + site.name}
                        checked={w.selection.includes(site.site_id)}
                        disabled={
                          !w.selection.includes(site.site_id) &&
                          w.selection.length === 2
                        }
                        onChange={() => {
                          w.focusSite(site.site_id);
                          w.toggleSite(site.site_id);
                        }}
                      />
                      Compare
                    </label>
                  </div>
                </article>
              );
            })}
          </div>
          <p className="helper">
            {project.source_status} locations · ranked by saved network NPV when
            available.
          </p>
        </aside>
      </div>
      <section className="opportunity-panel" aria-labelledby="dayparts-heading">
        <div className="section-heading">
          <div>
            <h2 id="dayparts-heading">
              DaypartDNA <span className="quiet-tag">Opportunity by time of day</span>
            </h2>
            <p>When could these locations be busiest?</p>
          </div>
          <span className="helper">
            {
              PERIODS.find(
                ([id]) => id === (w.activePeriod ?? "weekday_lunch"),
              )?.[1]
            }{" "}
            · Asia/Kolkata
          </span>
        </div>
        {!profileSites.length ? (
          <Unavailable>
            Select a location on the map to see its destination mix and
            time-of-day opportunity.
          </Unavailable>
        ) : (
          <div className="two-columns">
            {profileSites.map((site) => {
              const a = analyses.get(site.site_id);
              const profile = a?.dayparts?.find(
                (p) => p.time_bin === (w.activePeriod ?? "weekday_lunch"),
              );
              return (
                <article className="opportunity-location" key={site.site_id}>
                  <div className="section-heading">
                    <h3>{site.name}</h3>
                    <strong className="opportunity-score">
                      {profile?.opportunity_index == null
                        ? a ? 'Evidence unavailable' : w.operation === 'evaluate' ? 'Calculating…' : w.error || w.analyticsStatus === 'unavailable' ? 'Analysis unavailable' : 'Run analysis to view'
                        : profile.opportunity_index.toFixed(1) + "%"}
                    </strong>
                  </div>
                  {a ? <div
                    className="daypart-bars"
                    role="group"
                    aria-label={site.name + " six-period opportunity"}
                  >
                    {PERIODS.map(([id, label]) => {
                      const p = a?.dayparts?.find((p) => p.time_bin === id);
                      return (
                        <button
                          className="daypart-bar"
                          key={id}
                          type="button"
                          aria-pressed={id === w.activePeriod}
                          onClick={() => w.setActivePeriod(id)}
                          title={label}
                        >
                          <span>{label.split(" · ")[0]}</span>
                          {p?.opportunity_index != null ? (
                            <meter
                              min={0}
                              max={100}
                              value={p.opportunity_index}
                              aria-label={label + " opportunity"}
                            />
                          ) : (
                            <span className="unknown-bar">—</span>
                          )}
                          <strong aria-hidden="true">{p?.opportunity_index == null ? "—" : p.opportunity_index.toFixed(1)}</strong>
                        </button>
                      );
                    })}
                  </div> : <p className="helper" role="status">{w.operation === 'evaluate' ? 'Calculating six time periods for this scenario…' : w.error || w.analyticsStatus === 'unavailable' ? 'The calculation service is unavailable. Retry analysis from the scenario bar.' : 'Run analysis above to view all six periods for this saved scenario.'}</p>}
                  {profile ? (
                    <>
                      <p className="profile-explanation">
                        {profile.reason ??
                          (profile.opportunity_index === 0
                            ? "Supported evidence indicates zero opportunity in this period."
                            : "Nearby destinations support this period’s share of weekly opportunity.")}
                      </p>
                      <ul className="category-list">
                        {profile.categories.map((c) => (
                          <li key={c.category}>
                            {c.category} <strong>{c.count}</strong>
                          </li>
                        ))}
                      </ul>
                      <details>
                        <summary>Sources &amp; limitations</summary>
                        <p>{profile.reliability}</p>
                        <p>
                          {profile.support_count} supporting destinations ·{" "}
                          {profile.source_status}. Observation date:{" "}
                          {profile.observed_at ?? "not supplied"}.
                        </p>
                        <p>
                          Sources:{" "}
                          {profile.source_ids.join(", ") ||
                            "No supporting sources"}
                          . Raw weighted opportunity:{" "}
                          {profile.raw_opportunity?.toFixed(2) ?? "Unknown"}.
                        </p>
                        <p>
                          Index is the location’s six-period share, not measured
                          footfall or a cross-city score. Missing evidence is
                          not zero.
                        </p>
                      </details>
                    </>
                  ) : a ? <p className="helper">The saved analysis has no supported opportunity evidence for this period. Missing evidence is not zero.</p> : null}
                </article>
              );
            })}
          </div>
        )}
        <p className="helper">
          Estimated from nearby points of interest, not measured footfall.
          Opening hours and category weights may be assumed.
        </p>
      </section>
      <section aria-labelledby="comparison-heading">
        <div className="section-heading">
          <div>
            <h2 id="comparison-heading">Compare your locations</h2>
            <p>
              Sales potential and value after costs and existing-store impact.
            </p>
          </div>
          <span className="selection-count">
            {w.selection.length} of 2 selected
          </span>
        </div>
        <div className="two-columns comparison-pickers">
          {[0,1].map(index => <label key={index}>Candidate {index + 1}<select aria-label={`Comparison candidate ${index + 1}`} value={w.selection[index] ?? ''} onChange={e => {
            const ids = [...w.selection]; ids[index] = e.target.value;
            w.chooseSites(ids); w.focusSite(e.target.value || null);
          }}><option value="">Choose a candidate location</option>{sites.map(site => <option key={site.site_id} value={site.site_id} disabled={w.selection[1-index] === site.site_id}>{site.name}</option>)}</select></label>)}
        </div>
        {compared.length === 2 ? (
          <div className="two-columns">
            {compared.map((site) => (
              <InvestmentCard
                key={site.site_id}
                site={site}
                analysis={analyses.get(site.site_id)}
              />
            ))}
          </div>
        ) : (
          <Unavailable>
            Select two locations using the map or cards. Their investment cases
            will appear side by side.
          </Unavailable>
        )}
      </section>
      {compared.length === 2 && (
        <div className="cashflow-panel"><CashflowComparison sites={compared} analyses={analyses} /></div>
      )}
      <details className="detailed-comparison">
        <summary>Detailed Comparison</summary>
        <div
          className="table-scroll"
          tabIndex={0}
          role="region"
          aria-label="Full financial comparison"
        >
          <table>
            <caption className="sr-only">
              All financial values use the displayed saved evaluation. Amounts
              in INR.
            </caption>
            <thead>
              <tr>
                {[
                  "Location",
                  "Year 1 sales",
                  "Operating profit",
                  "Investment",
                  "Monthly rent",
                  "Branch contribution lost",
                  "Incremental NPV (alone)",
                  "Horizon ROI",
                  "Payback",
                  "Status",
                ].map((t) => (
                  <th key={t} scope="col">
                    {t}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {(compared.length === 2 ? compared : sites).map((site) => {
                const a = analyses.get(site.site_id);
                return (
                  <tr key={site.site_id}>
                    <th scope="row">{site.name}</th>
                    {[
                      money(a?.annual_revenue_inr),
                      money(a?.operating_profit_inr),
                      money(site.capex_inr),
                      money(a?.effective_inputs?.monthly_rent_inr),
                      money(a?.lost_existing_contribution_inr),
                      money(a?.npv_inr),
                      percent(a?.roi_fraction),
                      years(a?.payback_years),
                    ].map((value, index) => (
                      <td className="numeric" key={index}>
                        {value}
                      </td>
                    ))}
                    <td>
                      <StatusBadge status={a?.failfast.status} />
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
        <p className="helper">
          NPV is the value of future network cash flows after investment,
          discounted to today. ROI compares the total return with initial
          investment. Operating profit is before existing-store displacement;
          network NPV includes it.
        </p>
      </details>
      {evaluation && (
        <details className="exclusion-details">
          <summary>All location risks &amp; exclusions</summary>
          {sites.map((site) => {
            const a = analyses.get(site.site_id);
            return (
              <div className="excluded-site" key={site.site_id}>
                <strong>{site.name}</strong>{" "}
                <StatusBadge status={a?.failfast.status} />
                <ul>
                  {a?.failfast.reasons.length ? (
                    a.failfast.reasons.map((r, i) => <li key={i}>{reasonLabel(r)}</li>)
                  ) : (
                    <li>No rules failed in the evaluated cases.</li>
                  )}
                </ul>
              </div>
            );
          })}
        </details>
      )}
    </>
  );
}
