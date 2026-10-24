"use client";
import { useWorkspace } from "@/lib/workspace";
import { money } from "@/lib/format";
import { Unavailable } from "@/components/Feedback";
export default function Portfolio() {
  const w = useWorkspace();
  const p = w.current ? w.portfolio : null;
  const e = w.evaluation?.data;
  const available =
    p && p.solver_status !== "UNAVAILABLE" && p.solver_status !== "UNKNOWN";
  const siteName = (id: string) =>
    w.project?.data.sites.find((s) => s.site_id === id)?.name ?? id;
  const risks = w.current
    ? (e?.site_analyses.filter((s) => s.failfast.status === "AT_RISK") ?? [])
    : [];
  return (
    <>
      <div className="page-heading">
        <div>
          <h1>Portfolio &amp; Report</h1>
          <p>
            Choose the set that creates value together, within the saved
            scenario budget.
          </p>
        </div>
      </div>
      <div className="portfolio-grid">
        <section aria-labelledby="portfolio-heading">
          <h2 id="portfolio-heading">Full-network selection</h2>
          <p>
            Find the strongest combination within your saved budget, including
            overlap and effects on existing branches.
          </p>
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
            <p className="helper">Zero is valid and allows the empty plan.</p>
            <fieldset>
              <legend>AT_RISK acknowledgements</legend>
              {risks.length ? (
                risks.map((s) => (
                  <label className="check-label" key={s.site_id}>
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
                      I acknowledge the risks for {siteName(s.site_id)} in this
                      evaluation.
                      <small>
                        {s.failfast.reasons.join(" ") ||
                          "No risk explanation was supplied."}
                      </small>
                    </span>
                  </label>
                ))
              ) : (
                <p>
                  {w.current
                    ? "No AT_RISK candidates were returned."
                    : "A matching saved evaluation is needed to review risks."}
                </p>
              )}
            </fieldset>
            <button type="submit" disabled={!w.current || w.busy}>
              {w.operation === "portfolio"
                ? "Evaluating candidate sets…"
                : "Find feasible portfolio"}
            </button>
          </form>
          {p ? (
            <div className="portfolio-result">
              <h3>
                {p.solver_status === "UNAVAILABLE" ||
                p.solver_status === "UNKNOWN"
                  ? "Portfolio unavailable"
                  : p.selected_site_ids.length
                    ? "Selected stores"
                    : "Empty portfolio"}
              </h3>
              {p.selected_site_ids.length ? (
                <ul>
                  {p.selected_site_ids.map((id) => (
                    <li key={id}>{siteName(id)}</li>
                  ))}
                </ul>
              ) : (
                <p>
                  {available
                    ? "No stores were selected. An empty plan is valid when no eligible combination creates value."
                    : "Portfolio selection is currently unavailable. No investment recommendation has been made."}
                </p>
              )}
              <dl className="result-metrics">
                <div>
                  <dt>Full-network NPV (INR)</dt>
                  <dd>
                    {money(available ? p.full_network_npv_inr : undefined)}
                  </dd>
                </div>
                <div>
                  <dt>CAPEX used (INR)</dt>
                  <dd>{money(available ? p.budget_used_inr : undefined)}</dd>
                </div>
                <div>
                  <dt>Unused budget (INR)</dt>
                  <dd>{money(available ? p.budget_unused_inr : undefined)}</dd>
                </div>
              </dl>
              <p>
                <strong>
                  {
                    (
                      {
                        OPTIMAL: "Optimal combination",
                        FEASIBLE: "Feasible combination",
                        PARTIAL: "Partial search",
                        UNAVAILABLE: "Calculation unavailable",
                        UNKNOWN: "Result unknown",
                      } as const
                    )[p.solver_status ?? "UNKNOWN"]
                  }
                </strong>{" "}
                · {p.evaluated_subsets} of {p.total_subsets} subsets evaluated
              </p>
              {p.status !== "FULL_NETWORK_EXACT" && (
                <p>
                  Search completeness and optimality gap are unknown. This
                  result does not prove that no better positive portfolio
                  exists.
                </p>
              )}
              <details>
                <summary>Technical Details</summary>
                <p>
                  {p.solver_name} · {p.solver_version ?? "Version unavailable"}
                </p>
                <p>
                  Solver: {p.solver_status} · objective precision INR{" "}
                  {p.objective_precision_inr ?? "Unknown"} · gap{" "}
                  {p.optimality_gap ?? "Unknown"}
                </p>
                {p.limitations?.map((text, i) => (
                  <p key={i}>{text}</p>
                ))}
                <p>Run: {p.portfolio_run_id}</p>
                <p>Evaluation: {p.evaluation_id}</p>
              </details>
              <h3>Sites outside the selected set</h3>
              {w.project?.data.sites
                .filter((s) => !p.selected_site_ids.includes(s.site_id))
                .map((s) => {
                  const a = e?.site_analyses.find(
                    (v) => v.site_id === s.site_id,
                  );
                  return (
                    <p key={s.site_id}>
                      <strong>{s.name}</strong> ·{" "}
                      {a?.failfast.status ?? "No diagnosis"}
                      <br />
                      {p.exclusions
                        ?.find((x) => x.site_id === s.site_id)
                        ?.reasons.join(" ") ||
                        a?.failfast.reasons.join(" ") ||
                        "Not selected; a specific exclusion explanation was not supplied."}
                    </p>
                  );
                })}
            </div>
          ) : (
            <Unavailable>
              Choose a store-count cap and review any at-risk locations, then
              calculate the portfolio.
            </Unavailable>
          )}
        </section>
        <section aria-labelledby="report-heading">
          <h2 id="report-heading">Saved decision report</h2>
          <p>
            Export the frozen evaluation and matching portfolio, including
            assumptions, exclusions and evidence.
          </p>
          <button
            className="secondary"
            disabled={
              !w.current ||
              !p ||
              p.solver_status === "UNAVAILABLE" ||
              p.solver_status === "UNKNOWN" ||
              p.evaluation_id !== e?.evaluation_id ||
              w.busy
            }
            onClick={() => void w.downloadReport()}
          >
            {w.operation === "report"
              ? "Downloading report…"
              : "Download saved report"}
          </button>
          <p className="helper">
            Requires a completed saved evaluation and matching portfolio run.
            The report preserves the assumptions and evidence used for this
            decision.
          </p>
          {w.report ? (
            <>
              <h3>Downloaded content preview</h3>
              {w.report.type.includes("html") ? (
                <iframe
                  title="Saved decision report preview"
                  sandbox=""
                  srcDoc={w.report.text}
                />
              ) : (
                <pre className="report-preview">{w.report.text}</pre>
              )}
            </>
          ) : (
            <Unavailable>
              The report preview will reopen the exact downloaded content. No
              report is generated from unsaved browser inputs.
            </Unavailable>
          )}
        </section>
      </div>
    </>
  );
}
