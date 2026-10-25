"use client";
import Link from "next/link";
import { useWorkspace } from "@/lib/workspace";
import { money } from "@/lib/format";
import { compactMoney, reasonLabel } from "@/lib/presentation";
import StatusBadge from "@/components/StatusBadge";
import LocationMap from "@/features/explore/LocationMap";
import { Unavailable } from "@/components/Feedback";
export default function Portfolio() {
  const w = useWorkspace();
  const p = w.current ? w.portfolio : null;
  const e = w.evaluation?.data;
  const solver =
    p?.solver_status ??
    (p?.status === "FULL_NETWORK_EXACT"
      ? "OPTIMAL"
      : p?.status === "FEASIBLE_PARTIAL"
        ? "PARTIAL"
        : "UNKNOWN");
  const available = !!p && !["UNAVAILABLE", "UNKNOWN"].includes(solver);
  const siteName = (id: string) =>
    w.project?.data.sites.find((s) => s.site_id === id)?.name ?? id;
  const risks = w.current
    ? (e?.site_analyses.filter((s) => s.failfast.status === "AT_RISK") ?? [])
    : [];
  const sharedReasons = risks[0]?.failfast.reasons.filter(r => risks.every(site => site.failfast.reasons.includes(r))) ?? [];
  const stateText = {
    OPTIMAL: "Best combination found",
    FEASIBLE: "Feasible plan · optimality unproven",
    PARTIAL: "Partial search · better options may exist",
    UNAVAILABLE: "Plan calculation unavailable",
    UNKNOWN: "Result not confirmed",
  }[solver];
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Investment Plan</h1>
          <p>Where should your expansion budget go?</p>
        </div>
        <Link className="text-link" href="/app/scenarios">
          Adjust the budget →
        </Link>
      </div>
      <div className="plan-budget">
        <div>
          <span>Expansion budget</span>
          <strong>{compactMoney(w.scenario?.budget_inr)}</strong>
        </div>
        <p>
          Choose a group of stores that works together, within your saved
          budget.
        </p>
      </div>
      <div className="plan-layout">
        <section className="plan-controls" aria-labelledby="portfolio-heading">
          <h2 id="portfolio-heading">Choose the best group of stores</h2>
          <form
            onSubmit={(event) => {
              event.preventDefault();
              void w.optimise();
            }}
          >
            <label>
              Maximum new stores
              <input
                type="number"
                required
                min={0}
                max={w.project?.data.sites.length ?? 10}
                step={1}
                value={Number.isNaN(w.maxStores) ? "" : w.maxStores}
                onChange={(event) =>
                  w.changePortfolioInputs(
                    event.target.value === ""
                      ? NaN
                      : Number(event.target.value),
                    w.acknowledged,
                  )
                }
              />
            </label>
            <p className="helper">
              Zero keeps the option of opening no new stores.
            </p>
            <fieldset>
              <legend>Review investment risks</legend>
              {sharedReasons.length > 0 && <details><summary>Shared model and data risks</summary><ul>{sharedReasons.map(r => <li key={r}>{reasonLabel(r)}</li>)}</ul></details>}
              {risks.length > 0 && <p className="helper">Include only locations whose risks you have reviewed. This does not approve an investment automatically.</p>}
              {risks.length ? (
                risks.map((s) => (
                  <label className="check-label risk-ack" key={s.site_id}>
                    <input
                      type="checkbox"
                      checked={w.acknowledged.includes(s.site_id)}
                      onChange={(event) =>
                        w.changePortfolioInputs(
                          w.maxStores,
                          event.target.checked
                            ? [...w.acknowledged, s.site_id]
                            : w.acknowledged.filter((id) => id !== s.site_id),
                        )
                      }
                    />
                    <span>
                      I have reviewed the risks for {siteName(s.site_id)}.
                      {s.failfast.reasons.some(r => !sharedReasons.includes(r)) && <small>{s.failfast.reasons.filter(r => !sharedReasons.includes(r)).map(reasonLabel).join(" ")}</small>}
                    </span>
                  </label>
                ))
              ) : (
                <p className="helper">
                  {w.current
                    ? "No locations need additional risk acknowledgement."
                    : "Run analysis on a saved scenario to review location risks."}
                </p>
              )}
            </fieldset>
            <button type="submit" disabled={!w.current || w.busy}>
              {w.operation === "portfolio"
                ? "Comparing combinations…"
                : "Find the Best Store Combination"}
            </button>
          </form>
        </section>
        <section className="plan-result" aria-labelledby="plan-heading">
          <div className="section-heading">
            <h2 id="plan-heading">Your expansion plan</h2>
            {p && <span className="quiet-tag">{stateText}</span>}
          </div>
          <dl className="plan-metrics">
            <div>
              <dt title="Net present value after existing-store impact and overlap between new locations.">
                Expected network-adjusted NPV
              </dt>
              <dd
                title={money(available ? p?.full_network_npv_inr : undefined)}
              >
                {compactMoney(available ? p?.full_network_npv_inr : undefined)}
              </dd>
            </div>
            <div>
              <dt>Total investment</dt>
              <dd>
                {compactMoney(available ? p?.budget_used_inr : undefined)}
              </dd>
            </div>
            <div>
              <dt>Remaining budget</dt>
              <dd>
                {compactMoney(available ? p?.budget_unused_inr : undefined)}
              </dd>
            </div>
          </dl>
          {available && p ? (
            <>
              <div className="budget-allocation">
                <div className="section-heading">
                  <strong>Budget allocation</strong>
                  <span>{money(p.budget_used_inr)} invested</span>
                </div>
                <meter
                  min={0}
                  max={Math.max(w.scenario?.budget_inr ?? 0, 1)}
                  value={p.budget_used_inr}
                  aria-label="Investment used from expansion budget"
                />
                <div className="range-labels">
                  <span>Investment</span>
                  <span>{money(p.budget_unused_inr)} available</span>
                </div>
              </div>
              <h3>
                {p.selected_site_ids.length
                  ? "Recommended locations"
                  : "Empty portfolio"}
              </h3>
              {p.selected_site_ids.length ? (
                <div className="selected-plan-sites">
                  {p.selected_site_ids.map((id) => {
                    const a = e?.site_analyses.find((s) => s.site_id === id);
                    return (
                      <article key={id}>
                        <div className="section-heading">
                          <strong>{siteName(id)}</strong>
                          <StatusBadge status={a?.failfast.status} />
                        </div>
                        <p>
                          Year-one sales if opened alone:{" "}
                          {money(a?.annual_revenue_inr)} · existing-store
                          contribution lost{" "}
                          {money(a?.lost_existing_contribution_inr)}.
                        </p>
                      </article>
                    );
                  })}
                </div>
              ) : (
                <p>
                  No stores were selected. Keeping the budget uncommitted is a
                  valid result when no eligible combination improves value.
                </p>
              )}
              {solver !== "OPTIMAL" && (
                <p className="message">
                  This is a feasible result from an incomplete search. A better
                  combination may exist.
                </p>
              )}
            </>
          ) : (
            <Unavailable>
              {p
                ? "Portfolio selection is currently unavailable. No investment recommendation has been made. Your saved location analysis is unchanged."
                : "Set a store limit, review any risks, then find the best combination. The plan will account for overlap and effects on existing stores."}
            </Unavailable>
          )}
          {p && (
            <>
              <details>
                <summary>Locations outside the plan</summary>
                {p.exclusions?.length ? (
                  p.exclusions.map((x) => (
                    <div className="excluded-site" key={x.site_id}>
                      <strong>{siteName(x.site_id)}</strong>
                      <p>{x.reasons.map(reasonLabel).join(" ")}</p>
                    </div>
                  ))
                ) : (
                  <p>No detailed exclusions were supplied for this result.</p>
                )}
              </details>
              <details>
                <summary>Technical Details</summary>
                <p>
                  {p.solver_name} · {p.solver_version ?? "Version unavailable"}
                </p>
                <p>
                  {p.status} / {solver}. {p.evaluated_subsets} of{" "}
                  {p.total_subsets} subsets examined. Gap:{" "}
                  {p.optimality_gap ?? "unknown"}. Objective precision: INR{" "}
                  {p.objective_precision_inr ?? "unknown"}.
                </p>
                {p.limitations?.map((text, i) => (
                  <p key={i}>{text}</p>
                ))}
                <p>
                  Run: {p.portfolio_run_id}
                  <br />
                  Evaluation: {p.evaluation_id}
                </p>
              </details>
            </>
          )}
        </section>
      </div>
      {w.project && (
        <LocationMap
          compact
          selectedSiteIds={available ? (p?.selected_site_ids ?? []) : []}
        />
      )}
      <section className="decision-report" aria-labelledby="report-heading">
        <div className="section-heading">
          <div>
            <h2 id="report-heading">Your decision report</h2>
            <p>
              Recommendations, value, existing-store impact and the assumptions
              behind the decision.
            </p>
          </div>
          <button
            className="secondary"
            disabled={
              !w.current ||
              !available ||
              !p ||
              p.evaluation_id !== e?.evaluation_id ||
              w.busy
            }
            onClick={() => void w.downloadReport()}
          >
            {w.operation === "report"
              ? "Downloading…"
              : "Download decision report"}
          </button>
        </div>
        <div className="report-contents">
          <span>Recommended stores &amp; reasons</span>
          <span>Revenue, investment &amp; network impact</span>
          <span>Risks &amp; infrastructure assumptions</span>
          <span>Sources &amp; limitations</span>
        </div>
        <p className="helper">
          Uses the saved analysis and matching investment plan. Export content
          and calculation identities are preserved.
        </p>
        {w.report ? (
          <details open>
            <summary>Downloaded report preview</summary>
            {w.report.type.includes("html") ? (
              <iframe
                title="Saved decision report preview"
                sandbox=""
                srcDoc={w.report.text}
              />
            ) : (
              <pre className="report-preview">{w.report.text}</pre>
            )}
          </details>
        ) : (
          <p className="helper">
            {w.current && available && p?.evaluation_id === e?.evaluation_id
              ? "Your report is ready to download. It includes this saved analysis and investment plan."
              : "A completed investment plan is needed before downloading its report."}
          </p>
        )}
      </section>
    </>
  );
}
